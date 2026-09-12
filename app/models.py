from datetime import datetime

from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CreateTicketRequest(BaseModel):
    customer_name: str
    device_info: str


class TicketResponse(BaseModel):
    id: int
    customer_name: str
    device_info: str
    status: str
    technician_id: int
    created_at: datetime


class CreateLogRequest(BaseModel):
    ticket_id: int
    note: str


class CustomerLogResponse(BaseModel):
    id: int
    ticket_id: int
    note: str
    created_at: datetime


class CustomerTicketLogsResponse(BaseModel):
    ticket_id: int
    status: str
    logs: list[CustomerLogResponse]
