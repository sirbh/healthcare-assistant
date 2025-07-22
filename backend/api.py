from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from uuid import uuid4


app = FastAPI()

# Add the middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specify domains like ["https://example.com"]
    allow_credentials=True,
    allow_methods=["*"],  # or list specific methods like ["GET", "POST"]
    allow_headers=["*"],  # or list specific headers like ["Authorization"]
)

# @app.get("/set-user")
# def set_user(response: Response):
#     guest_id = f"guest-{uuid4()}"
#     response.set_cookie(key="guest_id", value=guest_id, httponly=True)
#     return {"message": "Cookie set", "guest_id": guest_id}

# @app.get("/chat")
# def get_chat(guest_id: str = Cookie(default=None)):
#     if guest_id:
#         return {"message": f"Welcome back, {guest_id}!"}
#     else:
#         return {"message": "No guest ID found. Please set one first."}

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "API is running smoothly."}

@app.get("/new-chat")
def chat(request: Request):
    # Check for userId cookie
    user_id = request.cookies.get("userId")
    new_user_id = user_id is None

    # Generate userId if missing
    if new_user_id:
        user_id = str(uuid4())

    # Always generate a new chatId
    chat_id = str(uuid4())

    # Prepare response with only chatId
    response = JSONResponse(content={"chatId": chat_id})

    # Set userId cookie if it's new
    if new_user_id:
        response.set_cookie(
            key="userId",
            value=user_id,
            httponly=True,
            samesite="lax",
            secure=False  # Set to True in production (HTTPS)
        )

    return response
