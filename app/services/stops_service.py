from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models import StopTimeUpdate, RealtimeTrip, StaticRoute, StaticTrip, StaticStopTime, StaticStop
from app.utils import utils


def get_parent_stops(db: Session):
    return (
        db.query(StaticStop)
        .filter(StaticStop.location_type == 1)
        .all()
    )

def get_parent_stop(db: Session, stop_id: str):
    return utils.get_parent_stop(db, stop_id)

def get_routes_for_stop(db: Session, stop_id: str):
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

    trip_ids = list({u.trip_id for u in updates})
    trips = (
        db.query(StaticTrip)
        .filter(StaticTrip.trip_id.in_(trip_ids))
        .all()
    )

    trip_map = {t.trip_id: t for t in trips}

    now = datetime.now(timezone.utc).timestamp()

    upcoming = [u for u in updates if u.arrival_time and u.arrival_time >= now]
    upcoming.sort(key=lambda x: x.arrival_time)

    results = []

    for u in upcoming[:num]:
        is_transfer = u.stop_id not in stop_ids

        trip = trip_map.get(u.trip_id)

        results.append({
            "route": u.trip.route_id if u.trip else None,
            "to": trip.trip_headsign if trip else "Unknown",
            "direction_id": trip.direction_id if trip else None,
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

def get_nearby_stops(db: Session, lat: float, lng: float, radius: int, limit: int):
    return 0