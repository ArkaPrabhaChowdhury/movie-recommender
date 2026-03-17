from fastapi import APIRouter
from utils.analytics_tracker import tracker

router = APIRouter()

@router.get("/analytics/summary")
async def get_analytics_summary():
    """
    Returns the real aggregated metrics from the in-memory tracker.
    Includes tokens, costs, cache hit rates, latency, and a live trace feed.
    """
    return tracker.get_summary()
