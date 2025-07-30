from fastapi import FastAPI, Request, Depends,Body, Path, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, PlainTextResponse
from uuid import uuid4
from fastapi import APIRouter, Request, Depends, HTTPException
from .models import Chat
from .deps import get_db
from .crud import create_chat_record, get_chats_by_user_id
from sqlalchemy.orm import Session
from .db import Base, engine
from datetime import datetime, timezone
from langgraph.types import Command
from pydantic import BaseModel, Field
from typing import List
from app.agent import UserProfile


from .agent import create_graph
from .agents.summarizer import create_graph as create_summarizer_graph

from contextlib import asynccontextmanager
from .agent_memory.db import init_memory

from langchain.schema import HumanMessage, AIMessage

import os,json







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
    app.state.summarizer_graph = create_summarizer_graph()

    yield

    await store_ctx.__aexit__(None, None, None)
    await checkpointer_ctx.__aexit__(None, None, None)


app = FastAPI(lifespan=lifespan)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "API is running smoothly."}



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




    # 🟢 Update: pass chat_name instead of info
    chat = create_chat_record(
        db,
        user_id=user_id,
        chat_id=chat_id,
        is_public=is_public,
        chat_name="new chat"
    )

    response = JSONResponse(content={
        "chatId": chat.chat_id,
        "info": {
            "name": chat.chat_name,
            "created_at": chat.created_at.isoformat(),
            "updated_at": chat.updated_at.isoformat(),
        }
    })
    if is_new_user:
        response.set_cookie(
            key="userId",
            value=user_id,
            httponly=True,
            samesite="lax",
            secure=False
        )

    return response




@app.get("/api/user-chats")
def get_user_chats(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("userId")
    if not user_id:
        return {"chats": []}

    chats = get_chats_by_user_id(db, user_id=user_id)

    return {
        "chats": [
            {
                "chat_id": chat.chat_id,
                "info": {
                    "name": chat.chat_name,
                    "created_at": chat.created_at,
                    "updated_at": chat.updated_at,
                }
            }
            for chat in chats
        ]
    }


@app.post("/api/chat")
async def chat_endpoint(
    request: Request,
    body: dict = Body(...),
    db: Session = Depends(get_db)
):
    user_id = request.cookies.get("userId")
    if not user_id:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})

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
            if event["event"] == "on_chat_model_stream" and event['metadata'].get('langgraph_node', '') == "assistant":
                data = event["data"]
                yield json.dumps({
                    "type": "ai",
                    "content": data["chunk"].content
                }) + "\n"
            # chunk = event.get('data', {}).get('chunk', {})

            # if '__interrupt__' in chunk:
            #     print("I Was interrupted!")
            #     print(f"Interrupt received: {chunk['__interrupt__'][0].value}")
            #     yield json.dumps(chunk['__interrupt__'][0].value) + "\n"
            #     break
            
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

    chat.updated_at = datetime.now(timezone.utc)
    return StreamingResponse(event_generator(), media_type="text/event-stream")

            








@app.get("/api/chat/{chat_id}")
def get_chat_by_id(chat_id: str, request: Request, db: Session = Depends(get_db)):
    chat = db.query(Chat).filter(Chat.chat_id == chat_id).first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Check if chat is public
    if not chat.is_public:
        # If private, validate user authentication
        user_id = request.cookies.get("userId")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        if str(chat.user_id) != str(user_id):
            raise HTTPException(status_code=403, detail="Access denied")
    

    graph = app.state.graph

    thread = {"configurable": {"thread_id": chat.chat_id}}

    state = graph.get_state(thread)

    if "messages" not in state.values:
        # If messages key is missing, return empty chat
        return {
            "id": chat.chat_id,
            "messages": [],
            "visibility": "public" if chat.is_public else "private"
        }

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
    



    return {
        "id": chat.chat_id,
        "messages": typed_messages,
        "visibility": "public" if chat.is_public else "private"
    }

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

    return {"chat_id": chat_id, "is_public": chat.is_public}



@app.get("/api/user-profile")
def get_user_profile(request: Request):
    user_id = request.cookies.get("userId")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    namespace_for_memory = ("user_profile", user_id)
    user_profile = app.state.store.get(namespace_for_memory, "user_details")
    if not user_profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    return user_profile.value