from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # API Configuration
    api_version: str = "v1"
    api_title: str = "Wikipedia Chatbot API"
    api_description: str = "A microservice that explains Wikipedia topics using ChatGPT"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-5-mini"
    openai_temperature: float = 0.7
    openai_max_tokens: int = 500

    # RabbitMQ Configuration
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"
    rabbitmq_queue_name: str = "wikipedia_chatbot_queue"
    rabbitmq_exchange_name: str = "wikipedia_chatbot_exchange"

    # Application Configuration
    log_level: str = "INFO"
    max_retries: int = 3
    request_timeout: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
