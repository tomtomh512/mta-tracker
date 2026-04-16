from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.services import stops_service

router = APIRouter(prefix="/stops", tags=["stops"])


@router.get("/{stop_id}")
def get_wait_times(stop_id: str, route_id: str | None = None, db: Session = Depends(get_db)):
    if route_id:
        return stops_service.get_wait_times(db, stop_id, 5, route_id)

    return stops_service.get_wait_times(db, stop_id, 5)


@router.get("/{stop_id}/routes")
def get_routes_for_stop(stop_id: str, db: Session = Depends(get_db)):
    return stops_service.get_routes_by_stop(db, stop_id)


@router.get("/")
def get_all_stops(db: Session = Depends(get_db)):
    return stops_service.get_parent_stops(db)