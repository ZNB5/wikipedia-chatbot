
import json
import logging
import asyncio
import pika
from services.rabbitmq_service import RabbitMQService
from services.wikipedia_service import WikipediaService
from services.chatgpt_service import ChatGPTService
from utils.logger import setup_logging

logger = setup_logging()
rabbitmq_service = RabbitMQService()
wikipedia_service = WikipediaService()
chatgpt_service = ChatGPTService()


def process_message(ch, method, properties, body):
    """
    Process message with retry logic and DLQ support.

    - Max 3 retries before sending to DLQ
    - Tracks retry count in message headers
    - NACK with requeue for transient errors
    - NACK without requeue (→ DLQ) for max retries
    """
    try:
        message = json.loads(body)
        correlation_id = properties.correlation_id or "unknown"
        user_id = message.get('user_id', 'anonymous')

        # Track retry count
        headers = properties.headers or {}
        retry_count = headers.get('x-retry-count', 0)

        logger.info(f"Message received - User: {user_id}, Correlation: {correlation_id}, Retry: {retry_count}")

        if 'message' in message:
            asyncio.run(process_question(message, correlation_id, user_id))

        # Success - ACK message
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        logger.error(f"Error processing message: {e}")

        # Get current retry count
        headers = properties.headers or {}
        retry_count = headers.get('x-retry-count', 0)
        max_retries = 3

        if retry_count >= max_retries:
            # Max retries reached - send to DLQ (NACK without requeue)
            logger.error(f"Max retries ({max_retries}) reached for correlation_id: {properties.correlation_id}. Sending to DLQ.")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        else:
            # Increment retry count and requeue
            new_retry_count = retry_count + 1
            logger.warning(f"Retry {new_retry_count}/{max_retries} for correlation_id: {properties.correlation_id}")

            # Update headers with new retry count
            new_headers = headers.copy()
            new_headers['x-retry-count'] = new_retry_count

            # Republish with updated headers
            new_properties = pika.BasicProperties(
                delivery_mode=properties.delivery_mode,
                content_type=properties.content_type,
                correlation_id=properties.correlation_id,
                headers=new_headers
            )

            ch.basic_publish(
                exchange='wikipedia_chatbot_exchange',
                routing_key='wikipedia_chatbot_queue',
                body=body,
                properties=new_properties
            )

            # ACK original message (we already republished it)
            ch.basic_ack(delivery_tag=method.delivery_tag)


async def process_question(message: dict, correlation_id: str, user_id: str):
    """Process a question using ChatGPT and Wikipedia."""
    try:
        question = message.get('message')
        logger.info(f"Processing question from {user_id}: {question}")

        # Get Wikipedia URL from ChatGPT
        logger.info(f"Asking ChatGPT for Wikipedia URL...")
        wikipedia_url = await chatgpt_service.get_wikipedia_url_from_question(question)
        logger.info(f"Wikipedia URL: {wikipedia_url}")

        # Download Wikipedia content
        logger.info(f"Downloading Wikipedia content...")
        wikipedia_content = await wikipedia_service.get_content_from_url(wikipedia_url)

        if not wikipedia_content:
            logger.warning(f"No Wikipedia content found")
            response = {
                "message": f"No se pudo obtener información de Wikipedia para: {wikipedia_url}",
                "user_id": user_id,
                "correlation_id": correlation_id
            }
        else:
            # Generate answer with ChatGPT
            logger.info(f"Generating answer with ChatGPT...")
            answer = await chatgpt_service.answer_question_with_wikipedia(question, wikipedia_content, wikipedia_url)
            response = {
                "message": answer,
                "user_id": user_id,
                "correlation_id": correlation_id
            }

        # Publish response to queue
        rabbitmq_service.publish_event(response, correlation_id=correlation_id)
        logger.info(f"Response published - User: {user_id}, Correlation: {correlation_id}")

    except Exception as e:
        logger.error(f"Error processing question for user {user_id}: {e}")
        # Publish error response to same queue
        rabbitmq_service.publish_event({
            "message": f"Error procesando la pregunta: {str(e)}",
            "error": str(e),
            "user_id": user_id,
            "correlation_id": correlation_id
        }, correlation_id=correlation_id)


def start_consumer():
    logger.info("Starting RabbitMQ consumer")
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
