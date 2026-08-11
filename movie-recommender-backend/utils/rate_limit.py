"""Small process-local limiter; use an edge/API gateway limiter for multi-instance scale."""
import time
from collections import defaultdict, deque
from fastapi import HTTPException, Request

_events = defaultdict(deque)


def enforce_rate_limit(request: Request, limit: int = 60, window_seconds: int = 60) -> None:
    key = request.client.host if request.client else "unknown"
    now = time.monotonic()
    events = _events[key]
    while events and events[0] <= now - window_seconds:
        events.popleft()
    if len(events) >= limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    events.append(now)
