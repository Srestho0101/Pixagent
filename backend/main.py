from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import List
import json
import os
from dotenv import load_dotenv
import asyncio

from backend.database import db
from backend.schemas import (
    LoginRequest, LoginResponse, TicketCreate, TicketResponse,
    LogCreate, LogResponse, ChatRequest
)
from auth import (
    hash_password, verify_password, create_access_token,
    get_current_technician, verify_token
)
from backend.agent import agent

load_dotenv()

app = FastAPI(title="Laptop Repair Shop AI Agent System")

# CORS configuration
frontend_origins = os.getenv("FRONTEND_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Laptop Repair Shop API", "status": "running"}

@app.post("/api/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """Technician login endpoint"""
    try:
        # Fetch technician from database
        result = db.get_client().table("technicians").select("*").eq("email", login_data.email).execute()
        
        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        technician = result.data[0]
        
        # Verify password
        if not verify_password(login_data.password, technician["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Create access token
        token = create_access_token(data={"sub": str(technician["id"])})
        
        return LoginResponse(
            token=token,
            technician={
                "id": technician["id"],
                "email": technician["email"],
                "name": technician["name"]
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login error: {str(e)}"
        )

@app.post("/api/tickets", response_model=TicketResponse)
async def create_ticket(
    ticket_data: TicketCreate,
    technician_id: int = Depends(get_current_technician)
):
    """Create a new repair ticket"""
    try:
        result = db.get_client().table("tickets").insert({
            "customer_name": ticket_data.customer_name,
            "device_info": ticket_data.device_info,
            "status": ticket_data.status,
            "technician_id": technician_id
        }).execute()
        
        if result.data:
            return result.data[0]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create ticket"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating ticket: {str(e)}"
        )

@app.get("/api/tickets/my", response_model=List[TicketResponse])
async def get_my_tickets(technician_id: int = Depends(get_current_technician)):
    """Get all tickets for the current technician"""
    try:
        result = db.get_client().table("tickets").select("*").eq("technician_id", technician_id).order("created_at", desc=True).execute()
        
        if result.data:
            # Fetch logs for each ticket
            tickets_with_logs = []
            for ticket in result.data:
                logs_result = db.get_client().table("repair_logs").select("*").eq("ticket_id", ticket["id"]).order("created_at", desc=True).limit(3).execute()
                ticket["logs"] = logs_result.data if logs_result.data else []
                tickets_with_logs.append(ticket)
            return tickets_with_logs
        
        return []
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching tickets: {str(e)}"
        )

@app.post("/api/logs", response_model=LogResponse)
async def add_log(
    log_data: LogCreate,
    technician_id: int = Depends(get_current_technician)
):
    """Add a technician note to a ticket"""
    try:
        # Verify ticket belongs to technician or exists
        ticket_result = db.get_client().table("tickets").select("*").eq("id", log_data.ticket_id).execute()
        
        if not ticket_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found"
            )
        
        # Add the log
        result = db.get_client().table("repair_logs").insert({
            "ticket_id": log_data.ticket_id,
            "technician_id": technician_id,
            "note": log_data.note
        }).execute()
        
        if result.data:
            return result.data[0]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add log"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding log: {str(e)}"
        )

@app.post("/api/chat")
async def chat(chat_request: ChatRequest):
    """Customer chat with AI agent - streaming response"""
    try:
        # Verify ticket exists
        ticket_result = db.get_client().table("tickets").select("*").eq("id", chat_request.ticket_id).execute()
        
        if not ticket_result.data:
            async def generate_error():
                error_msg = "I couldn't find that ticket ID. Please check your ticket number and try again."
                yield f"data: {json.dumps({'content': error_msg})}\n\n"
                yield "data: [DONE]\n\n"
            return StreamingResponse(generate_error(), media_type="text/event-stream")
        
        async def generate():
            # Get AI response
            response = await agent.chat(
                ticket_id=chat_request.ticket_id,
                message=chat_request.message,
                history=chat_request.history
            )
            
            # Stream the response
            yield f"data: {json.dumps({'content': response})}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(generate(), media_type="text/event-stream")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat error: {str(e)}"
        )

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected" if db.client else "disconnected",
        "agent": "ready" if agent.client else "not ready"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)