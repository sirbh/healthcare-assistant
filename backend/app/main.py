from fastapi import FastAPI, Request, Depends,Body
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

from .agent import create_graph

from contextlib import asynccontextmanager
from .agent_memory.db import init_memory

from langchain.schema import HumanMessage, AIMessage

import os






# Create tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    print(os.environ.get("OPENAI_API_KEY"))
    store, checkpointer, store_ctx, checkpointer_ctx = await init_memory()
    await store.setup()
    await checkpointer.setup()
    app.state.store = store
    app.state.checkpointer = checkpointer
    app.state.graph = create_graph(store, checkpointer)

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

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "API is running smoothly."}

@app.post("/new-chat")
def create_chat(
    request: Request,
    is_public: bool = False,
    info: dict = Body(default={"name": "new chat"}),
    db: Session = Depends(get_db)
):
    user_id = request.cookies.get("userId")
    is_new_user = user_id is None

    if is_new_user:
        user_id = str(uuid4())

    chat_id = str(uuid4())

    create_chat_record(db, user_id=user_id, chat_id=chat_id, is_public=is_public, info=info)

    response = JSONResponse(content={"chatId": chat_id})
    if is_new_user:
        response.set_cookie(
            key="userId",
            value=user_id,
            httponly=True,
            samesite="lax",
            secure=False
        )

    return response



@app.get("/user-chats")
def get_user_chats(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("userId")
    if not user_id:
        return {"chats": []}

    chats = get_chats_by_user_id(db, user_id=user_id)

    return {
        "chats": [
            {
                "chat_id": chat.chat_id,
                "info": chat.info
            }
            for chat in chats
        ]
    }

@app.post("/chat")
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

    print(f"Received chat request: {chat_id}, {message}")

    config = {
        "configurable": {
            "thread_id": chat_id,
            "user_id": user_id,
        }
    }

    if not chat_id or not message:
        return JSONResponse(status_code=400, content={"error": "Invalid request"})

    
    graph = app.state.graph

    if not graph:
        return JSONResponse(status_code=500, content={"error": "Graph not initialized"})
    
    async def even_generator():
        async for event in graph.astream_events(
            {"messages": [{"role": "user", "content": message}]},
            config=config,
            version="v2"
        ):
            if event["event"] == "on_chat_model_stream" and event['metadata'].get('langgraph_node','') == "assistant":
                data = event["data"]
                # Yield text to client
                yield data["chunk"].content
        

    
    return StreamingResponse(even_generator(), media_type="text/plain")






@app.get("/chat/{chat_id}")
def get_chat_by_id(chat_id: str, request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("userId")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    chat = db.query(Chat).filter(Chat.chat_id == chat_id).first()
    if not chat or str(chat.user_id) != str(user_id):
        raise HTTPException(status_code=403, detail="Chat not found or access denied")
    

    graph = app.state.graph

    thread = {"configurable": {"thread_id": chat.chat_id}}

    state = graph.get_state(thread)

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
        "messages": typed_messages,  # Assuming metadata is stored as JSON
    }





 