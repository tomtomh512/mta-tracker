from sqlalchemy.orm import Session
from google.transit import gtfs_realtime_pb2
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from collections import defaultdict
NY_TZ = ZoneInfo("America/New_York")

from app.models import StaticRoute, StaticShape, StaticStop, StaticTrip, StopTimeUpdate, RealtimeTrip

def format_time(ts: int | None) -> str:
    dt = datetime.fromtimestamp(ts, tz=NY_TZ)
    return dt.strftime("%Y-%m-%d %I:%M:%S %p")

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

def test_realtime(db: Session):
    updates = (
        db.query(StopTimeUpdate)
        .join(RealtimeTrip)
        .filter(RealtimeTrip.route_id == "A")
        .all()
    )

    grouped = defaultdict(list)

    for stu in updates:
        grouped[stu.trip_id].append(stu)

    for trip_id, stops in grouped.items():
        print(f"\nTrip: {trip_id}")

        for stu in stops:
            print(
                f"  Stop: {stu.stop.stop_name} ({stu.stop_id}), "
                f"Arrival: {format_time(stu.arrival_time)}, "
                f"Departure: {format_time(stu.departure_time)}"
            )