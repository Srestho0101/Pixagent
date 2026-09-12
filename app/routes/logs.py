from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_technician
from app.database import get_connection
from app.models import (
    CreateLogRequest,
    CustomerLogResponse,
    CustomerTicketLogsResponse,
)


router = APIRouter()


@router.get(
    "/tickets/{ticket_id}/logs",
    response_model=CustomerTicketLogsResponse,
)
def get_customer_logs(ticket_id: int):
    """Return the public repair history for a ticket.

    Customer access is currently based on possession of the ticket ID. The
    response intentionally excludes technician IDs and other internal data.
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    t.status,
                    l.id,
                    l.ticket_id,
                    l.note,
                    l.created_at
                FROM tickets AS t
                LEFT JOIN repair_logs AS l
                    ON l.ticket_id = t.id
                WHERE t.id = %s
                ORDER BY l.created_at DESC NULLS LAST
                """,
                (ticket_id,),
            )

            rows = cur.fetchall()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    return {
        "ticket_id": ticket_id,
        "status": rows[0][0],
        "logs": [
            {
                "id": row[1],
                "ticket_id": row[2],
                "note": row[3],
                "created_at": row[4],
            }
            for row in rows
            if row[1] is not None
        ],
    }


@router.post("/logs")
def create_log(
    data: CreateLogRequest,
    technician_id: str = Depends(
        get_current_technician
    ),
):

    with get_connection() as conn:
        with conn.cursor() as cur:

            # First make sure this ticket belongs
            # to the logged-in technician.
            cur.execute(
                """
                SELECT id
                FROM tickets
                WHERE id = %s
                  AND technician_id = %s
                """,
                (
                    data.ticket_id,
                    technician_id,
                ),
            )

            ticket = cur.fetchone()

            if not ticket:
                raise HTTPException(
                    status_code=404,
                    detail="Ticket not found"
                )

            # Ticket belongs to the technician,
            # so insert the repair log.
            cur.execute(
                """
                INSERT INTO repair_logs (
                    ticket_id,
                    technician_id,
                    note
                )
                VALUES (%s, %s, %s)
                RETURNING
                    id,
                    ticket_id,
                    technician_id,
                    note,
                    created_at
                """,
                (
                    data.ticket_id,
                    technician_id,
                    data.note,
                ),
            )

            log = cur.fetchone()

        conn.commit()

    return {
        "id": log[0],
        "ticket_id": log[1],
        "technician_id": log[2],
        "note": log[3],
        "created_at": log[4],
    }
