from sqlalchemy.orm import Session
from .models import Chat

def create_chat_record(db, user_id: str, chat_id: str, is_public: bool, info: dict = None):
    chat = Chat(
        user_id=user_id,
        chat_id=chat_id,
        is_public=is_public,
        info=info or {"name": "new chat"}
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat



def get_chats_by_user_id(db: Session, user_id: str):
    return db.query(Chat).filter(Chat.user_id == user_id).all()