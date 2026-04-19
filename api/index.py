import sys
import os
from urllib.parse import parse_qs

# Add the backend directory to the sys.path so imports work
backend_path = os.path.join(os.path.dirname(__file__), '../movie-recommender-backend')
sys.path.append(backend_path)

from main import app as _app

_app.root_path = "/api"

async def app(scope, receive, send):
    """
    Vercel rewrites `/api/<path>` to `/api/index.py` and (optionally) forwards the
    original path via the `path` query param. Preserve that original path so
    FastAPI can route correctly.
    """
    if scope.get("type") in {"http", "websocket"}:
        query_string = (scope.get("query_string") or b"").decode("utf-8", errors="ignore")
        query_params = parse_qs(query_string)
        forwarded_path = query_params.get("path", [None])[0]
        if forwarded_path and isinstance(forwarded_path, str) and forwarded_path.startswith("/"):
            scope = dict(scope)
            scope["path"] = forwarded_path

    await _app(scope, receive, send)
