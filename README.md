# Enterprise Conversational AI & MLOps Framework

An enterprise-grade, production-ready repository for Conversational AI systems, built with scalability, state management, and MLOps observability at its core.

## 🏛 Architecture Overview

The system is designed with a modular architecture that separates concerns between conversational logic, session management, and operational monitoring.

### Core Components
- **FastAPI / WebSockets**: High-performance, asynchronous API and real-time communication layer.
- **Redis State Management**: High-speed, persistent session memory and context tracking.
- **Intent Classification Layer**: Modular intent detection (replaceable with LLM/NLP models).
- **MLOps Monitoring (Prometheus/Grafana)**: Real-time tracking of latency, throughput, and conversational metrics.
- **Multi-stage Docker Builds**: Optimized production images for deployment.

## 🔄 Conversational AI Lifecycle

1.  **Ingestion**: Real-time message reception via WebSockets.
2.  **Preprocessing**: Intent classification and entity extraction.
3.  **Memory Retrieval**: Context restoration from Redis using `session_id`.
4.  **Logic Execution**: Business rules and response generation.
5.  **State Persistence**: Session state updates back to Redis.
6.  **Observability**: Metric emission for latency and success rates.

## 🚀 Setup Instructions

### 1. Local Development
Ensure you have Python 3.11+ and Redis installed.

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn src.conversational.chat_engine:app --reload
```

### 2. Docker Execution
The easiest way to stand up the entire stack is using Docker Compose.

```bash
cd infrastructure
docker-compose up --build
```

### 3. Verification
- **Health Check**: `GET http://localhost:8000/health`
- **Metrics**: `GET http://localhost:8000/metrics`
- **Prometheus Dashboard**: `http://localhost:9090`
- **WebSocket Chat**: `ws://localhost:8000/ws/chat/{session_id}`

## 🧪 Testing

Run the test suite using `pytest`:

```bash
pytest tests/
```

## 📊 MLOps Integration

- **Latency Tracking**: `@track_latency` decorator monitors response times.
- **Intent Distribution**: `chat_requests_total` counter tracks conversation variety.
- **Session Health**: Monitoring Redis operation success/failure rates.

---
**Maintained by:** Senior Applied Scientist / GCP Certified ML Engineer
