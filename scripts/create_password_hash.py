"""Print a bcrypt password hash for manually creating a FixFlow technician."""

from getpass import getpass

import bcrypt


password = getpass("Technician password: ").encode()
confirmation = getpass("Confirm password: ").encode()
if not password or password != confirmation:
    raise SystemExit("Passwords must match and cannot be empty.")

print(bcrypt.hashpw(password, bcrypt.gensalt()).decode())
