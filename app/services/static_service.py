from sqlalchemy.orm import Session
import requests, zipfile, io

from app.models import (
    StaticRoute,
    StaticShape,
    StaticStop,
    StaticTrip,
    StaticTransfer,
    RealtimeTrip,
    StopTimeUpdate,
    StaticStopTime,
)
from app.services import realtime_service
from app.utils import static_utils
from app.cache import delete_pattern

STATIC_GTFS_URL = "https://rrgtfsfeeds.s3.amazonaws.com/gtfs_subway.zip"
CHUNK_SIZE = 5000
STOP_TIMES_CHUNK_SIZE = 10000

def populate_static_gtfs(db: Session):
    populated = {
        "routes": db.query(StaticRoute).count() > 0,
        "stops": db.query(StaticStop).count() > 0,
        "trips": db.query(StaticTrip).count() > 0,
        "stop_times": db.query(StaticStopTime).count() > 0,
        "shapes": db.query(StaticShape).count() > 0,
        "transfers": db.query(StaticTransfer).count() > 0,
    }

    if all(populated.values()):
        print("Static GTFS tables already populated, skipping...")
        return

    print("Fetching static GTFS data...")
    r = requests.get(STATIC_GTFS_URL)
    r.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(r.content))

    if not populated["routes"]:
        populate_routes(db, z)
    if not populated["stops"]:
        populate_stops(db, z)
    if not populated["transfers"]:
        populate_transfers(db, z)
    if not populated["trips"]:
        populate_trips(db, z)

    populate_stop_times(db, z)

    if not populated["shapes"]:
        populate_shapes(db, z)

    db.commit()
    print("Fetching static GTFS data finished")

def update_static_gtfs(db: Session):
    print("Updating static GTFS data...")
    r = requests.get(STATIC_GTFS_URL)
    r.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(r.content))

    for model in [
        StopTimeUpdate,
        StaticStopTime,
        RealtimeTrip,
        StaticShape,
        StaticTrip,
        StaticTransfer,
        StaticStop,
        StaticRoute,
    ]:
        deleted = db.query(model).delete()
        print(f"Deleted {deleted} rows from {model.__tablename__}")

    db.flush()

    populate_routes(db, z)
    populate_stops(db, z)
    populate_transfers(db, z)
    populate_trips(db, z)
    populate_stop_times(db, z)
    populate_shapes(db, z)

    realtime_service.populate_trips(db)

    db.commit()

    for pattern in [
        "parent_stops",
        "parent_stop:*"
        "routes_for_stop:*",
        "wait_times:*",

        "routes",
        "route:*",
        "route_stops:*",
        "active_trips:*"
    ]:
        delete_pattern(pattern)

    print("Static GTFS update finished")

def populate_routes(db: Session, z: zipfile.ZipFile):
    rows = static_utils.read_csv_from_zip(z, "routes.txt")
    db.bulk_save_objects([
        StaticRoute(
            route_id=r["route_id"],
            agency_id=r["agency_id"],
            route_short_name=r["route_short_name"],
            route_long_name=r["route_long_name"],
            route_desc=r.get("route_desc"),
            route_type=int(r["route_type"]),
            route_url=r.get("route_url"),
            route_color=r.get("route_color"),
            route_text_color=r.get("route_text_color"),
            route_sort_order=int(r["route_sort_order"]) if r.get("route_sort_order") else None,
        )
        for r in rows
    ])
    print(f"Inserted {len(rows)} routes")

def populate_stops(db: Session, z: zipfile.ZipFile):
    rows = static_utils.read_csv_from_zip(z, "stops.txt")
    db.bulk_save_objects([
        StaticStop(
            stop_id=r["stop_id"],
            stop_name=r["stop_name"],
            stop_lat=float(r["stop_lat"]),
            stop_lon=float(r["stop_lon"]),
            location_type=int(r["location_type"]) if r.get("location_type") else None,
            parent_station=r.get("parent_station") or None,
        )
        for r in rows
    ])
    print(f"Inserted {len(rows)} stops")

def populate_trips(db: Session, z: zipfile.ZipFile):
    rows = static_utils.read_csv_from_zip(z, "trips.txt")
    db.bulk_save_objects([
        StaticTrip(
            trip_id=r["trip_id"],
            route_id=r["route_id"],
            service_id=r["service_id"],
            shape_id=r["shape_id"],
            trip_headsign=r.get("trip_headsign"),
            direction_id=int(r["direction_id"]) if r.get("direction_id") else None,
        )
        for r in rows
    ])
    print(f"Inserted {len(rows)} trips")


def populate_stop_times(db: Session, z: zipfile.ZipFile):
    rows = static_utils.read_csv_from_zip(z, "stop_times.txt")

    total = len(rows)

    for i in range(0, total, STOP_TIMES_CHUNK_SIZE):
        chunk = rows[i:i + STOP_TIMES_CHUNK_SIZE]

        db.bulk_save_objects([
            StaticStopTime(
                trip_id=r["trip_id"],
                stop_id=r["stop_id"],
                arrival_time=r.get("arrival_time"),
                departure_time=r.get("departure_time"),
                stop_sequence=int(r["stop_sequence"]),
            )
            for r in chunk
        ])

        db.flush()

    print(f"Inserted {total} stop times")

def populate_shapes(db: Session, z: zipfile.ZipFile):
    rows = static_utils.read_csv_from_zip(z, "shapes.txt")
    for i in range(0, len(rows), CHUNK_SIZE):
        chunk = rows[i:i + CHUNK_SIZE]
        db.bulk_save_objects([
            StaticShape(
                shape_id=r["shape_id"],
                shape_pt_lat=float(r["shape_pt_lat"]),
                shape_pt_lon=float(r["shape_pt_lon"]),
                shape_pt_sequence=int(r["shape_pt_sequence"]),
                shape_dist_traveled=float(r["shape_dist_traveled"]) if r.get("shape_dist_traveled") else None,
            )
            for r in chunk
        ])
        db.flush()
    print(f"Inserted {len(rows)} shape points")

def populate_transfers(db: Session, z: zipfile.ZipFile):
    try:
        rows = static_utils.read_csv_from_zip(z, "transfers.txt")
    except KeyError:
        print("No transfers.txt found, skipping...")
        return

    db.bulk_save_objects([
        StaticTransfer(
            from_stop_id=r["from_stop_id"],
            to_stop_id=r["to_stop_id"],
            transfer_type=int(r["transfer_type"]) if r.get("transfer_type") else 0,
            min_transfer_time=int(r["min_transfer_time"]) if r.get("min_transfer_time") else None,
        )
        for r in rows
    ])

    print(f"Inserted {len(rows)} transfers")