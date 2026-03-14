import sys
import os

# Add the backend directory to the sys.path so imports work
backend_path = os.path.join(os.path.dirname(__file__), '../movie-recommender-backend')
sys.path.append(backend_path)

from main import app as _app

# Export the app for Vercel
app = _app

# Fix for Vercel: FastAPI needs to know it's running behind the /api proxy
# This is required if the frontend calls /api/endpoint
app.root_path = "/api"
