from fastapi import APIRouter, HTTPException, Header, Depends
from services.cron_service import CronService
import os
import time

router = APIRouter(prefix="/cron", tags=["cron"])
cron_service = CronService()
_replayed_runs = {}

def verify_cron_secret(authorization: str = Header(None)):
    """Simple check for Vercel Cron secret"""
    expected_secret = os.getenv('CRON_SECRET')
    if not expected_secret and os.getenv("ALLOW_UNAUTHENTICATED_CRON", "false").lower() != "true":
        raise HTTPException(status_code=503, detail="CRON_SECRET is required")
        
    if authorization != f"Bearer {expected_secret}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True


def reject_replay(run_id: str = Header(None, alias="X-Cron-Run-Id")):
    if not run_id:
        return True
    now = time.time()
    _replayed_runs.update({key: value for key, value in _replayed_runs.items() if value > now})
    if run_id in _replayed_runs:
        raise HTTPException(status_code=409, detail="Cron run already processed")
    _replayed_runs[run_id] = now + 3600
    return True

@router.get("/weekly-recommendations")
async def trigger_weekly_recommendations(authorized: bool = Depends(verify_cron_secret), replay_safe: bool = Depends(reject_replay)):
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

@router.get("/watching-notifications")
async def trigger_watching_notifications(authorized: bool = Depends(verify_cron_secret), replay_safe: bool = Depends(reject_replay)):
    """Check TMDB daily and notify users when a watched show's episode airs."""
    try:
        return {"status": "completed", "results": await cron_service.run_watching_notifications()}
    except Exception as e:
        print(f"Watching notification cron failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
