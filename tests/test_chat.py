import pytest
from fastapi.testclient import TestClient
from src.conversational.chat_engine import app, IntentClassifier

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_intent_classifier():
    classifier = IntentClassifier()
    
    intent, confidence = await classifier.classify("I need help with my order")
    assert intent == "support"
    assert confidence > 0.9
    
    intent, confidence = await classifier.classify("What is my order status?")
    assert intent == "query"
    
    intent, confidence = await classifier.classify("Hello there!")
    assert intent == "general_chat"

def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "chat_requests_total" in response.text
