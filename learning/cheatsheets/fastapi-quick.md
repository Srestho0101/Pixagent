# Cheatsheet — FastAPI Patterns in This Repo

## App Assembly
```python
app = FastAPI(...)
app.add_middleware(CORSMiddleware, allow_origins=settings.FRONTEND_ORIGINS, ...)
app.include_router(router, prefix="/api")
```

## Dependency Auth
```python
technician_id: str = Depends(get_current_technician)
```

## Route Skeleton
```python
@router.post("/path", response_model=SomeModel)
def handler(data: RequestModel, technician_id: str = Depends(...)):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("... %s ...", (val,))
            row = cur.fetchone()
        conn.commit()
    return {...}
```

## Streaming
```python
return StreamingResponse(
    generator(),
    media_type="text/event-stream",
    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
)
```

## Settings
```python
from app.config import settings
# settings.MISTRAL_API_KEY, settings.JWT_SECRET, settings.FRONTEND_ORIGINS
```

## Common Headers / Status
- 401 → invalid / expired JWT
- 404 → ticket or log not found (or not owned)
- 422 → Pydantic validation failure
