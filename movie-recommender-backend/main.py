from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config.constants import SERVER_CONFIG, CORS_ORIGINS, MESSAGES

# --- FastAPI App ---
app = FastAPI(title=SERVER_CONFIG.get('title', 'Movie Recommender API'))

# --- CORS Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper to include routers safely
def include_router_safely(router, name):
    try:
        app.include_router(router)
        print(f"[ OK ] Router '{name}' loaded")
    except Exception as e:
        print(f"[ ERROR ] Failed to load router '{name}': {e}")

try:
    from routes.discovery import router as discovery_router
    app.include_router(discovery_router)
except Exception as e: print(f"[ ERROR ] Failed to import discovery: {e}")

try:
    from routes.search import router as search_router
    app.include_router(search_router)
except Exception as e: print(f"[ ERROR ] Failed to import search: {e}")

try:
    from routes.ai_chat import router as ai_chat_router
    app.include_router(ai_chat_router)
except Exception as e: print(f"[ ERROR ] Failed to import ai_chat: {e}")

try:
    from routes.user_preferences import router as user_preferences_router
    app.include_router(user_preferences_router)
except Exception as e: print(f"[ ERROR ] Failed to import user_preferences: {e}")

try:
    from routes.analytics import router as analytics_router
    app.include_router(analytics_router)
except Exception as e: print(f"[ ERROR ] Failed to import analytics: {e}")

try:
    from routes.cron import router as cron_router
    app.include_router(cron_router)
except Exception as e: print(f"[ ERROR ] Failed to import cron: {e}")

try:
    from routes.details import router as details_router
    app.include_router(details_router)
except Exception as e: print(f"[ ERROR ] Failed to import details: {e}")

# --- Health Endpoints ---
@app.get("/")
async def root():
    return {"message": MESSAGES['API_RUNNING'], "status": "active"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": MESSAGES['HEALTH_OK']}

if __name__ == "__main__":
    uvicorn.run(
        app, 
        host=SERVER_CONFIG.get('host', '127.0.0.1'),
        port=SERVER_CONFIG.get('port', 8000),
        reload=SERVER_CONFIG.get('reload', True)
    )
