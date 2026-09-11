from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_technician
from app.database import get_connection
from app.models import CreateLogRequest


router = APIRouter()


@router.post("/logs")
def create_log(
    data: CreateLogRequest,
    technician_id: str = Depends(get_current_technician),
):

    with get_connection() as conn:
        with conn.cursor() as cur:

            # Make sure this ticket belongs to the
            # authenticated technician.
            cur.execute(
                """
                SELECT id
                FROM tickets
                WHERE id = %s
                  AND technician_id = %s
                """,
                (
                    str(data.ticket_id),
                    technician_id,
                ),
            )

            ticket = cur.fetchone()

            if not ticket:
                raise HTTPException(
                    status_code=404,
                    detail="Ticket not found"
                )

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
                    str(data.ticket_id),
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