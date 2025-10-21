from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime
import logging
from uuid import uuid4

from config.settings import settings
from utils.logger import setup_logging
from utils.exceptions import (
    ChatbotException,
    TopicNotFoundError,
    AuthenticationException,
    RateLimitException,
    OpenAIException
)
from schemas.request import ChatRequest, HealthCheckResponse
from schemas.response import ChatResponse, ErrorResponse
from services.wikipedia_service import WikipediaService
from services.chatgpt_service import ChatGPTService
from events.event_producer import EventProducer


# Setup logging
logger = setup_logging()


# Initialize services
wikipedia_service = WikipediaService()
chatgpt_service = ChatGPTService()
event_producer = EventProducer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    logger.info("Application starting up")
    yield
    logger.info("Application shutting down")


# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(OpenAIException)
async def openai_exception_handler(request, exc: OpenAIException):
    """Handle OpenAI exceptions"""
    request_id = request.headers.get("X-Request-ID", str(uuid4()))

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    if exc.error_code == "OPENAI_API_ERROR":
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    error_response = ErrorResponse(
        error_code=exc.error_code,
        message=exc.message,
        request_id=request_id
    )

    logger.error(f"OpenAI exception: {exc.error_code} - {exc.message}")

    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(mode='json')
    )


@app.exception_handler(ChatbotException)
async def chatbot_exception_handler(request, exc: ChatbotException):
    """Handle chatbot exceptions"""
    request_id = request.headers.get("X-Request-ID", str(uuid4()))

    error_response = ErrorResponse(
        error_code=exc.error_code,
        message=exc.message,
        request_id=request_id
    )

    logger.error(f"Chatbot exception: {exc.error_code} - {exc.message}")

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_response.model_dump(mode='json')
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions"""
    request_id = request.headers.get("X-Request-ID", str(uuid4()))

    error_response = ErrorResponse(
        error_code="INTERNAL_ERROR",
        message="An unexpected error occurred",
        details=str(exc) if settings.debug else None,
        request_id=request_id
    )

    logger.error(f"Unexpected error: {exc}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode='json')
    )


# Routes
@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return HealthCheckResponse(
        status="healthy",
        version=settings.api_version,
        timestamp=datetime.utcnow()
    )


@app.post(
    "/api/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    tags=["Chat"],
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def chat(request: ChatRequest):
    """
    Answer a question by extracting the topic and explaining it with Wikipedia + ChatGPT.

    This endpoint:
    1. Extracts the topic from the user's question
    2. Searches for the topic on Wikipedia
    3. Uses ChatGPT to generate a simple explanation
    4. Emits events for each transaction
    5. Returns the explanation with Wikipedia sources

    Request example:
    ```json
    {
        "question": "¿Qué es la Inteligencia Artificial?",
        "session_id": "session-123"
    }
    ```
    """

    # Generate request ID
    request_id = str(uuid4())

    try:
        logger.info(f"Chat request received for question: {request.question} (Request ID: {request_id})")

        # Extract topic from question
        topic = await chatgpt_service.extract_topic_from_question(request.question)
        logger.info(f"Extracted topic: '{topic}' from question: '{request.question}'")

        # Publish event - explanation requested
        event_producer.publish_explanation_requested(
            request_id=request_id,
            topic=topic,
            session_id=request.session_id
        )

        # Fetch Wikipedia content
        wikipedia_data = await wikipedia_service.search_topic(topic)

        if not wikipedia_data:
            logger.warning(f"Topic not found: {topic}")
            event_producer.publish_explanation_failed(
                request_id=request_id,
                topic=topic,
                error="WIKIPEDIA_NOT_FOUND"
            )
            raise TopicNotFoundError(topic)

        content, summary, sources = wikipedia_data

        # Generate explanation with ChatGPT
        explanation = await chatgpt_service.explain_topic(topic, content)

        # Publish event - explanation completed
        event_producer.publish_explanation_completed(
            request_id=request_id,
            topic=topic,
            explanation=explanation,
            sources=sources
        )

        # Build message with URLs
        message_with_urls = explanation
        if sources:
            urls_text = "\n\nFuentes verificables:"
            for source in sources:
                urls_text += f"\n- {source.title}: {source.url}"
            message_with_urls += urls_text

        response = ChatResponse(
            message=message_with_urls,
            session_id=request.session_id,
            request_id=request_id
        )

        logger.info(f"Chat response generated successfully for topic: {topic}")
        return response

    except (TopicNotFoundError, AuthenticationException, RateLimitException, OpenAIException) as e:
        logger.error(f"Known error: {e.error_code} - {e.message}")
        raise

    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}")
        event_producer.publish_explanation_failed(
            request_id=request_id,
            topic=topic if 'topic' in locals() else "unknown",
            error=str(e)
        )
        raise


@app.get(
    "/api/status",
    tags=["Status"],
    responses={200: {"description": "Status information"}}
)
async def get_status():
    """Get API status and version information"""
    return {
        "status": "running",
        "version": settings.api_version,
        "timestamp": datetime.utcnow().isoformat(),
        "debug": settings.debug
    }


# Versioning info
@app.get("/api/versions", tags=["Info"])
async def get_versions():
    """Get available API versions"""
    return {
        "current_version": settings.api_version,
        "available_versions": ["v1"],
        "info": "Currently only v1 is available"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower()
    )
