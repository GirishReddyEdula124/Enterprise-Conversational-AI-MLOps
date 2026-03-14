from prometheus_client import Counter, Histogram, Summary
import time
from functools import wraps

# Metrics for Conversational AI engine
CHAT_REQUEST_COUNT = Counter(
    "chat_requests_total",
    "Total number of chat requests received",
    ["status", "intent"]
)

CHAT_RESPONSE_LATENCY = Histogram(
    "chat_response_latency_seconds",
    "Latency of chat responses in seconds",
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, float("inf"))
)

SESSION_MEMORY_OPERATIONS = Counter(
    "session_memory_operations_total",
    "Total number of session memory operations (read/write)",
    ["operation", "status"]
)

ACTIVE_WEBSOCKET_CONNECTIONS = Summary(
    "active_websocket_connections",
    "Number of active WebSocket connections"
)

def track_latency(f):
    @wraps(f)
    async def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            result = await f(*args, **kwargs)
            CHAT_RESPONSE_LATENCY.observe(time.perf_counter() - start_time)
            return result
        except Exception as e:
            CHAT_RESPONSE_LATENCY.observe(time.perf_counter() - start_time)
            raise e
    return wrapper
