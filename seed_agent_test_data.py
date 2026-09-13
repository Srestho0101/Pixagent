"""Create a realistic repair ticket for testing the customer AI assistant.

The script is additive by default. It only deletes existing seed data when
--reset is supplied, and that deletion is limited to this script's marker and
the selected technician.

Examples:
    python seed_agent_test_data.py
    python seed_agent_test_data.py --technician-email tech@example.com
    python seed_agent_test_data.py --reset --technician-email tech@example.com
"""

import argparse
from datetime import datetime, timedelta, timezone

from app.database import get_connection


SEED_MARKER = "[AI_AGENT_TEST_DATA]"
DEFAULT_TECHNICIAN_EMAIL = "srestho@pixelit.com"
CUSTOMER_NAME = "Maya Rahman"
DEVICE_INFO = (
    "2021 Lenovo ThinkPad X1 Carbon Gen 9 — intermittent shutdowns and a swollen battery. "
    f"{SEED_MARKER}"
)


def build_logs(now: datetime) -> list[tuple[datetime, str]]:
    """Return old-to-new notes representing one repair's complete timeline."""
    entries = [
        (14 * 24, "Intake: Customer reports intermittent shutdowns when the laptop is unplugged. The issue began about two weeks ago. No liquid spill was reported."),
        (13 * 24, "Initial inspection: Bottom cover is slightly lifted near the battery compartment. Battery swelling is suspected. Device was tagged as unsafe to charge until inspection is complete."),
        (12 * 24, "Diagnostic: Battery health reads 58% with 421 reported cycles. The charger and DC-in port pass the basic electrical check."),
        (11 * 24, "Diagnostic: SSD SMART health is good and the customer files are readable. No data backup was performed by the shop; customer was advised to keep a backup."),
        (10 * 24, "Estimate prepared for battery replacement. The estimate does not include a keyboard replacement because the keyboard was working during intake testing."),
        (9 * 24, "Customer approved the battery replacement. Customer asked to keep the existing data and declined an optional shop backup service."),
        (8 * 24, "Replacement battery ordered from the supplier. Supplier quoted an estimated delivery window of 3–5 business days; this is not a guaranteed delivery date."),
        (7 * 24, "Safety step: Swollen battery was disconnected and isolated. Laptop is not being charged while waiting for the replacement part."),
        (5 * 24, "Supplier update: The first shipment was delayed and has not arrived. No pickup date can be promised yet."),
        (4 * 24, "Replacement battery received and visually matched to the device. Part label was recorded in the technician worksheet."),
        (3 * 24, "Battery replacement completed. Laptop powered on normally and passed a 30-minute charging and shutdown test."),
        (2 * 24, "Post-repair check: Customer files remain accessible and the SSD still reports healthy. No operating-system reinstall was performed."),
        (30, "Final keyboard test found an intermittent spacebar issue that was not present in the intake note. This is separate from the original battery fault."),
        (20, "Customer approved an optional keyboard assembly replacement. This additional work is not included in the original battery-only scope."),
        (12, "Keyboard assembly ordered from the supplier. The supplier has not confirmed a delivery date yet."),
        (6, "Current status: Waiting for the keyboard assembly. Battery repair is complete, but the ticket is not ready for pickup until the approved keyboard work is finished or the customer chooses to collect it as-is."),
    ]
    return [
        (now - timedelta(hours=hours_ago), note)
        for hours_ago, note in entries
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--technician-id",
        type=int,
        help="Technician ID that will own the seeded ticket.",
    )
    parser.add_argument(
        "--technician-email",
        default=DEFAULT_TECHNICIAN_EMAIL,
        help=f"Technician email to use (default: {DEFAULT_TECHNICIAN_EMAIL}).",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete this script's previous seed tickets for the selected technician first.",
    )
    return parser.parse_args()


def find_technician(cur, args: argparse.Namespace) -> int:
    if args.technician_id is not None:
        cur.execute("SELECT id FROM technicians WHERE id = %s", (args.technician_id,))
    else:
        cur.execute("SELECT id FROM technicians WHERE email = %s", (args.technician_email,))

    technician = cur.fetchone()
    if not technician:
        selector = f"ID {args.technician_id}" if args.technician_id else f"email {args.technician_email}"
        raise RuntimeError(
            f"No technician found for {selector}. Create one first or pass --technician-id."
        )
    return technician[0]


def reset_seed_data(cur, technician_id: int) -> int:
    cur.execute(
        """
        SELECT id
        FROM tickets
        WHERE technician_id = %s
          AND device_info LIKE %s
        """,
        (technician_id, f"%{SEED_MARKER}%"),
    )
    ticket_ids = [row[0] for row in cur.fetchall()]

    if ticket_ids:
        cur.execute("DELETE FROM repair_logs WHERE ticket_id = ANY(%s)", (ticket_ids,))
        cur.execute("DELETE FROM tickets WHERE id = ANY(%s)", (ticket_ids,))

    return len(ticket_ids)


def seed_ticket(cur, technician_id: int, now: datetime) -> tuple[int, int]:
    cur.execute(
        """
        INSERT INTO tickets (
            customer_name,
            device_info,
            status,
            technician_id,
            created_at
        )
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """,
        (CUSTOMER_NAME, DEVICE_INFO, "waiting_parts", technician_id, now - timedelta(hours=14 * 24)),
    )
    ticket_id = cur.fetchone()[0]

    logs = build_logs(now)
    for created_at, note in logs:
        cur.execute(
            """
            INSERT INTO repair_logs (
                ticket_id,
                technician_id,
                note,
                created_at
            )
            VALUES (%s, %s, %s, %s)
            """,
            (ticket_id, technician_id, note, created_at),
        )

    return ticket_id, len(logs)


def main() -> None:
    args = parse_args()
    now = datetime.now(timezone.utc).replace(microsecond=0)

    with get_connection() as conn:
        with conn.cursor() as cur:
            technician_id = find_technician(cur, args)
            removed = reset_seed_data(cur, technician_id) if args.reset else 0
            ticket_id, log_count = seed_ticket(cur, technician_id, now)
        conn.commit()

    print(f"Seeded ticket #{ticket_id} for {CUSTOMER_NAME}.")
    print(f"Technician ID: {technician_id}")
    print(f"Repair logs: {log_count}")
    if removed:
        print(f"Removed previous seed tickets: {removed}")
    print(f"Use ticket ID {ticket_id} in the customer lookup and AI chat.")


if __name__ == "__main__":
    main()
