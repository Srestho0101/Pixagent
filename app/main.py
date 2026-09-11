from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import auth, tickets

from fastapi import Depends

from app.auth import get_current_technician


app = FastAPI(
    title="Laptop Repair Shop API",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    auth.router,
    prefix="/api"
)


@app.get("/")
def root():
    return {
        "message": "Laptop Repair Shop API"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }

@app.get("/api/me")
def get_me(
    technician_id: str = Depends(
        get_current_technician
    )
):
    return {
        "technician_id": technician_id
    }