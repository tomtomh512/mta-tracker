from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.services import routes_service
import app.schemas as schemas

router = APIRouter(prefix="/routes", tags=["routes"])


@router.get("/", response_model=list[schemas.Route])
def get_routes(db: Session = Depends(get_db)):
    return routes_service.get_routes(db)

@router.get("/{route_id}", response_model=schemas.Route)
def get_route(route_id: str, db: Session = Depends(get_db)):
    return routes_service.get_route(db, route_id)

@router.get("/{route_id}/stops", response_model=schemas.RouteStops)
def get_stops(route_id: str, db: Session = Depends(get_db)):
    return routes_service.get_route_stops(db, route_id)

@router.get("/{route_id}/trips", response_model=schemas.ActiveTrips)
def get_trips(route_id: str, db: Session = Depends(get_db)):
    return routes_service.get_active_trips(db, route_id)