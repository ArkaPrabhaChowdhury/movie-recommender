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

# Import and include routers AFTER app creation
try:
    from routes.discovery import router as discovery_router
    from routes.search import router as search_router
    from routes.ai_chat import router as ai_chat_router
    from routes.user_preferences import router as user_preferences_router  # NEW
    
    app.include_router(discovery_router)
    app.include_router(search_router)
    app.include_router(ai_chat_router)
    app.include_router(user_preferences_router)  # NEW
    
    print("✅ All routes loaded successfully")
    print("  - Discovery routes: /discover")
    print("  - Search routes: /search")
    print("  - AI Chat routes: /ai-chat")
    print("  - User Preference routes: /user/*")  # NEW
except ImportError as e:
    print(f"❌ Error importing routes: {e}")

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
