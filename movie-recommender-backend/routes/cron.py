from fastapi import APIRouter, HTTPException, Header, Depends
from services.cron_service import CronService
import os

router = APIRouter(prefix="/cron", tags=["cron"])
cron_service = CronService()

def verify_cron_secret(authorization: str = Header(None)):
    """Simple check for Vercel Cron secret"""
    expected_secret = os.getenv('CRON_SECRET')
    if not expected_secret:
        # If not set, we allow for now but log warning
        print("⚠️ CRON_SECRET not set in environment!")
        return True
        
    if authorization != f"Bearer {expected_secret}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True

@router.get("/weekly-recommendations")
async def trigger_weekly_recommendations(authorized: bool = Depends(verify_cron_secret)):
    """
    Endpoint intended to be called by Vercel Cron weekly.
    It generates and sends recommendation emails to all users.
    """
    try:
        results = await cron_service.run_weekly_recommendations()
        return {
            "status": "completed",
            "results": results
        }
    except Exception as e:
        print(f"❌ Cron execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
