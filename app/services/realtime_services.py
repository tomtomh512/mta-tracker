from sqlalchemy.orm import Session
from google.transit import gtfs_realtime_pb2
from app.models import RealtimeTrip, StopTimeUpdate, StaticTrip, StaticStop, StaticRoute
from datetime import datetime, timezone
import requests

FEEDS = {
    "ACE": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace",
    "BDFM": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm",
    "G": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-g",
    "JZ": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-jz",
    "NQRW": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw",
    "L": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-l",
    "FULL": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
    "SI": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-si",
}

def fetch_feed(url: str) -> gtfs_realtime_pb2.FeedMessage | None:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)
        return feed
    except Exception as e:
        print(f"Failed to fetch feed {url}: {e}")
        return None

def match_static_trip(trip_id_from_url: str, valid_trip_ids: set[str]) -> str | None:
    for valid_id in valid_trip_ids:
        if trip_id_from_url in valid_id:
            return valid_id
    return None

def populate_trips(db: Session):
    print("Populating trips")

    valid_trip_ids = {row.trip_id for row in db.query(StaticTrip.trip_id).all()}
    valid_route_ids = {row.route_id for row in db.query(StaticRoute.route_id).all()}
    valid_stop_ids = {row.stop_id for row in db.query(StaticStop.stop_id).all()}
    now = datetime.now(timezone.utc)

    for feed_key, url in FEEDS.items():
        feed = fetch_feed(url)
        if not feed:
            continue

        for entity in feed.entity:
            if not entity.HasField("trip_update"):
                continue

            tu = entity.trip_update
            trip = tu.trip

            trip_id_from_URL = trip.trip_id
            route_id = trip.route_id

            # validate route_id first
            if route_id not in valid_route_ids:
                print(f"Skipping unknown route_id: {route_id}")
                continue

            # validate trip_id
            trip_id = match_static_trip(trip_id_from_URL, valid_trip_ids)
            if not trip_id:
                print(f"Skipping unknown trip_id: {trip_id_from_URL}")
                continue

            realtime_trip = db.get(RealtimeTrip, trip_id)
            if realtime_trip is None:
                realtime_trip = RealtimeTrip(
                    trip_id=trip_id,
                    route_id=trip.route_id,
                    direction_id=trip.direction_id or None,
                    start_time=trip.start_time or None,
                    start_date=trip.start_date or None,
                    last_updated=now,
                )
                db.add(realtime_trip)
            else:
                realtime_trip.route_id = trip.route_id
                realtime_trip.direction_id = trip.direction_id or None
                realtime_trip.start_time = trip.start_time or None
                realtime_trip.start_date = trip.start_date or None
                realtime_trip.last_updated = now


            existing_updates = {
                stu.stop_id: stu
                for stu in db.query(StopTimeUpdate)
                .filter(StopTimeUpdate.trip_id == trip_id)
                .all()
            }

            for stu in tu.stop_time_update:
                if stu.stop_id not in valid_stop_ids:
                    print(f"Skipping unknown stop_id: {stu.stop_id}")
                    continue

                arrival_time = stu.arrival.time if stu.HasField("arrival") else None
                departure_time = stu.departure.time if stu.HasField("departure") else None

                if stu.stop_id in existing_updates:
                    existing = existing_updates[stu.stop_id]
                    existing.arrival_time = arrival_time
                    existing.departure_time = departure_time
                    existing.last_updated = now
                else:
                    db.add(StopTimeUpdate(
                        trip_id=trip_id,
                        stop_id=stu.stop_id,
                        arrival_time=arrival_time,
                        departure_time=departure_time,
                        last_updated=now,
                    ))

    db.commit()
    print("Trips populated")

def cleanup_trips(db: Session):
    print("Cleanup trips")