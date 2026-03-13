import os
import sys
from dotenv import load_dotenv

# Try to find .env relative to this script
backend_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(backend_dir, '.env')

print(f"Checking for .env at: {env_path}")
print(f"Exists: {os.path.exists(env_path)}")

load_dotenv(env_path)

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')

print(f"SUPABASE_URL: {url}")
print(f"SUPABASE_KEY length: {len(key) if key else 0}")
