from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_technician
from app.database import get_connection
from app.models import (
    CreateTicketRequest,
    TicketResponse,
    UpdateTicketRequest,
    DeleteResponse,
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


@router.patch(
    "/tickets/{ticket_id}",
    response_model=TicketResponse,
)
def update_ticket(
    ticket_id: int,
    data: UpdateTicketRequest,
    technician_id: str = Depends(
        get_current_technician
    ),
):
    customer_name = (
        data.customer_name.strip()
        if data.customer_name is not None
        else None
    )
    device_info = (
        data.device_info.strip()
        if data.device_info is not None
        else None
    )

    if customer_name == "" or device_info == "":
        raise HTTPException(
            status_code=422,
            detail="Customer name and device information cannot be blank",
        )

    if customer_name is None and device_info is None and data.status is None:
        raise HTTPException(
            status_code=400,
            detail="At least one ticket field is required",
        )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE tickets
                SET
                    customer_name = COALESCE(%s, customer_name),
                    device_info = COALESCE(%s, device_info),
                    status = COALESCE(%s, status)
                WHERE id = %s
                  AND technician_id = %s
                RETURNING
                    id,
                    customer_name,
                    device_info,
                    status,
                    technician_id,
                    created_at
                """,
                (
                    customer_name,
                    device_info,
                    data.status,
                    ticket_id,
                    technician_id,
                ),
            )

            ticket = cur.fetchone()

        if not ticket:
            raise HTTPException(
                status_code=404,
                detail="Ticket not found",
            )

        conn.commit()

    return {
        "id": ticket[0],
        "customer_name": ticket[1],
        "device_info": ticket[2],
        "status": ticket[3],
        "technician_id": ticket[4],
        "created_at": ticket[5],
    }


@router.delete(
    "/tickets/{ticket_id}",
    response_model=DeleteResponse,
)
def delete_ticket(
    ticket_id: int,
    technician_id: str = Depends(
        get_current_technician
    ),
):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id
                FROM tickets
                WHERE id = %s
                  AND technician_id = %s
                """,
                (ticket_id, technician_id),
            )

            if not cur.fetchone():
                raise HTTPException(
                    status_code=404,
                    detail="Ticket not found",
                )

            # Delete dependent logs explicitly so this works even when the
            # database foreign key is not configured with ON DELETE CASCADE.
            cur.execute(
                "DELETE FROM repair_logs WHERE ticket_id = %s",
                (ticket_id,),
            )
            cur.execute(
                """
                DELETE FROM tickets
                WHERE id = %s
                  AND technician_id = %s
                """,
                (ticket_id, technician_id),
            )

        conn.commit()

    return {
        "message": f"Ticket {ticket_id} deleted",
    }
