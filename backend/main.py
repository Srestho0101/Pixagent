import asyncio
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncIterator, Literal

import bcrypt
import httpx
import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

load_dotenv()

VALID_STATUSES = {"pending", "in_progress", "waiting_parts", "completed"}


def required_setting(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


class Settings:
    supabase_url = required_setting("SUPABASE_URL").rstrip("/")
    supabase_key = required_setting("SUPABASE_KEY")
    mistral_api_key = required_setting("MISTRAL_API_KEY")
    jwt_secret = required_setting("JWT_SECRET")
    mistral_model = os.getenv("MISTRAL_MODEL", "mistral-small-latest")
    origins = [origin.strip() for origin in os.getenv("FRONTEND_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500").split(",") if origin.strip()]


settings = Settings()
app = FastAPI(title="FixFlow API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


class LoginInput(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class TicketCreate(BaseModel):
    customer_name: str = Field(min_length=1, max_length=120)
    device_info: str = Field(min_length=1, max_length=240)
    status: Literal["pending", "in_progress", "waiting_parts", "completed"] = "pending"


class LogCreate(BaseModel):
    ticket_id: str = Field(pattern=r"^RF-[0-9]{6}$")
    note: str = Field(min_length=1, max_length=2000)


class ChatInput(BaseModel):
    ticket_id: str = Field(pattern=r"^RF-[0-9]{6}$")
    message: str = Field(min_length=1, max_length=2000)


class Supabase:
    def __init__(self) -> None:
        self.base_url = f"{settings.supabase_url}/rest/v1"
        self.headers = {
            "apikey": settings.supabase_key,
            "Authorization": f"Bearer {settings.supabase_key}",
            "Content-Type": "application/json",
        }

    async def request(self, method: str, table: str, *, params: dict[str, str] | None = None, payload: Any = None, prefer: str | None = None) -> list[dict[str, Any]]:
        headers = dict(self.headers)
        if prefer:
            headers["Prefer"] = prefer
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.request(method, f"{self.base_url}/{table}", params=params, json=payload, headers=headers)
        if response.is_error:
            raise HTTPException(status_code=502, detail="Database request failed")
        if not response.content:
            return []
        return response.json()


db = Supabase()


def ticket_dto(ticket: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": ticket["public_id"],
        "customer_name": ticket["customer_name"],
        "device_info": ticket["device_info"],
        "status": ticket["status"],
        "created_at": ticket["created_at"],
    }


async def find_ticket(public_id: str, technician_id: int | None = None) -> dict[str, Any]:
    params = {"select": "*", "public_id": f"eq.{public_id}", "limit": "1"}
    if technician_id is not None:
        params["technician_id"] = f"eq.{technician_id}"
    rows = await db.request("GET", "tickets", params=params)
    if not rows:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return rows[0]


async def recent_logs(ticket_id: int, limit: int = 5) -> list[dict[str, Any]]:
    return await db.request(
        "GET",
        "repair_logs",
        params={"select": "note,created_at", "ticket_id": f"eq.{ticket_id}", "order": "created_at.desc", "limit": str(limit)},
    )


def create_access_token(technician: dict[str, Any]) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(technician["id"]), "email": technician["email"], "iat": now, "exp": now + timedelta(hours=24)},
        settings.jwt_secret,
        algorithm="HS256",
    )


async def current_technician(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        claims = jwt.decode(authorization.removeprefix("Bearer "), settings.jwt_secret, algorithms=["HS256"])
        return {"id": int(claims["sub"]), "email": claims["email"]}
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/login")
async def login(payload: LoginInput) -> dict[str, Any]:
    email = payload.email.strip().lower()
    rows = await db.request("GET", "technicians", params={"select": "id,email,name,password_hash", "email": f"eq.{email}", "limit": "1"})
    if not rows:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    try:
        password_matches = bcrypt.checkpw(payload.password.encode(), rows[0]["password_hash"].encode())
    except (ValueError, TypeError):
        # Do not expose storage details to the client, but avoid turning a
        # malformed seed row into an opaque 500 response.
        password_matches = False
    if not password_matches:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    technician = rows[0]
    return {"access_token": create_access_token(technician), "token_type": "bearer", "technician": {"id": technician["id"], "email": technician["email"], "name": technician["name"]}}


@app.get("/api/tickets/my")
async def my_tickets(technician: dict[str, Any] = Depends(current_technician)) -> list[dict[str, Any]]:
    rows = await db.request("GET", "tickets", params={"select": "*", "technician_id": f"eq.{technician['id']}", "order": "created_at.desc"})
    return [ticket_dto(ticket) for ticket in rows]


@app.post("/api/tickets", status_code=status.HTTP_201_CREATED)
async def create_ticket(payload: TicketCreate, technician: dict[str, Any] = Depends(current_technician)) -> dict[str, Any]:
    # Retrying on the unique public-id constraint is intentionally bounded.
    for _ in range(3):
        public_id = f"RF-{secrets.randbelow(900000) + 100000}"
        rows = await db.request(
            "POST", "tickets",
            payload={"public_id": public_id, "customer_name": payload.customer_name.strip(), "device_info": payload.device_info.strip(), "status": payload.status, "technician_id": technician["id"]},
            prefer="return=representation",
        )
        if rows:
            return ticket_dto(rows[0])
    raise HTTPException(status_code=503, detail="Could not allocate a ticket ID; please retry")


@app.post("/api/logs", status_code=status.HTTP_201_CREATED)
async def add_log(payload: LogCreate, technician: dict[str, Any] = Depends(current_technician)) -> dict[str, Any]:
    ticket = await find_ticket(payload.ticket_id, technician["id"])
    rows = await db.request(
        "POST", "repair_logs",
        payload={"ticket_id": ticket["id"], "technician_id": technician["id"], "note": payload.note.strip()},
        prefer="return=representation",
    )
    return rows[0]


@app.get("/api/tickets/{ticket_id}")
async def public_ticket(ticket_id: str) -> dict[str, Any]:
    # This intentionally returns only the customer-safe ticket fields.
    return ticket_dto(await find_ticket(ticket_id.upper()))


TOOLS = [
    {"type": "function", "function": {"name": "get_ticket_status", "description": "Get the current repair status and device for this ticket.", "parameters": {"type": "object", "properties": {"ticket_id": {"type": "string"}}, "required": ["ticket_id"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "get_recent_logs", "description": "Get the latest technician updates for this ticket.", "parameters": {"type": "object", "properties": {"ticket_id": {"type": "string"}, "limit": {"type": "integer", "minimum": 1, "maximum": 5}}, "required": ["ticket_id"], "additionalProperties": False}}},
]


async def mistral_completion(messages: list[dict[str, Any]], *, stream: bool = False, include_tools: bool = True) -> tuple[httpx.Response, httpx.AsyncClient]:
    client = httpx.AsyncClient(timeout=45)
    body: dict[str, Any] = {"model": settings.mistral_model, "messages": messages, "stream": stream}
    if include_tools:
        body.update({"tools": TOOLS, "tool_choice": "auto"})
    request = client.build_request(
        "POST", "https://api.mistral.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {settings.mistral_api_key}", "Content-Type": "application/json"},
        json=body,
    )
    response = await client.send(request, stream=stream)
    if response.is_error:
        await response.aclose()
        await client.aclose()
        raise HTTPException(status_code=502, detail="AI service request failed")
    return response, client


async def tool_result(name: str, arguments: dict[str, Any], ticket: dict[str, Any]) -> dict[str, Any]:
    # The model never gets authority to access a ticket other than the request's ticket.
    if name == "get_ticket_status":
        return {"ticket_id": ticket["public_id"], "status": ticket["status"], "device": ticket["device_info"]}
    if name == "get_recent_logs":
        logs = await recent_logs(ticket["id"], min(max(int(arguments.get("limit", 5)), 1), 5))
        return {"ticket_id": ticket["public_id"], "logs": logs}
    return {"error": "Unknown tool"}


@app.post("/api/chat")
async def chat(payload: ChatInput) -> StreamingResponse:
    ticket = await find_ticket(payload.ticket_id)
    initial_logs = await recent_logs(ticket["id"])
    logs_text = "\n".join(f"- {entry['created_at']}: {entry['note']}" for entry in initial_logs) or "No technician updates have been recorded."
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": f"You are FixFlow's repair-shop assistant. You may discuss only ticket {ticket['public_id']}. Device: {ticket['device_info']}. Current status: {ticket['status']}. Recent technician updates:\n{logs_text}\nRules: greetings are warm; progress answers must use the tool results or supplied context; never guess; if unknown say 'I don't have that info yet'; keep responses to 2–3 sentences; do not reveal internal IDs or technician details."},
        {"role": "user", "content": payload.message.strip()},
    ]
    first, first_client = await mistral_completion(messages)
    try:
        completion = first.json()["choices"][0]["message"]
    finally:
        await first.aclose()
        await first_client.aclose()

    tool_calls = completion.get("tool_calls", [])
    if tool_calls:
        messages.append({"role": "assistant", "content": completion.get("content") or "", "tool_calls": tool_calls})
        for call in tool_calls:
            try:
                arguments = json.loads(call["function"]["arguments"])
            except json.JSONDecodeError:
                arguments = {}
            result = await tool_result(call["function"]["name"], arguments, ticket)
            messages.append({"role": "tool", "tool_call_id": call["id"], "name": call["function"]["name"], "content": json.dumps(result)})
        final, final_client = await mistral_completion(messages, stream=True, include_tools=False)

        async def stream_mistral() -> AsyncIterator[str]:
            try:
                async for line in final.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line.removeprefix("data: ")
                    if data == "[DONE]":
                        break
                    try:
                        delta = json.loads(data)["choices"][0].get("delta", {}).get("content")
                    except (json.JSONDecodeError, IndexError, KeyError):
                        delta = None
                    if delta:
                        yield delta
            finally:
                await final.aclose()
                await final_client.aclose()

        return StreamingResponse(stream_mistral(), media_type="text/plain; charset=utf-8")

    content = completion.get("content") or "I don't have that info yet."

    async def stream_content() -> AsyncIterator[str]:
        yield content

    return StreamingResponse(stream_content(), media_type="text/plain; charset=utf-8")
