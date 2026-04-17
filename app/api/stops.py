from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from app.limiter import limiter

from app.db import get_db
from app.services import stops_service
import app.schemas as schemas

router = APIRouter(prefix="/stops", tags=["stops"])


@router.get("/", response_model=list[schemas.Stop])
@limiter.limit("10/minute")
def get_stops(request: Request, db: Session = Depends(get_db)):
    return stops_service.get_parent_stops(db)

@router.get("/{stop_id}", response_model=schemas.Stop)
@limiter.limit("30/minute")
def get_stop(request: Request, stop_id: str, db: Session = Depends(get_db)):
    return stops_service.get_parent_stop(db, stop_id)

@router.get("/{stop_id}/routes", response_model=list[schemas.Route])
@limiter.limit("30/minute")
def get_routes_for_stop(request: Request, stop_id: str, db: Session = Depends(get_db)):
    return stops_service.get_routes_for_stop(db, stop_id)

@router.get("/{stop_id}/wait", response_model=schemas.WaitTimes)
@limiter.limit("60/minute")
def get_wait_times(
        request: Request,
        stop_id: str,
        route_id: str | None = None,
        db: Session = Depends(get_db)
):
    if route_id:
        return stops_service.get_wait_times(db, stop_id, 5, route_id)

    return stops_service.get_wait_times(db, stop_id, 5)

@router.get("/nearby")
def get_nearby_stops(
    lat: float = Query(..., description="User latitude"),
    lon: float = Query(..., description="User longitude"),
    radius_m: int = Query(1000, description="Search radius in meters (default 1km)"),
    limit: int = Query(10, description="Max number of stops to return"),
    db: Session = Depends(get_db),
):
    return stops_service.get_nearby_stops(db, lat, lon, radius_m, limit)