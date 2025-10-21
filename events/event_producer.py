import logging
from typing import Dict, Any
from datetime import datetime
from uuid import uuid4
from services.rabbitmq_service import RabbitMQService


logger = logging.getLogger(__name__)


class EventProducer:
    """Producer for publishing events to RabbitMQ"""

    def __init__(self):
        self.rabbitmq_service = RabbitMQService()

    def publish_explanation_requested(self, request_id: str, topic: str, session_id: str = None):
        """Publish event when explanation is requested"""
        event = {
            "event_id": str(uuid4()),
            "request_id": request_id,
            "event_type": "EXPLANATION_REQUESTED",
            "topic": topic,
            "status": "pending",
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id
        }
        self.rabbitmq_service.publish_event(event)
        logger.info(f"Published EXPLANATION_REQUESTED event for topic: {topic}")

    def publish_explanation_completed(self, request_id: str, topic: str, explanation: str, sources: list):
        """Publish event when explanation is completed"""
        event = {
            "event_id": str(uuid4()),
            "request_id": request_id,
            "event_type": "EXPLANATION_COMPLETED",
            "topic": topic,
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "explanation": explanation,
                "sources": [{"title": s.title, "url": s.url} for s in sources]
            }
        }
        self.rabbitmq_service.publish_event(event)
        logger.info(f"Published EXPLANATION_COMPLETED event for topic: {topic}")

    def publish_explanation_failed(self, request_id: str, topic: str, error: str):
        """Publish event when explanation fails"""
        event = {
            "event_id": str(uuid4()),
            "request_id": request_id,
            "event_type": "EXPLANATION_FAILED",
            "topic": topic,
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "error": error
            }
        }
        self.rabbitmq_service.publish_event(event)
        logger.error(f"Published EXPLANATION_FAILED event for topic: {topic} - Error: {error}")
