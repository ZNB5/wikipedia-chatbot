"""Custom exceptions for the application"""


class ChatbotException(Exception):
    """Base exception for chatbot"""
    def __init__(self, message: str, error_code: str = "INTERNAL_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class WikipediaException(ChatbotException):
    """Exception for Wikipedia service errors"""
    def __init__(self, message: str, error_code: str = "WIKIPEDIA_ERROR"):
        super().__init__(message, error_code)


class TopicNotFoundError(WikipediaException):
    """Exception when topic is not found on Wikipedia"""
    def __init__(self, topic: str):
        super().__init__(
            f"Topic '{topic}' not found on Wikipedia",
            "WIKIPEDIA_NOT_FOUND"
        )


class ChatGPTException(ChatbotException):
    """Exception for ChatGPT service errors"""
    def __init__(self, message: str, error_code: str = "CHATGPT_ERROR"):
        super().__init__(message, error_code)


class RabbitMQException(ChatbotException):
    """Exception for RabbitMQ service errors"""
    def __init__(self, message: str, error_code: str = "RABBITMQ_ERROR"):
        super().__init__(message, error_code)


class ValidationException(ChatbotException):
    """Exception for validation errors"""
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")


class AuthenticationException(ChatbotException):
    """Exception for authentication errors"""
    def __init__(self, message: str = "Invalid OpenAI API key"):
        super().__init__(message, "AUTHENTICATION_ERROR")


class RateLimitException(ChatbotException):
    """Exception for rate limit errors"""
    def __init__(self, message: str = "OpenAI rate limit exceeded"):
        super().__init__(message, "RATE_LIMIT_ERROR")


class OpenAIException(ChatbotException):
    """Exception for OpenAI service errors"""
    def __init__(self, message: str, error_code: str = "OPENAI_ERROR"):
        super().__init__(message, error_code)
