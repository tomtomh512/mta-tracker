from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.services import trips_service

router = APIRouter(prefix="/trips", tags=["trips"])


@router.get("/routes/{route_id}")
def get_trips(route_id: str, db: Session = Depends(get_db)):
    return trips_service.get_active_trips_by_route(db, route_id)