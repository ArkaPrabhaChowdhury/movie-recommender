import uvicorn
import os

if __name__ == "__main__":
    print("🚀 Starting Movie Recommender Backend...")
    print("📍 API will be available at: http://127.0.0.1:8000")
    print("📖 API docs will be available at: http://127.0.0.1:8000/docs")
    print("🏠 Root endpoint: http://127.0.0.1:8000")
    print("❤️  Health check: http://127.0.0.1:8000/health")
    
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
