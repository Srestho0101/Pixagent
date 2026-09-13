from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.agent import chat_stream
from app.models import ChatRequest


router = APIRouter()


@router.post("/chat")
def chat(data: ChatRequest):
    history = [
        item.model_dump() if hasattr(item, "model_dump") else item.dict()
        for item in data.history
    ]
    return StreamingResponse(
        chat_stream(
            data.ticket_id,
            data.message,
            history,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
