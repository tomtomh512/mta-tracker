from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.limiter import limiter

from app.db import get_db
from app.services import routes_service
import app.schemas as schemas

router = APIRouter(prefix="/routes", tags=["routes"])


@router.get("/", response_model=list[schemas.Route])
@limiter.limit("10/minute")
def get_routes(request: Request, db: Session = Depends(get_db)):
    return routes_service.get_routes(db)

@router.get("/{route_id}", response_model=schemas.Route)
@limiter.limit("30/minute")
def get_route(request: Request, route_id: str, db: Session = Depends(get_db)):
    return routes_service.get_route(db, route_id)

@router.get("/{route_id}/stops", response_model=schemas.RouteStops)
@limiter.limit("30/minute")
def get_stops(request: Request, route_id: str, db: Session = Depends(get_db)):
    return routes_service.get_route_stops(db, route_id)

@router.get("/{route_id}/trips", response_model=schemas.ActiveTrips)
@limiter.limit("60/minute")
def get_trips(request: Request, route_id: str, db: Session = Depends(get_db)):
    return routes_service.get_active_trips(db, route_id)

@router.get("/{route_id}/map", response_model=schemas.RouteMapData)
@limiter.limit("30/minute")
def get_route_map_data(request: Request, route_id: str, db: Session = Depends(get_db)):
    return routes_service.get_route_map_data(db, route_id)