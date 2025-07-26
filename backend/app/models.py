from sqlalchemy import Column, String, Boolean, JSON, DateTime, func
from sqlalchemy.ext.mutable import MutableDict
from .db import Base

class Chat(Base):
    __tablename__ = "chats"

    chat_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True)
    is_public = Column(Boolean, default=False)
    chat_name = Column(String, nullable=False, default="Untitled")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
