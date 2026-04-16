from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.services import routes_service

router = APIRouter(prefix="/routes", tags=["routes"])


@router.get("/")
def get_routes(db: Session = Depends(get_db)):
    return routes_service.get_routes(db)

@router.get("/{route_id}")
def get_route(route_id: str, db: Session = Depends(get_db)):
    return routes_service.get_route(db, route_id)

@router.get("/{route_id}/stops")
def get_stops(route_id: str, db: Session = Depends(get_db)):
    return routes_service.get_route_stops(db, route_id)

@router.get("/{route_id}/trips")
def get_trips(route_id: str, db: Session = Depends(get_db)):
    return routes_service.get_active_trips(db, route_id)