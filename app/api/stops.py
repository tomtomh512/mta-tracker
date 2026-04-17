from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from app.limiter import limiter

from app.db import get_db
from app.services import stops_service
import app.schemas as schemas

router = APIRouter(prefix="/stops", tags=["stops"])


@router.get("/nearby", response_model=list[schemas.NearbyStop])
@limiter.limit("30/minute")
def get_nearby_stops(
    request: Request,
    lat: float,
    lon: float,
    radius_m: int,
    limit: int,
    db: Session = Depends(get_db),
):
    return stops_service.get_nearby_stops(db, lat, lon, radius_m, limit)

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