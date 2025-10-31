from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

Base = declarative_base()

class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), index=True)
    user_message = Column(Text)
    bot_response = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    temperature = Column(String(10))
    model = Column(String(50), default="DialoGPT-medium")

class Database:
    def __init__(self, db_url="sqlite:///./chatbot.db"):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def save_conversation(self, session_id, user_message, bot_response, temperature="0.7"):
        session = self.SessionLocal()
        try:
            message = ChatMessage(
                session_id=session_id,
                user_message=user_message,
                bot_response=bot_response,
                temperature=str(temperature)
            )
            session.add(message)
            session.commit()
        finally:
            session.close()
    
    def get_conversation_history(self, session_id, limit=50):
        session = self.SessionLocal()
        try:
            messages = session.query(ChatMessage)\
                .filter(ChatMessage.session_id == session_id)\
                .order_by(ChatMessage.timestamp.desc())\
                .limit(limit)\
                .all()
            return list(reversed(messages))
        finally:
            session.close()

# Global database instance
db = Database()

