from app.auth import hash_password
from app.database import get_connection


email = "tech@example.com"
name = "Test Technician"
password_hash = hash_password("test-password")


with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO technicians (
                email,
                name,
                password_hash
            )
            VALUES (%s, %s, %s)
            """,
            (
                email,
                name,
                password_hash,
            ),
        )

    conn.commit()