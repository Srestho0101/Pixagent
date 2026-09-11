from fastapi import APIRouter, Depends

from app.auth import get_current_technician
from app.database import get_connection
from app.models import (
    CreateTicketRequest,
    TicketResponse,
)


router = APIRouter()


@router.post(
    "/tickets",
    response_model=TicketResponse
)
def create_ticket(
    data: CreateTicketRequest,
    technician_id: str = Depends(
        get_current_technician
    ),
):

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO tickets (
                    customer_name,
                    device_info,
                    technician_id
                )
                VALUES (%s, %s, %s)
                RETURNING
                    id,
                    customer_name,
                    device_info,
                    status,
                    technician_id,
                    created_at
                """,
                (
                    data.customer_name,
                    data.device_info,
                    technician_id,
                ),
            )

            ticket = cur.fetchone()

        conn.commit()

    return {
        "id": ticket[0],
        "customer_name": ticket[1],
        "device_info": ticket[2],
        "status": ticket[3],
        "technician_id": ticket[4],
        "created_at": ticket[5],
    }


@router.get(
    "/tickets/my",
    response_model=list[TicketResponse]
)
def get_my_tickets(
    technician_id: str = Depends(
        get_current_technician
    ),
):

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    id,
                    customer_name,
                    device_info,
                    status,
                    technician_id,
                    created_at
                FROM tickets
                WHERE technician_id = %s
                ORDER BY created_at DESC
                """,
                (technician_id,),
            )

            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "customer_name": row[1],
            "device_info": row[2],
            "status": row[3],
            "technician_id": row[4],
            "created_at": row[5],
        }
        for row in rows
    ]