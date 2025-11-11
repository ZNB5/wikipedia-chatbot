import pika
import json
import logging
from typing import Dict, Any, Optional
from config.settings import settings
import time
import uuid


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

                # Declare Dead Letter Exchange (DLX)
                dlx_exchange = f"{settings.rabbitmq_exchange_name}_dlx"
                dlq_name = f"{settings.rabbitmq_queue_name}_dlq"

                self.channel.exchange_declare(
                    exchange=dlx_exchange,
                    exchange_type='direct',
                    durable=True
                )

                # Declare Dead Letter Queue (DLQ)
                self.channel.queue_declare(
                    queue=dlq_name,
                    durable=True
                )

                self.channel.queue_bind(
                    queue=dlq_name,
                    exchange=dlx_exchange,
                    routing_key=settings.rabbitmq_queue_name
                )

                # Declare main exchange and queue with DLX
                self.channel.exchange_declare(
                    exchange=settings.rabbitmq_exchange_name,
                    exchange_type='direct',
                    durable=True
                )

                # Main queue with DLX configuration
                self.channel.queue_declare(
                    queue=settings.rabbitmq_queue_name,
                    durable=True,
                    arguments={
                        'x-dead-letter-exchange': dlx_exchange,
                        'x-dead-letter-routing-key': settings.rabbitmq_queue_name
                    }
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

    def publish_event(self, event: Dict[str, Any], routing_key: str = None, correlation_id: str = None):
        """
        Publish an event to RabbitMQ with correlation support.

        Simple pattern: Always publishes to the named exchange and routing key.

        Args:
            event: Event dictionary
            routing_key: RabbitMQ routing key (defaults to queue name)
            correlation_id: Correlation ID to track request-response
        """
        try:
            if not self.connection or self.connection.is_closed:
                self._ensure_connection()

            routing_key = routing_key or settings.rabbitmq_queue_name
            message = json.dumps(event)

            props = pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
                content_type='application/json',
                correlation_id=correlation_id
            )

            # Always use named exchange for simplicity
            self.channel.basic_publish(
                exchange=settings.rabbitmq_exchange_name,
                routing_key=routing_key,
                body=message,
                properties=props
            )

            logger.info(f"Event published - exchange: {settings.rabbitmq_exchange_name}, routing_key: {routing_key}, correlation_id: {correlation_id}")

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

    def publish_and_wait(self, event: Dict[str, Any], timeout: int = 30) -> Optional[Dict[str, Any]]:
        """
        Publish an event to RabbitMQ and wait for response from SAME queue.

        Simple event-driven pattern:
        1. Publishes message with unique correlation_id to wikipedia_chatbot_queue
        2. Consumes from SAME queue with unique consumer_tag, filtering by correlation_id
        3. Messages that don't match are requeued for others (NACK + requeue)
        4. Cancels consumer after receiving response or timeout
        5. Returns response or None if timeout

        This is the simple single-queue pattern, similar to traditional message queues.
        Each API request creates a temporary consumer that is properly cleaned up.

        Args:
            event: Event dictionary to publish
            timeout: Timeout in seconds (default: 30)

        Returns:
            Response dictionary or None if timeout
        """
        consumer_tag = None
        try:
            if not self.connection or self.connection.is_closed:
                self._ensure_connection()

            # Generate unique correlation_id and consumer_tag
            correlation_id = str(uuid.uuid4())
            consumer_tag = f"api_consumer_{correlation_id}"
            response = {'received': False, 'data': None}

            def on_response(ch, method, properties, body):
                """Callback to handle response messages - filter by correlation_id"""
                if properties.correlation_id == correlation_id:
                    # This is our response
                    response['received'] = True
                    response['data'] = json.loads(body)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                else:
                    # Not our response, requeue for others
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

            # Set up consumer on SAME queue (will filter responses)
            # Using consumer_tag to identify this specific consumer
            self.channel.basic_consume(
                queue=settings.rabbitmq_queue_name,
                on_message_callback=on_response,
                auto_ack=False,
                consumer_tag=consumer_tag
            )

            # Publish the request (no reply_to needed)
            self.publish_event(event, correlation_id=correlation_id)
            logger.info(f"Published request with correlation_id: {correlation_id}, consumer_tag: {consumer_tag}")

            # Wait for response with timeout
            connection_start = time.time()
            while not response['received']:
                if time.time() - connection_start > timeout:
                    logger.warning(f"Timeout waiting for response (correlation_id: {correlation_id})")
                    break

                # Process events with short timeout
                self.connection.process_data_events(time_limit=1)

            # Always cancel the consumer to clean up
            if consumer_tag:
                try:
                    self.channel.basic_cancel(consumer_tag)
                    logger.info(f"Cancelled consumer: {consumer_tag}")
                except Exception as e:
                    logger.warning(f"Error cancelling consumer {consumer_tag}: {e}")

            if response['received']:
                logger.info(f"Received response for correlation_id: {correlation_id}")
                return response['data']
            else:
                return None

        except Exception as e:
            logger.error(f"Error in publish_and_wait: {e}")
            # Try to cancel consumer even on error
            if consumer_tag:
                try:
                    self.channel.basic_cancel(consumer_tag)
                except:
                    pass
            raise

    def close(self):
        """Close RabbitMQ connection"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")
