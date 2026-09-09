from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    token: str
    technician: dict

class TicketCreate(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100)
    device_info: str = Field(..., min_length=2, max_length=500)
    status: str = Field(default="pending", pattern="^(pending|in_progress|waiting_parts|completed)$")

class TicketResponse(BaseModel):
    id: int
    customer_name: str
    device_info: str
    status: str
    technician_id: int
    created_at: datetime
    logs: Optional[List[dict]] = []

class LogCreate(BaseModel):
    ticket_id: int
    note: str = Field(..., min_length=1, max_length=1000)

class LogResponse(BaseModel):
    id: int
    ticket_id: int
    technician_id: int
    note: str
    created_at: datetime

class ChatRequest(BaseModel):
    ticket_id: int
    message: str = Field(..., min_length=1, max_length=500)
    history: Optional[List[dict]] = []

class ChatResponse(BaseModel):
    response: str