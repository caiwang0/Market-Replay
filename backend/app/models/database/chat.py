from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy import Column, Integer, String, JSON
from app.database.base import Base

class Chat(Base):
    __tablename__ = "chats"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    chat_uuid = Column(String(36), nullable=False, unique=True)
    title = Column(String(500))  # MySQL: specify length
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="chats")
    messages = relationship("ChatMessage", back_populates="chat", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "chat_uuid": self.chat_uuid,
            "user_id": self.user_id,
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False, index=True)
    query = Column(Text, nullable=False)  # MySQL: Text type for long content
    result = Column(Text, nullable=False)  # MySQL: Text type for long content
    steps = Column(JSON)  # MySQL 5.7+ supports JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    chat = relationship("Chat", back_populates="messages")
    
    def to_dict(self):
        return {
            "id": self.id,
            "chat_id": self.chat_id,
            "query": self.query,
            "result": self.result,
            "steps": self.steps,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    