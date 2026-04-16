from sqlalchemy.orm import Session
from google.transit import gtfs_realtime_pb2
import requests
from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

NY_TZ = ZoneInfo("America/New_York")

from app.models import StaticRoute, StaticShape, StaticStop, StaticTrip, StaticTransfer, StopTimeUpdate, RealtimeTrip

def format_time(ts):
    if ts is None:
        return "—"

    return datetime.fromtimestamp(ts, tz=NY_TZ).strftime("%Y-%m-%d %I:%M:%S %p")

def test_trips():
    url = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace"
    response = requests.get(url)

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)

    for entity in feed.entity[:5]:
        if entity.trip_update:
            print(entity.trip_update)


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
        print(f"\nTrip: {trip_id}")

        for stu in stops:
            print(
                f"  Stop: ({stu.stop_id}) {stu.stop.stop_name}, "
                f"Arrival: {format_time(stu.arrival_time)}, "
                f"Departure: {format_time(stu.departure_time)}"
            )

# Given a stop id, return a staticstop of the stop's parent
# If the stop is a parent, return its own staticstop
def get_parent_stop(db: Session, stop_id: str):
    stop = (
        db.query(StaticStop)
        .filter(StaticStop.stop_id == stop_id)
        .first()
    )

    if stop and stop.parent_station:
        return (
            db.query(StaticStop)
            .filter(StaticStop.stop_id == stop.parent_station)
            .first()
        )

    return stop

# Given a stop id, return a list of staticstops of the stop's children
def get_children_stops(db: Session, stop_id: str):
    return (
        db.query(StaticStop)
        .filter(StaticStop.parent_station == stop_id)
        .all()
    )

# Given a stop id, return a list of staticstops of the stop's transfers
def get_transfers(db: Session, stop_id: str, includeChildren: bool):
    transfers = (
        db.query(StaticTransfer)
        .filter(StaticTransfer.from_stop_id == stop_id)
        .filter(StaticTransfer.from_stop_id != StaticTransfer.to_stop_id)
        .all()
    )

    transfer_stop_ids = {t.to_stop_id for t in transfers}

    result = []

    transfer_stops = (
        db.query(StaticStop)
        .filter(StaticStop.stop_id.in_(transfer_stop_ids))
        .all()
    )
    result.extend(transfer_stops)

    if includeChildren:
        for stop_id in transfer_stop_ids:
            result.extend(get_children_stops(db, stop_id))

    return result

def get_next_trains_at_station(db: Session, stop_id: str):
    stop = get_parent_stop(db, stop_id)
    stop_id = stop.stop_id

    children = get_children_stops(db, stop_id)
    child_ids = [s.stop_id for s in children]

    stop_ids = list(set([stop_id] + child_ids))

    transfer_stop_ids = []

    for current_stop_id in stop_ids:
        current_transfers = get_transfers(db, current_stop_id, True)
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
        print(
            f"Route: {u.trip.route_id} | "
            f"Arrival: {format_time(u.arrival_time)}"
            f"{label}"
        )