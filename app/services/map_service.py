from collections import defaultdict
from sqlalchemy.orm import Session

from app.models import StaticRoute, StaticTrip, StaticShape, StaticStop


def get_route_map_data(db: Session, route_id: str) -> dict | None:
    print("Getting route map data for route id:", route_id)