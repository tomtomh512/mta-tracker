from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.services import map_service

router = APIRouter(prefix="/map", tags=["map"])


@router.get("/{route_id}")
def get_route_map(route_id: str, db: Session = Depends(get_db)):
    return map_service.get_route_map_data(db, route_id)