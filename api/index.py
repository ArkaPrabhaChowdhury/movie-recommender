import sys
import os

# Add the backend directory to the sys.path so imports work
backend_path = os.path.join(os.path.dirname(__file__), '../movie-recommender-backend')
sys.path.append(backend_path)

from main import app
