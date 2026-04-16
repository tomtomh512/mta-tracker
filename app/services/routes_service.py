from sqlalchemy.orm import Session
from collections import defaultdict

from app.models import StopTimeUpdate, RealtimeTrip, StaticRoute, StaticStopTime, StaticTrip, StaticStop
from app.utils import utils


def get_routes(db: Session):
    return db.query(StaticRoute).all()

def get_route(db: Session, route_id: str):
    route = (
        db.query(StaticRoute)
        .filter(StaticRoute.route_id == route_id)
        .first()
    )

    return route

def get_route_stops(db: Session, route_id: str):
    # verify route exists
    route = (
        db.query(StaticRoute)
        .filter(StaticRoute.route_id == route_id)
        .first()
    )

    if not route:
        return None

    # get all stops served by any trip on this route
    stops = (
        db.query(StaticStop)
        .join(StaticStopTime, StaticStopTime.stop_id == StaticStop.stop_id)
        .join(StaticTrip, StaticTrip.trip_id == StaticStopTime.trip_id)
        .filter(StaticTrip.route_id == route_id)
        .distinct()
        .all()
    )

    return {
        "route_id": route_id,
        "stops": stops
    }

def get_active_trips(db: Session, route_id: str):
    updates = (
        db.query(StopTimeUpdate)
        .join(RealtimeTrip)
        .filter(RealtimeTrip.route_id == route_id)
        .all()
    )

    grouped = defaultdict(list)

    for stu in updates:
        grouped[stu.trip_id].append(stu)

    results = []

    for trip_id, stops in grouped.items():
        trip = db.query(StaticTrip).filter(StaticTrip.trip_id == trip_id).first()

        stop_data = []
        for stu in stops:
            stop_data.append({
                "stop_id": stu.stop_id,
                "stop_name": stu.stop.stop_name if stu.stop else None,
                "arrival_time": utils.format_time(stu.arrival_time),
                "departure_time": utils.format_time(stu.departure_time),
                "arrival_timestamp": stu.arrival_time,
                "departure_timestamp": stu.departure_time,
            })

        results.append({
            "trip_id": trip_id,
            "to": trip.trip_headsign if trip else "Unknown",
            "direction_id": trip.direction_id if trip else None,
            "stops": stop_data,
        })

    return {
        "route_id": route_id,
        "trips": results,
    }