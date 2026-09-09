from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

class Technician(BaseModel):
    id: int
    email: EmailStr
    name: str
    password_hash: str
    created_at: datetime

class Ticket(BaseModel):
    id: int
    customer_name: str
    device_info: str
    status: str  # pending, in_progress, waiting_parts, completed
    technician_id: int
    created_at: datetime

class RepairLog(BaseModel):
    id: int
    ticket_id: int
    technician_id: int
    note: str
    created_at: datetime