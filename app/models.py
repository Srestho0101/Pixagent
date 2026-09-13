from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


RepairStatus = Literal[
    "pending",
    "in_progress",
    "waiting_parts",
    "completed",
]


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CreateTicketRequest(BaseModel):
    customer_name: str = Field(min_length=1, max_length=120)
    device_info: str = Field(min_length=1, max_length=500)


class UpdateTicketRequest(BaseModel):
    customer_name: str | None = Field(default=None, min_length=1, max_length=120)
    device_info: str | None = Field(default=None, min_length=1, max_length=500)
    status: RepairStatus | None = None


class TicketResponse(BaseModel):
    id: int
    customer_name: str
    device_info: str
    status: str
    technician_id: int
    created_at: datetime


class CreateLogRequest(BaseModel):
    ticket_id: int
    note: str = Field(min_length=1, max_length=1000)


class CustomerLogResponse(BaseModel):
    id: int
    ticket_id: int
    note: str
    created_at: datetime


class CustomerTicketLogsResponse(BaseModel):
    ticket_id: int
    status: str
    logs: list[CustomerLogResponse]


class ChatRequest(BaseModel):
    ticket_id: int | None = Field(default=None, ge=1)
    message: str = Field(min_length=1, max_length=2000)


class DeleteResponse(BaseModel):
    message: str
