import pika
import json
import logging
from typing import Dict, Any
from config.settings import settings
import time


logger = logging.getLogger(__name__)


class RabbitMQService:
    """Service for managing RabbitMQ connections and messaging"""

    def __init__(self):
        self.connection = None
        self.channel = None
        self._ensure_connection()

    def _ensure_connection(self):
        """Ensure connection to RabbitMQ with retry logic"""
        retries = 0
        max_retries = settings.max_retries

        while retries < max_retries:
            try:
                credentials = pika.PlainCredentials(
                    settings.rabbitmq_user,
                    settings.rabbitmq_password
                )

                connection_params = pika.ConnectionParameters(
                    host=settings.rabbitmq_host,
                    port=settings.rabbitmq_port,
                    credentials=credentials,
                    connection_attempts=3,
                    retry_delay=2,
                    heartbeat=600
                )

                self.connection = pika.BlockingConnection(connection_params)
                self.channel = self.connection.channel()

                # Declare exchange and queue
                self.channel.exchange_declare(
                    exchange=settings.rabbitmq_exchange_name,
                    exchange_type='direct',
                    durable=True
                )

                self.channel.queue_declare(
                    queue=settings.rabbitmq_queue_name,
                    durable=True
                )

                self.channel.queue_bind(
                    queue=settings.rabbitmq_queue_name,
                    exchange=settings.rabbitmq_exchange_name,
                    routing_key=settings.rabbitmq_queue_name
                )

                logger.info("Successfully connected to RabbitMQ")
                return

            except Exception as e:
                retries += 1
                logger.warning(f"RabbitMQ connection attempt {retries}/{max_retries} failed: {e}")
                if retries < max_retries:
                    time.sleep(2 ** retries)  # Exponential backoff

        logger.error("Failed to connect to RabbitMQ after retries")
        raise Exception("Could not connect to RabbitMQ")

    def publish_event(self, event: Dict[str, Any], routing_key: str = None):
        """
        Publish an event to RabbitMQ.

        Args:
            event: Event dictionary
            routing_key: RabbitMQ routing key (defaults to queue name)
        """
        try:
            if not self.connection or self.connection.is_closed:
                self._ensure_connection()

            routing_key = routing_key or settings.rabbitmq_queue_name
            message = json.dumps(event)

            self.channel.basic_publish(
                exchange=settings.rabbitmq_exchange_name,
                routing_key=routing_key,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
                    content_type='application/json'
                )
            )

            logger.info(f"Event published successfully with routing_key: {routing_key}")

        except Exception as e:
            logger.error(f"Error publishing event to RabbitMQ: {e}")
            raise

    def consume_events(self, callback):
        """
        Start consuming events from RabbitMQ.

        Args:
            callback: Function to call when an event is received
        """
        try:
            if not self.connection or self.connection.is_closed:
                self._ensure_connection()

            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(
                queue=settings.rabbitmq_queue_name,
                on_message_callback=callback
            )

            logger.info(f"Starting to consume events from queue: {settings.rabbitmq_queue_name}")
            self.channel.start_consuming()

        except Exception as e:
            logger.error(f"Error consuming events: {e}")
            raise

    def close(self):
        """Close RabbitMQ connection"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")
