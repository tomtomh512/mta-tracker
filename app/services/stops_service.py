from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models import StopTimeUpdate, RealtimeTrip, StaticRoute, StaticTrip, StaticStopTime, StaticStop
from app.utils import utils


def get_wait_times(
    db: Session,
    stop_id: str,
    num: int = 5,
    route_id: str | None = None,
):
    parent_stop_id, stop_ids, all_stop_ids = utils.get_all_stop_ids(db, stop_id)

    query = (
        db.query(StopTimeUpdate)
        .join(RealtimeTrip)
        .filter(StopTimeUpdate.stop_id.in_(all_stop_ids))
    )

    if route_id:
        query = query.filter(RealtimeTrip.route_id == route_id)

    updates = query.all()

    now = datetime.now(timezone.utc).timestamp()

    upcoming = [u for u in updates if u.arrival_time and u.arrival_time >= now]
    upcoming.sort(key=lambda x: x.arrival_time)

    results = []

    for u in upcoming[:num]:
        is_transfer = u.stop_id not in stop_ids

        terminal_stop = utils.get_last_stop_for_trip(db, u.trip_id)
        terminal_name = terminal_stop.stop_name if terminal_stop else "Unknown"

        results.append({
            "route": u.trip.route_id,
            "to": terminal_name,
            "arrival_time": utils.format_time(u.arrival_time),
            "arrival_timestamp": u.arrival_time,
            "stop_id": u.stop_id,
            "is_transfer": is_transfer,
        })

    return {
        "stop_id": parent_stop_id,
        "route_id": route_id,
        "results": results,
    }

def get_routes_by_stop(db: Session, stop_id: str):
    parent_stop_id, stop_ids, all_stop_ids = utils.get_all_stop_ids(db, stop_id)

    routes = (
        db.query(StaticRoute)
        .join(StaticTrip, StaticTrip.route_id == StaticRoute.route_id)
        .join(StaticStopTime, StaticStopTime.trip_id == StaticTrip.trip_id)
        .filter(StaticStopTime.stop_id.in_(all_stop_ids))
        .distinct(StaticRoute.route_id)
        .all()
    )

    return routes

def get_parent_stops(db: Session):
    return (
        db.query(StaticStop)
        .filter(StaticStop.location_type == 1)
        .all()
    )

def get_stops_by_route(db: Session, route_id: str):
    print("test")

def get_nearby_stops(db: Session, lat: float, lng: float, radius: int):
    print("test")