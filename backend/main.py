from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, List
import asyncio
from datetime import datetime
import json
from pathlib import Path
from model import get_chatbot
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Chatbot API",
    description="ChatGPT-style chatbot powered by DialoGPT, optimized for Apple Silicon M4",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: ["http://localhost:3000", "https://yourdomain.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    temperature: Optional[float] = Field(default=0.7, ge=0.1, le=1.0)
    max_length: Optional[int] = Field(default=1000, ge=100, le=2000)
    top_k: Optional[int] = Field(default=50, ge=10, le=100)
    top_p: Optional[float] = Field(default=0.95, ge=0.1, le=1.0)

class ChatResponse(BaseModel):
    response: str
    timestamp: str
    model: str = "DialoGPT-medium"

class HealthResponse(BaseModel):
    status: str
    message: str
    version: str
    device: str
    model_loaded: bool

# Store active WebSocket connections
active_connections: List[WebSocket] = []

# Health check endpoint
@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    import torch
    device = "Apple Silicon (MPS)" if torch.backends.mps.is_available() else "CPU"
    
    return HealthResponse(
        status="online",
        message="AI Chatbot API is running",
        version="1.0.0",
        device=device,
        model_loaded=True
    )

# REST API endpoint for chat
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Handle chat requests via REST API
    
    Request body:
    - message: User's message (required)
    - temperature: Sampling temperature (0.1-1.0, default: 0.7)
    - max_length: Maximum response length (100-2000, default: 1000)
    - top_k: Top-k sampling (10-100, default: 50)
    - top_p: Nucleus sampling (0.1-1.0, default: 0.95)
    """
    try:
        logger.info(f"Received message: {request.message[:50]}...")
        
        # Get chatbot instance
        bot = get_chatbot()
        
        # Generate response
        response = bot.generate_response(
            request.message,
            max_length=request.max_length,
            temperature=request.temperature,
            top_k=request.top_k,
            top_p=request.top_p
        )
        
        logger.info(f"Generated response: {response[:50]}...")
        
        return ChatResponse(
            response=response,
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time chat
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    Handle real-time chat via WebSocket
    Provides typing indicators and streaming responses
    """
    await websocket.accept()
    active_connections.append(websocket)
    bot = get_chatbot()
    
    logger.info("New WebSocket connection established")
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            user_message = data.get("message", "").strip()
            
            if not user_message:
                await websocket.send_json({
                    "type": "error",
                    "error": "Message cannot be empty"
                })
                continue
            
            logger.info(f"WebSocket received: {user_message[:50]}...")
            
            # Send typing indicator
            await websocket.send_json({
                "type": "typing",
                "isTyping": True
            })
            
            # Simulate thinking time (optional)
            await asyncio.sleep(0.3)
            
            # Generate response
            response = bot.generate_response(
                user_message,
                temperature=data.get("temperature", 0.7),
                max_length=data.get("max_length", 1000)
            )
            
            # Send response
            await websocket.send_json({
                "type": "message",
                "response": response,
                "timestamp": datetime.now().isoformat(),
                "isTyping": False
            })
            
            logger.info(f"WebSocket sent: {response[:50]}...")
    
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        active_connections.remove(websocket)
        await websocket.close()

# Reset conversation history
@app.post("/api/reset")
async def reset_conversation():
    """Reset chatbot conversation history"""
    try:
        bot = get_chatbot()
        bot.reset_history()
        logger.info("Conversation history reset")
        return {
            "status": "success",
            "message": "Conversation history has been reset"
        }
    except Exception as e:
        logger.error(f"Error resetting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Get model info
@app.get("/api/info")
async def model_info():
    """Get information about the loaded model"""
    import torch
    
    bot = get_chatbot()
    
    return {
        "model_name": "DialoGPT-medium",
        "parameters": "345M",
        "device": "Apple Silicon (MPS)" if torch.backends.mps.is_available() else "CPU",
        "framework": "PyTorch",
        "max_context_length": 800,
        "supported_languages": ["English"]
    }

# Startup event - preload model
@app.on_event("startup")
async def startup_event():
    """Load model when server starts"""
    logger.info("=" * 60)
    logger.info("Starting AI Chatbot API Server")
    logger.info("=" * 60)
    logger.info("Loading AI model (this may take 1-2 minutes)...")
    
    try:
        bot = get_chatbot()
        logger.info("✅ Model loaded successfully!")
        logger.info("=" * 60)
        logger.info("Server is ready to accept requests")
        logger.info("API Docs: http://localhost:8000/docs")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"❌ Failed to load model: {e}")
        raise

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on server shutdown"""
    logger.info("Shutting down server...")
    # Close all WebSocket connections
    for connection in active_connections:
        await connection.close()
    logger.info("Server shutdown complete")

if __name__ == "__main__":
    import uvicorn
    
    # Run server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )
from database import db
import uuid

# Add session management
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, session_id: str = None):
    try:
        if not session_id:
            session_id = str(uuid.uuid4())
        
        bot = get_chatbot()
        response = bot.generate_response(request.message)
        
        # Save to database
        db.save_conversation(
            session_id=session_id,
            user_message=request.message,
            bot_response=response,
            temperature=request.temperature
        )
        
        return ChatResponse(
            response=response,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get conversation history
@app.get("/api/history/{session_id}")
async def get_history(session_id: str, limit: int = 50):
    try:
        history = db.get_conversation_history(session_id, limit)
        return {
            "session_id": session_id,
            "messages": [
                {
                    "user_message": msg.user_message,
                    "bot_response": msg.bot_response,
                    "timestamp": msg.timestamp.isoformat()
                }
                for msg in history
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


    
