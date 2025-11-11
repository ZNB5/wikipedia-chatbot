from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ResponseStatus(str, Enum):
    """Response status enumeration"""
    SUCCESS = "success"
    PROCESSING = "processing"
    ERROR = "error"


class WikipediaSource(BaseModel):
    """Wikipedia source information"""
    title: str = Field(..., description="Article title")
    url: str = Field(..., description="Wikipedia URL")
    excerpt: Optional[str] = Field(None, description="Brief excerpt from the article")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Artificial Intelligence",
                "url": "https://en.wikipedia.org/wiki/Artificial_intelligence",
                "excerpt": "Artificial intelligence (AI) is..."
            }
        }


class ChatResponse(BaseModel):
    """Schema for chat response"""
    message: str = Field(..., description="Explanation of the topic with Wikipedia URLs included")
    request_id: str = Field(..., description="Unique request ID")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "La Inteligencia Artificial es... Fuente: https://en.wikipedia.org/wiki/Artificial_intelligence",
                "request_id": "req-12345"
            }
        }


class ChatWikipediaResponse(BaseModel):
    """Schema for chat Wikipedia response"""
    message: str = Field(..., description="Answer with Wikipedia source")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "La Inteligencia Artificial es la simulación de procesos de inteligencia humana por parte de máquinas. Fuente: https://es.wikipedia.org/wiki/Inteligencia_artificial"
            }
        }


class ErrorResponse(BaseModel):
    """Schema for error response"""
    status: ResponseStatus = ResponseStatus.ERROR
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")
    request_id: str = Field(..., description="Unique request ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "error_code": "WIKIPEDIA_NOT_FOUND",
                "message": "Topic not found on Wikipedia",
                "details": "The topic 'xyz123abc' could not be found",
                "request_id": "req-12345",
                "timestamp": "2024-01-01T12:00:00"
            }
        }


class EventMessage(BaseModel):
    """Schema for event messages in RabbitMQ"""
    event_id: str = Field(..., description="Unique event ID")
    request_id: str = Field(..., description="Request ID")
    event_type: str = Field(..., description="Type of event")
    topic: str = Field(..., description="Topic")
    status: str = Field(..., description="Status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Optional[dict] = Field(None, description="Additional event data")

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "evt-123",
                "request_id": "req-123",
                "event_type": "EXPLANATION_REQUESTED",
                "topic": "Python",
                "status": "processing",
                "timestamp": "2024-01-01T12:00:00",
                "data": {}
            }
        }
