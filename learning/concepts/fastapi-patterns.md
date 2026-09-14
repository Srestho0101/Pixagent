# FastAPI Patterns Used in Pixagent

These are the patterns you will copy into almost every future Python API.

## 1. Composition Root (`app/main.py`)

```python
app = FastAPI(title=..., version=...)
app.add_middleware(CORSMiddleware, ...)
app.include_router(auth.router, prefix="/api")
app.include_router(tickets.router, prefix="/api")
# ...
@app.get("/health")
def health(): ...
```

Everything is assembled in one place. Routers stay independent.

## 2. Settings Object (`app/config.py`)

```python
class Settings:
    JWT_SECRET = os.getenv("JWT_SECRET")
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
    ...
settings = Settings()
if not settings.JWT_SECRET:
    raise RuntimeError(...)
```

- Fail fast on missing critical config.
- One import (`from app.config import settings`) everywhere.
- Easy to later swap for Pydantic Settings or a secret manager.

## 3. Dependency Injection for Auth

```python
def get_current_technician(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    ...
```

Any route that needs a logged-in technician simply declares:

```python
def create_ticket(..., technician_id: str = Depends(get_current_technician)):
```

FastAPI injects the value. No global state, easy to test, easy to mock.

## 4. Pydantic Models as Contracts (`app/models.py`)

- Request models → automatic validation + OpenAPI docs.
- Response models → consistent JSON shape.
- `Literal` for enums, `Field(min_length=...)` for constraints.
- Prefer models over raw `dict` returns.

## 5. Thin Route Handlers

Typical shape:

```python
@router.post("/tickets", response_model=TicketResponse)
def create_ticket(data: CreateTicketRequest, technician_id: str = Depends(...)):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT ... RETURNING ...", (...))
            ticket = cur.fetchone()
        conn.commit()
    return {...}
```

- Validation is already done by Pydantic.
- Authorization is already done by the dependency.
- The handler only orchestrates DB work and shapes the response.

## 6. Streaming Responses

```python
return StreamingResponse(
    chat_stream(...),
    media_type="text/event-stream",
    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
)
```

`chat_stream` is a generator that yields SSE lines.  
This is the standard way to stream LLM tokens with FastAPI.

## 7. Database Access Pattern

```python
with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute(...)
        ...
    conn.commit()   # only for writes
```

Simple, explicit, no hidden magic. Later you can replace `get_connection` with a pool without touching every route.

## Common Pitfalls (and how Pixagent avoids them)

| Pitfall | How this project handles it |
|---------|-----------------------------|
| Forgetting `commit()` | Explicit `conn.commit()` after every write |
| SQL injection | Always parameterized (`%s`) |
| Leaking other users’ data | Ownership check in every mutating query |
| CORS hell | Central `FRONTEND_ORIGINS` list |
| Missing secret | Fail at import time |

---

**Practice**: Open `app/routes/tickets.py` and `app/routes/logs.py`. Notice how almost identical the ownership-check + execute + commit pattern is. That repetition is intentional and easy to extract later if needed.
