from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class ChatRequest(BaseModel):
    """Schema for chat query requests"""
    question: str = Field(..., min_length=1, max_length=500, description="Question about a topic (e.g., 'What is Python?')")
    session_id: Optional[str] = Field(None, description="Session ID for tracking")

    @validator('question')
    def validate_question(cls, v):
        if not v.strip():
            raise ValueError('Question cannot be empty or whitespace only')
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "question": "¿Qué es la Inteligencia Artificial?",
                "session_id": "session-123"
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
