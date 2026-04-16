from sqlalchemy.orm import Session
from collections import defaultdict

from app.models import StopTimeUpdate, RealtimeTrip
from app.utils import utils


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
        terminal_stop = utils.get_last_stop_for_trip(db, trip_id)
        terminal_name = terminal_stop.stop_name if terminal_stop else "Unknown"

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
            "to": terminal_name,
            "stops": stop_data,
        })

    return {
        "route_id": route_id,
        "trips": results,
    }