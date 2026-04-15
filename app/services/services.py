from sqlalchemy.orm import Session
from google.transit import gtfs_realtime_pb2
import requests
from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

NY_TZ = ZoneInfo("America/New_York")

from app.models import StaticRoute, StaticShape, StaticStop, StaticTrip, StopTimeUpdate, RealtimeTrip

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
    trip_count = db.query(StaticTrip).count()
    shape_count = db.query(StaticShape).count()

    print(f"Routes:         {route_count}")
    print(f"Stops:          {stop_count}")
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

def get_next_trains_at_station(db: Session, stop_id: str):
    updates = (
        db.query(StopTimeUpdate)
        .join(RealtimeTrip)
        .filter(StopTimeUpdate.stop_id == stop_id)
        .all()
    )

    now = datetime.now(timezone.utc).timestamp()

    # keep only future arrivals
    upcoming = [
        u for u in updates
        if u.arrival_time and u.arrival_time >= now
    ]

    # sort by arrival time
    upcoming.sort(key=lambda x: x.arrival_time)

    print(f"\nNext trains at {stop_id}\n")

    for u in upcoming[:5]:
        print(
            f"Route: {u.trip.route_id} | "
            f"Arrival: {format_time(u.arrival_time)}"
        )