from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.agent import chat_stream
from app.models import ChatRequest


router = APIRouter()


@router.post("/chat")
def chat(data: ChatRequest):
    return StreamingResponse(
        chat_stream(data.ticket_id, data.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
