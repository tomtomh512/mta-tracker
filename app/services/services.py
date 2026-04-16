from sqlalchemy.orm import Session
from collections import defaultdict
from datetime import datetime, timezone

from app.models import StaticRoute, StaticShape, StaticStop, StaticTrip, StaticTransfer, StopTimeUpdate, RealtimeTrip
from app.utils import utils

def test_static(db: Session):
    # temp function to test static info injection
    route_count = db.query(StaticRoute).count()
    stop_count = db.query(StaticStop).count()
    transfer_count = db.query(StaticTransfer).count()
    trip_count = db.query(StaticTrip).count()
    shape_count = db.query(StaticShape).count()

    print(f"Routes:         {route_count}")
    print(f"Stops:          {stop_count}")
    print(f"Transfer:       {transfer_count}")
    print(f"Trips:          {trip_count}")
    print(f"Shape points:   {shape_count}")

    sample_route = db.query(StaticRoute).first()
    if sample_route:
        print(f"Sample route: [{sample_route.route_id}] {sample_route.route_long_name} (#{sample_route.route_color})")

    sample_stop = db.query(StaticStop).first()
    if sample_stop:
        print(f"Sample stop:  {sample_stop.stop_name} ({sample_stop.stop_lat}, {sample_stop.stop_lon})")

def test_realtime(db: Session, route_id: str):
    updates = (
        db.query(StopTimeUpdate)
        .join(RealtimeTrip)
        .filter(RealtimeTrip.route_id == route_id)
        .all()
    )

    grouped = defaultdict(list)

    for stu in updates:
        grouped[stu.trip_id].append(stu)

    for trip_id, stops in grouped.items():
        terminal_stop = utils.get_last_stop_for_trip(db, trip_id)
        terminal_name = terminal_stop.stop_name if terminal_stop else "Unknown"
        print(f"\nTrip: {trip_id}, to {terminal_name}")

        for stu in stops:
            print(
                f"  Stop: ({stu.stop_id}) {stu.stop.stop_name}, "
                f"Arrival: {utils.format_time(stu.arrival_time)}, "
                f"Departure: {utils.format_time(stu.departure_time)}"
            )

def get_next_trains_at_station(db: Session, stop_id: str):
    stop = utils.get_parent_stop(db, stop_id)
    stop_id = stop.stop_id

    children = utils.get_children_stops(db, stop_id)
    child_ids = [s.stop_id for s in children]

    stop_ids = list(set([stop_id] + child_ids))

    transfer_stop_ids = []

    for current_stop_id in stop_ids:
        current_transfers = utils.get_transfers(db, current_stop_id, True)
        current_transfer_stop_ids = [s.stop_id for s in current_transfers]
        transfer_stop_ids.extend(current_transfer_stop_ids)

    all_stop_ids = list(set(stop_ids + transfer_stop_ids))

    updates = (
        db.query(StopTimeUpdate)
        .join(RealtimeTrip)
        .filter(StopTimeUpdate.stop_id.in_(all_stop_ids))
        .all()
    )

    now = datetime.now(timezone.utc).timestamp()

    upcoming = [u for u in updates if u.arrival_time and u.arrival_time >= now]
    upcoming.sort(key=lambda x: x.arrival_time)

    print(f"\nNext trains at {stop_id}\n")

    for u in upcoming[:5]:
        is_transfer = u.stop_id not in stop_ids
        label = f" [transfer via {u.stop_id}]" if is_transfer else ""

        terminal_stop = utils.get_last_stop_for_trip(db, u.trip_id)
        terminal_name = terminal_stop.stop_name if terminal_stop else "Unknown"

        print(
            f"Route: {u.trip.route_id} | "
            f"To: {terminal_name} | "
            f"Arrival: {utils.format_time(u.arrival_time)}"
            f"{label}"
        )