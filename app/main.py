from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime
import logging
from uuid import uuid4

from config.settings import settings
from utils.logger import setup_logging
from utils.exceptions import ChatbotException, AuthenticationException, RateLimitException, OpenAIException
from schemas.request import ChatWikipediaRequest, HealthCheckResponse
from schemas.response import ChatWikipediaResponse, ErrorResponse
from services.wikipedia_service import WikipediaService
from services.chatgpt_service import ChatGPTService

logger = setup_logging()
wikipedia_service = WikipediaService()
chatgpt_service = ChatGPTService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up")
    yield
    logger.info("Application shutting down")


app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json"
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(OpenAIException)
async def openai_exception_handler(request, exc: OpenAIException):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE if exc.error_code == "OPENAI_API_ERROR" else status.HTTP_500_INTERNAL_SERVER_ERROR
    logger.error(f"OpenAI exception: {exc.error_code} - {exc.message}")
    return JSONResponse(status_code=status_code, content=ErrorResponse(error_code=exc.error_code, message=exc.message, request_id=request_id).model_dump(mode='json'))

@app.exception_handler(ChatbotException)
async def chatbot_exception_handler(request, exc: ChatbotException):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    logger.error(f"Chatbot exception: {exc.error_code} - {exc.message}")
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=ErrorResponse(error_code=exc.error_code, message=exc.message, request_id=request_id).model_dump(mode='json'))

@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=ErrorResponse(error_code="INTERNAL_ERROR", message="An unexpected error occurred", details=str(exc) if settings.debug else None, request_id=request_id).model_dump(mode='json'))


@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check():
    return HealthCheckResponse(status="healthy", version=settings.api_version, timestamp=datetime.utcnow())


@app.post("/chat-wikipedia", response_model=ChatWikipediaResponse, status_code=status.HTTP_200_OK, tags=["Chat"])
async def chat_wikipedia(request: ChatWikipediaRequest):
    """Chat endpoint for Wikipedia questions."""
    try:
        logger.info(f"Chat Wikipedia request: {request.message}")

        # Step 1: Get Wikipedia URL from ChatGPT
        wikipedia_url = await chatgpt_service.get_wikipedia_url_from_question(request.message)
        logger.info(f"Wikipedia URL: {wikipedia_url}")

        # Step 2: Download Wikipedia content
        wikipedia_content = await wikipedia_service.get_content_from_url(wikipedia_url)

        if not wikipedia_content:
            logger.warning(f"No Wikipedia content found")
            return ChatWikipediaResponse(
                message=f"No se pudo obtener información de Wikipedia para: {wikipedia_url}"
            )

        # Step 3: Generate answer with ChatGPT
        answer = await chatgpt_service.answer_question_with_wikipedia(
            request.message, wikipedia_content, wikipedia_url
        )

        logger.info(f"Answer generated for: {request.message}")
        return ChatWikipediaResponse(message=answer)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port, log_level=settings.log_level.lower())
