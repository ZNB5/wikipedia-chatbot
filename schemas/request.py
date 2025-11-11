from pydantic import BaseModel, Field, validator
from datetime import datetime


class ChatRequest(BaseModel):
    """Schema for chat query requests"""
    question: str = Field(..., min_length=1, max_length=500, description="Question about a topic (e.g., 'What is Python?')")

    @validator('question')
    def validate_question(cls, v):
        if not v.strip():
            raise ValueError('Question cannot be empty or whitespace only')
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "question": "¿Qué es la Inteligencia Artificial?"
            }
        }


class ChatWikipediaRequest(BaseModel):
    """Schema for chat Wikipedia requests"""
    message: str = Field(..., min_length=1, max_length=500, description="Question to ask about Wikipedia")

    @validator('message')
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError('Message cannot be empty or whitespace only')
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "message": "¿Qué es la Inteligencia Artificial?"
            }
        }


class HealthCheckResponse(BaseModel):
    """Schema for health check response"""
    status: str
    version: str
    timestamp: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "v1",
                "timestamp": "2024-01-01T12:00:00"
            }
        }
