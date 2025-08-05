from fastapi import FastAPI, Request, Depends,Body, Path, Form
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, PlainTextResponse
from uuid import uuid4
from fastapi import Request, Depends, HTTPException
from .models import Chat
from .deps import get_db
from .crud import create_chat_record, get_chats_by_user_id
from sqlalchemy.orm import Session
from .db import Base, engine
from pydantic import BaseModel, Field
from app.agents.supervisor_agent import UserProfile
import asyncio


from .graph.health_care_assistant_graph import create_graph
from .graph.chat_naming_graph import create_graph as create_summarizer_graph
from .graph.test_graph import create_graph as create_test_graph

from contextlib import asynccontextmanager
from .agent_memory.db import init_memory

from langchain.schema import HumanMessage, AIMessage

import os,json,gzip







class ChatForm(BaseModel):
    name: str
    age: str
    gender: str
    conditions: str | None = None

# Create tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    store, checkpointer, store_ctx, checkpointer_ctx = await init_memory()
    await store.setup()
    await checkpointer.setup()
    app.state.store = store
    app.state.checkpointer = checkpointer
    app.state.graph = create_graph(store, checkpointer)
    # app.state.graph = create_test_graph(checkpointer)
    app.state.summarizer_graph = create_summarizer_graph()

    yield

    await store_ctx.__aexit__(None, None, None)
    await checkpointer_ctx.__aexit__(None, None, None)


app = FastAPI(lifespan=lifespan)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://healthcare-assistant-woad.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    data = {"status": "ok", "message": "API is running smoothly!"}
    compressed = gzip.compress(json.dumps(data).encode('utf-8'))
    return Response(
        content=compressed,
        media_type="application/json",
        headers={"Content-Encoding": "gzip"}
    )



@app.post("/api/new-chat")
def create_chat(
    request: Request,
    form: ChatForm,
    is_public: bool = False,
    db: Session = Depends(get_db)
):
    user_id = request.cookies.get("userId")
    is_new_user = user_id is None

    if is_new_user:
        user_id = str(uuid4())

    namespace = ("user_profile", user_id)
    key = "user_details"
    value = UserProfile(
        user_name=form.name,
        age=int(form.age),
        gender=form.gender,
        conditions=form.conditions.split(",") if form.conditions else []
    )
    app.state.store.put(namespace, key, value.model_dump())

    for m in app.state.store.search(namespace):
        print(m.dict())

    chat_id = str(uuid4())

    chat = create_chat_record(
        db,
        user_id=user_id,
        chat_id=chat_id,
        is_public=is_public,
        chat_name="new chat"
    )

    # Prepare content
    response_dict = {
        "chatId": chat.chat_id,
        "info": {
            "name": chat.chat_name,
            "created_at": chat.created_at.isoformat(),
            "updated_at": chat.updated_at.isoformat(),
        }
    }
    json_data = json.dumps(response_dict).encode("utf-8")
    compressed_data = gzip.compress(json_data)

    # Create compressed response
    response = Response(
        content=compressed_data,
        media_type="application/json",
        headers={"Content-Encoding": "gzip"}
    )

    # Set cookie if it's a new user
    if is_new_user:
      response.set_cookie(
         key="userId",
         value=user_id,
         httponly=True,
         samesite="none",  # ✅ REQUIRED for cross-origin
         secure=True       # ✅ REQUIRED when samesite="none"
    )

    return response




