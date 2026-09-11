from app.auth import hash_password
from app.database import get_connection


email = "srestho@pixelit.com"
name = "Srestho"
password = "test-password"


password_hash = hash_password(password)


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
            RETURNING id
            """,
            (
                email,
                name,
                password_hash
            )
        )

        technician_id = cur.fetchone()[0]

    conn.commit()


print("Technician created!")
print("ID:", technician_id)