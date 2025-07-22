from sqlalchemy import Column, String, Boolean, JSON
from .db import Base

class Chat(Base):
    __tablename__ = "chats"

    chat_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True)
    is_public = Column(Boolean, default=False)
    info = Column(JSON, nullable=True)  # ✅ new column to store JSON data
