"""AI Assistant API: natural-language questions about the live flood situation.
"""
from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.assistant import engine

router = APIRouter(prefix="/assistant", tags=["AI Assistant"])


class ChatTurn(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., max_length=2000)
    history: Optional[List[ChatTurn]] = None


@router.get("/status")
def assistant_status():
    """Which engine answers (Claude or the built-in NLP) and suggested questions."""
    return engine.status()


@router.post("/chat")
def assistant_chat(req: ChatRequest):
    """Ask the assistant a question. Runs in a worker thread because the Claude call blocks."""
    history = [t.model_dump() for t in (req.history or [])]
    return engine.chat(req.message, history)
