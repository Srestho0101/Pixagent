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