@app.get("/api/user-chats")
def get_user_chats(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("userId")
    if not user_id:
        # Return gzipped empty response
        empty_data = json.dumps({"chats": []}).encode("utf-8")
        compressed = gzip.compress(empty_data)
        return Response(
            content=compressed,
            media_type="application/json",
            headers={"Content-Encoding": "gzip"}
        )

    chats = get_chats_by_user_id(db, user_id=user_id)

    response_data = {
        "chats": [
            {
                "chat_id": chat.chat_id,
                "info": {
                    "name": chat.chat_name,
                    "created_at": chat.created_at.isoformat(),
                    "updated_at": chat.updated_at.isoformat(),
                }
            }
            for chat in chats
        ]
    }

    json_data = json.dumps(response_data).encode("utf-8")
    compressed_data = gzip.compress(json_data)

    return Response(
        content=compressed_data,
        media_type="application/json",
        headers={"Content-Encoding": "gzip"}
    )


@app.post("/api/chat")
async def chat_endpoint(
    request: Request,
    body: dict = Body(...),
    db: Session = Depends(get_db)
):
    user_id = body.get("user_id")  # <-- get user_id from body now
    if not user_id:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    # user_id = request.cookies.get("userId")
    # if not user_id:
    #     return JSONResponse(status_code=401, content={"error": "Unauthorized"})

    chat_id = body.get("chat_id")
    message = body.get("message", "")




    if not chat_id or not message:
        return JSONResponse(status_code=400, content={"error": "Invalid request"})

    chat = db.query(Chat).filter(Chat.chat_id == chat_id).first()
    if not chat:
        return JSONResponse(status_code=404, content={"error": "Chat not found"})
    if chat.user_id != user_id:
        return JSONResponse(status_code=403, content={"error": "Chat does not belong to user"})

    config = {
        "configurable": {
            "thread_id": chat_id,
            "user_id": user_id,
        }
    }


    graph = app.state.graph
    if not graph:
        return JSONResponse(status_code=500, content={"error": "Graph not initialized"})

    async def event_generator():
        async for event in graph.astream_events(
            # Command(resume="go to step 3!"),
            
            {"messages": [HumanMessage(content=message)],"summary":""},
            config=config,
            version="v2",
        ):
            if event["metadata"].get('langgraph_node', '') == "tools" and event["event"]=="on_tool_start" and event["name"] == "retrieve": 

                print(event["name"])
                yield json.dumps({
                    "type": "tool",
                    "content": "retrieving documents...",
                }) + "\n"
                await asyncio.sleep(0.01)
            elif event["event"] == "on_tool_start" and event["name"] == "check_documents":
                print(event["name"])
                yield json.dumps({
                    "type": "tool",
                    "content": "checking documents...",
                }) + "\n"
                await asyncio.sleep(0.01)
            
            elif event["event"] == "on_tool_start" and event["name"] == "diagnose_condition":
                print(event["name"])
                yield json.dumps({
                    "type": "tool",
                    "content": "consulting diagnostic agent...",
                }) + "\n"
                await asyncio.sleep(0.01)
            
            elif event["event"] == "on_tool_start" and event["name"] == "explain_diagnosis":
                print(event["name"])
                yield json.dumps({
                    "type": "tool",
                    "content": "consulting explanation agent...",
                }) + "\n"
                await asyncio.sleep(0.01)
            
            elif event["event"] == "on_tool_start" and event["name"] == "recommend_treatment":
                print(event["name"])
                yield json.dumps({
                    "type": "tool",
                    "content": "consulting recommendation agent...",
                }) + "\n"
                await asyncio.sleep(0.01)
               
            
            elif event["event"] == "on_chat_model_stream" and event['metadata'].get('langgraph_node', '') == "supervisor":
                data = event["data"]
                print(data["chunk"].content)
                yield json.dumps({
                    "type": "ai",
                    "content": data["chunk"].content
                }) + "\n"
                
                await asyncio.sleep(0.01)

            
        state = await graph.aget_state(config)
        messages = state.values.get('messages', [])

        if len(messages) <= 8:
            typed_messages = []
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    typed_messages.append({'role': 'user', 'content': msg.content})
                elif isinstance(msg, AIMessage):
                    if msg.response_metadata.get('finish_reason') == 'stop':
                        typed_messages.append({'role': 'ai', 'content': msg.content})

            summary_prompt = f"""
               summarize the chat in max 2 words
               only return the summary, do not return any other text
               Here is the chat: {typed_messages}
            """
            summary_chunks = []

            async for event in app.state.summarizer_graph.astream_events(
                {"messages": [{"role": "user", "content": summary_prompt}]},
                config={},
                version="v2"
            ):
                
                if event["event"] == "on_chat_model_stream" and event['metadata'].get('langgraph_node', '') == "assistant":
                    data = event["data"]
                    yield json.dumps({
                        "type": "summary",
                        "content": data["chunk"].content
                    }) + "\n"
                    await asyncio.sleep(0.01)
                    summary_chunks.append(data["chunk"].content)

            chat_name = "".join(summary_chunks).strip()
            print(f"Chat name generated: {chat_name}")

            if chat_name:
                chat.chat_name = chat_name
                try:
                   updated_chat = db.query(Chat).filter(Chat.chat_id == chat_id).first()
                   updated_chat.chat_name = chat_name
                   db.commit()
                except Exception as e:
                   print(f"Error updating chat name: {e}")

    return StreamingResponse(event_generator(), media_type="text/event-stream")








@app.get("/api/chat/{chat_id}")
def get_chat_by_id(chat_id: str, request: Request, db: Session = Depends(get_db)):
    chat = db.query(Chat).filter(Chat.chat_id == chat_id).first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Check if chat is public
    if not chat.is_public:
        user_id = request.cookies.get("userId")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        if str(chat.user_id) != str(user_id):
            raise HTTPException(status_code=403, detail="Access denied")
    
    graph = app.state.graph
    thread = {"configurable": {"thread_id": chat.chat_id}}
    state = graph.get_state(thread)

    if "messages" not in state.values:
        response_data = {
            "id": chat.chat_id,
            "messages": [],
            "visibility": "public" if chat.is_public else "private"
        }
    else:
        messages = state.values['messages']
        typed_messages = []

        for msg in messages:
            if isinstance(msg, HumanMessage):
                typed_messages.append({
                    'role': 'user',
                    'content': msg.content
                })
            elif isinstance(msg, AIMessage):
                finish_reason = msg.response_metadata.get('finish_reason')
                if finish_reason == 'stop':
                    typed_messages.append({
                        'role': 'ai',
                        'content': msg.content
                    })

        response_data = {
            "id": chat.chat_id,
            "messages": typed_messages,
            "visibility": "public" if chat.is_public else "private"
        }

    # Compress the response
    json_data = json.dumps(response_data).encode("utf-8")
    compressed_data = gzip.compress(json_data)

    return Response(
        content=compressed_data,
        media_type="application/json",
        headers={"Content-Encoding": "gzip"}
    )

@app.patch("/api/chat/{chat_id}/visibility")
def update_chat_visibility(
    chat_id: str = Path(...),
    is_public: bool = Body(..., embed=True),
    request: Request = None,
    db: Session = Depends(get_db)
):
    user_id = request.cookies.get("userId")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    chat = db.query(Chat).filter(Chat.chat_id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    if str(chat.user_id) != str(user_id):
        raise HTTPException(status_code=403, detail="Access denied")

    chat.is_public = is_public
    db.commit()

    response_data = {"chat_id": chat_id, "is_public": chat.is_public}
    compressed = gzip.compress(json.dumps(response_data).encode("utf-8"))

    return Response(
        content=compressed,
        media_type="application/json",
        headers={"Content-Encoding": "gzip"}
    )



@app.get("/api/user-profile")
def get_user_profile(request: Request):
    user_id = request.cookies.get("userId")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    namespace_for_memory = ("user_profile", user_id)
    user_profile = app.state.store.get(namespace_for_memory, "user_details")
    if not user_profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    # Compress the response
    json_data = json.dumps(user_profile.value).encode("utf-8")
    compressed = gzip.compress(json_data)

    return Response(
        content=compressed,
        media_type="application/json",
        headers={"Content-Encoding": "gzip"}
    )

@app.get("/api/user-id")
def get_user_id(request: Request):
    user_id = request.cookies.get("userId")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    return {"user_id": user_id}