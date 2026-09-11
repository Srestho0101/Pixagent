from fastapi import APIRouter, HTTPException

from app.auth import (
    create_access_token,
    verify_password,
)

from app.database import get_connection
from app.models import LoginRequest, LoginResponse


router = APIRouter()


@router.post(
    "/login",
    response_model=LoginResponse
)
def login(data: LoginRequest):

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT id, password_hash
                FROM technicians
                WHERE email = %s
                """,
                (data.email,)
            )

            technician = cur.fetchone()

    if not technician:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    technician_id, password_hash = technician

    if not verify_password(
        data.password,
        password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token = create_access_token(
        str(technician_id)
    )

    return LoginResponse(
        access_token=token
    )