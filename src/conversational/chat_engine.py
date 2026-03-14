import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

import redis.asyncio as redis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from prometheus_client import make_asgi_app

from src.mlops.monitoring import (
    CHAT_REQUEST_COUNT,
    SESSION_MEMORY_OPERATIONS,
    ACTIVE_WEBSOCKET_CONNECTIONS,
    track_latency
)

# Configuration using Pydantic Settings
class Settings(BaseSettings):
    PROJECT_NAME: str = "Enterprise-Conversational-AI"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    SESSION_TTL: int = 3600  # 1 hour
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

# Logging setup
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Models
class ChatMessage(BaseModel):
    session_id: str
    user_id: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatResponse(BaseModel):
    session_id: str
    response: str
    intent: str
    confidence: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SessionState(BaseModel):
    history: List[Dict[str, str]] = []
    metadata: Dict[str, str] = {}

# Redis Memory Manager
class RedisMemoryManager:
    def __init__(self, host: str, port: int):
        self.client = redis.Redis(host=host, port=port, decode_responses=True)

    async def get_session(self, session_id: str) -> SessionState:
        try:
            data = await self.client.get(f"session:{session_id}")
            SESSION_MEMORY_OPERATIONS.labels(operation="read", status="success").inc()
            if data:
                return SessionState(**json.loads(data))
            return SessionState()
        except Exception as e:
            logger.error(f"Redis read error: {e}")
            SESSION_MEMORY_OPERATIONS.labels(operation="read", status="error").inc()
            return SessionState()

    async def save_session(self, session_id: str, state: SessionState):
        try:
            await self.client.setex(
                f"session:{session_id}",
                settings.SESSION_TTL,
                state.model_dump_json()
            )
            SESSION_MEMORY_OPERATIONS.labels(operation="write", status="success").inc()
        except Exception as e:
            logger.error(f"Redis write error: {e}")
            SESSION_MEMORY_OPERATIONS.labels(operation="write", status="error").inc()

# Intent Classifier (Mock implementation for enterprise logic)
class IntentClassifier:
    async def classify(self, text: str) -> tuple[str, float]:
        text = text.lower()
        if "help" in text:
            return "support", 0.95
        if "status" in text:
            return "query", 0.88
        return "general_chat", 0.75

# Core Application
app = FastAPI(title=settings.PROJECT_NAME)
memory_manager = RedisMemoryManager(settings.REDIS_HOST, settings.REDIS_PORT)
intent_classifier = IntentClassifier()

# Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        ACTIVE_WEBSOCKET_CONNECTIONS.observe(len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        ACTIVE_WEBSOCKET_CONNECTIONS.observe(len(self.active_connections))

manager = ConnectionManager()

@app.websocket("/ws/chat/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            chat_msg = ChatMessage(session_id=session_id, **message_data)
            
            response = await process_chat_message(chat_msg)
            await websocket.send_text(response.model_dump_json())
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@track_latency
async def process_chat_message(msg: ChatMessage) -> ChatResponse:
    # 1. Intent Classification
    intent, confidence = await intent_classifier.classify(msg.message)
    
    # 2. Retrieve Memory
    state = await memory_manager.get_session(msg.session_id)
    
    # 3. Business Logic / Response Generation
    response_text = f"Analyzed intent: {intent}. Echo: {msg.message}"
    
    # 4. Update Memory
    state.history.append({"role": "user", "content": msg.message})
    state.history.append({"role": "assistant", "content": response_text})
    await memory_manager.save_session(msg.session_id, state)
    
    # 5. Track Metrics
    CHAT_REQUEST_COUNT.labels(status="success", intent=intent).inc()
    
    return ChatResponse(
        session_id=msg.session_id,
        response=response_text,
        intent=intent,
        confidence=confidence
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
