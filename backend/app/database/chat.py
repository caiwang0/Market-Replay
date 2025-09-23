import uuid
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.models.database.chat import Chat as ChatDBModel
from app.models.database.chat import ChatMessage as MessageDBModel

class ChatDB:
    def __init__(self, db: Session):
        self.db = db
    
    # Chat Operations
    def get_latest_chat(self) -> ChatDBModel:
        """Get the most recently updated chat (no user restriction)"""
        return (
            self.db.query(ChatDBModel)
            .order_by(ChatDBModel.updated_at.desc())
            .first()
        )

    def get_chat_by_uuid(self, chat_uuid: str) -> Optional[ChatDBModel]:
        """Get a chat by chat_uuid (no user restriction)"""
        return (
            self.db.query(ChatDBModel)
            .filter(ChatDBModel.chat_uuid == chat_uuid)
            .first()
        )

    def get_chat_messages(self, chat_id: int, offset: int = 0, limit: int = 100) -> List[MessageDBModel]:
        """Get messages for a chat"""
        return self.db.query(MessageDBModel).filter(
            MessageDBModel.chat_id == chat_id
        ).order_by(MessageDBModel.created_at.desc()).offset(offset).limit(limit).all()
    
    def create_chat(self, title: str = None) -> ChatDBModel:
        """Create a new chat session (no user restriction)"""
        chat = ChatDBModel(title=title, chat_uuid=str(uuid.uuid4()))
        self.db.add(chat)
        self.db.commit()
        self.db.refresh(chat)
        return chat
    
    def get_chat_by_id(self, chat_id: int) -> Optional[ChatDBModel]:
        """Get chat by ID with messages"""
        return self.db.query(ChatDBModel).filter(ChatDBModel.id == chat_id).first()


    def get_all_chats(self, skip: int = 0, limit: int = 50) -> List[ChatDBModel]:
        """Get all chats (no user restriction)"""
        return self.db.query(ChatDBModel).order_by(
            ChatDBModel.updated_at.desc()
        ).offset(skip).limit(limit).all()
    
    def update_chat_title(self, chat_id: int, title: str) -> Optional[ChatDBModel]:
        """Update chat title"""
        chat = self.get_chat_by_id(chat_id)
        if chat:
            chat.title = title
            self.db.commit()
            self.db.refresh(chat)
        return chat
    
    def delete_chat(self, chat_id: int) -> bool:
        """Delete chat and all its messages"""
        chat = self.get_chat_by_id(chat_id)
        if chat:
            self.db.delete(chat)
            self.db.commit()
            return True
        return False
    
    # Message Operations
    def add_message(self, chat_id: int, query: str, result: str, steps: Dict[str, Any] = None) -> MessageDBModel:
        """Add a message to a chat"""
        chat = self.get_chat_by_id(chat_id)
        if not chat:
            raise ValueError(f"Chat with id {chat_id} not found")
        
        message = MessageDBModel(
            chat_id=chat_id,
            query=query,
            result=result,
            steps=steps
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message
    
    
    def get_message_by_id(self, message_id: int) -> Optional[MessageDBModel]:
        """Get specific message"""
        return self.db.query(MessageDBModel).filter(MessageDBModel.id == message_id).first()
    
    def update_message(self, message_id: int, query: str = None, result: str = None, steps: Dict[str, Any] = None) -> Optional[MessageDBModel]:
        """Update a message"""
        message = self.get_message_by_id(message_id)
        if message:
            if query is not None:
                message.query = query
            if result is not None:
                message.result = result
            if steps is not None:
                message.steps = steps
            self.db.commit()
            self.db.refresh(message)
        return message
    
    def delete_message(self, message_id: int) -> bool:
        """Delete a specific message"""
        message = self.get_message_by_id(message_id)
        if message:
            self.db.delete(message)
            self.db.commit()
            return True
        return False
    