from fastapi import APIRouter
from database import get_recent_events

router = APIRouter(prefix="/api")


@router.get("/events")
def get_events(limit: int = 20):
    # returns recent threshold breach events for the event log
    return get_recent_events(limit)
