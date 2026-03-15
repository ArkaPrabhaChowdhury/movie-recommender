import os
import asyncio
from supabase import create_client, Client
from dotenv import load_dotenv

async def check_users():
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase = create_client(url, key)
    
    try:
        res = supabase.table('user_data').select('user_id, email').execute()
        print(f"Total records in user_data: {len(res.data)}")
        for i, user in enumerate(res.data):
            print(f"[{i}] ID: {user['user_id']} | Email: {user.get('email')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_users())
