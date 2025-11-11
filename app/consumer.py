"""RabbitMQ event consumer for processing queued tasks"""

import json
import logging
import asyncio
from datetime import datetime
from services.rabbitmq_service import RabbitMQService
from services.wikipedia_service import WikipediaService
from services.chatgpt_service import ChatGPTService
from utils.logger import setup_logging


# Setup logging
logger = setup_logging()

# Initialize services
rabbitmq_service = RabbitMQService()
wikipedia_service = WikipediaService()
chatgpt_service = ChatGPTService()


def process_message(ch, method, properties, body):
    """Process incoming RabbitMQ message"""
    try:
        event = json.loads(body)
        logger.info(f"Processing event: {event.get('event_id')}")

        # Here you can add custom processing logic
        if event.get('event_type') == 'EXPLANATION_REQUESTED':
            process_explanation_request(event)

        # Acknowledge the message
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info(f"Event processed successfully: {event.get('event_id')}")

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        # Negative acknowledge to requeue
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def process_explanation_request(event: dict):
    """Process explanation request event"""
    try:
        topic = event.get('topic')
        request_id = event.get('request_id')

        logger.info(f"Processing explanation request for topic: {topic}")

        # You can add additional processing here
        # For example: logging to database, triggering webhooks, etc.

    except Exception as e:
        logger.error(f"Error processing explanation request: {e}")


def start_consumer():
    """Start the RabbitMQ consumer"""
    logger.info("Starting RabbitMQ event consumer")

    try:
        rabbitmq_service.consume_events(process_message)

    except KeyboardInterrupt:
        logger.info("Consumer interrupted by user")

    except Exception as e:
        logger.error(f"Consumer error: {e}")

    finally:
        rabbitmq_service.close()
        logger.info("Consumer stopped")


if __name__ == "__main__":
    start_consumer()
