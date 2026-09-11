import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    JWT_SECRET = os.getenv("JWT_SECRET")

    FRONTEND_ORIGINS = [
        origin.strip()
        for origin in os.getenv(
            "FRONTEND_ORIGINS",
            ""
        ).split(",")
        if origin.strip()
    ]


settings = Settings()


if not settings.JWT_SECRET:
    raise RuntimeError("JWT_SECRET is not configured")