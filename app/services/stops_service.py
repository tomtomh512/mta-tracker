from sqlalchemy.orm import Session
from sqlalchemy import func, Float
from datetime import datetime, timezone

from app.models import StopTimeUpdate, RealtimeTrip, StaticRoute, StaticTrip, StaticStopTime, StaticStop
from app.utils import utils
from app.cache import get_cached, set_cached

import math

def get_parent_stops(db: Session):
    cache_key = "parent_stops"
    cached = get_cached(cache_key)
    if cached:
        return cached

    stops = (
        db.query(StaticStop)
        .filter(StaticStop.location_type == 1)
        .all()
    )

    result = []

    for stop in stops:
        result.append({
            "stop_name": stop.stop_name,
            "stop_lon": stop.stop_lon,
            "stop_id": stop.stop_id,
            "stop_lat": stop.stop_lat,
            "location_type": stop.location_type,
        })

    set_cached(cache_key, result, ttl=86400)
    return result

def get_parent_stop(db: Session, stop_id: str):
    cache_key = f"parent_stop:{stop_id}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    stop = utils.get_parent_stop(db, stop_id)

    result = {
        "stop_name": stop.stop_name,
        "stop_lon": stop.stop_lon,
        "stop_id": stop.stop_id,
        "stop_lat": stop.stop_lat,
        "location_type": stop.location_type,
    }

    set_cached(cache_key, result, ttl=86400)
    return result

def get_routes_for_stop(db: Session, stop_id: str):
    cache_key = f"routes_for_stop:{stop_id}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    parent_stop_id, stop_ids, all_stop_ids = utils.get_all_stop_ids(db, stop_id)

    routes = (
        db.query(StaticRoute)
        .join(StaticTrip, StaticTrip.route_id == StaticRoute.route_id)
        .join(StaticStopTime, StaticStopTime.trip_id == StaticTrip.trip_id)
        .filter(StaticStopTime.stop_id.in_(all_stop_ids))
        .distinct(StaticRoute.route_id)
        .all()
    )

    result = []

    for route in routes:
        result.append({
            "route_long_name": route.route_long_name,
            "route_type": route.route_type,
            "route_sort_order": route.route_sort_order,
            "route_id": route.route_id,
            "agency_id": route.agency_id,
            "route_short_name": route.route_short_name,
            "route_desc": route.route_desc,
            "route_url": route.route_url,
        })

    set_cached(cache_key, result, ttl=86400)  # 24h
    return result

def get_wait_times(
    db: Session,
    stop_id: str,
    num: int = 5,
    route_id: str | None = None,
):
    cache_key = f"wait_times:{stop_id}:{route_id}"
    cached = get_cached(cache_key)
    if cached:
        return cached

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

    result = {
        "stop_id": parent_stop_id,
        "route_id": route_id,
        "results": results,
    }

    set_cached(cache_key, result, ttl=20)
    return result


def get_nearby_stops(
        db: Session,
        lat: float,
        lng: float,
        radius: int,
        limit: int
):
    # Round to 2 decimal places (~1.1km grid) so nearby coordinates share cache hits
    cache_key = f"nearby_stops:{round(lat, 2)}:{round(lng, 2)}:{radius}:{limit}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    # Bounding box pre-filter to avoid a full table scan.
    # 1 degree of latitude ~ 111,320m; longitude shrinks by cos(lat).
    lat_delta = radius / 111_320.0
    lng_delta = radius / (111_320.0 * math.cos(math.radians(lat)))

    # Haversine via SQL so sorting and filtering happen in the DB.
    # Using the standard spherical law-of-cosines approximation expressed
    R = 6_371_000  # Earth radius in metres

    lat_r = math.radians(lat)
    lng_r = math.radians(lng)

    # SQLAlchemy expression for haversine distance in metres
    stop_lat_r = func.radians(StaticStop.stop_lat.cast(Float))
    stop_lng_r = func.radians(StaticStop.stop_lon.cast(Float))

    dlat = stop_lat_r - lat_r
    dlng = stop_lng_r - lng_r

    a = func.pow(func.sin(dlat / 2), 2) + math.cos(lat_r) * func.cos(stop_lat_r) * func.pow(func.sin(dlng / 2), 2)
    distance_m = 2 * R * func.asin(func.sqrt(a))

    stops = (
        db.query(StaticStop, distance_m.label("distance_m"))
        .filter(
            StaticStop.location_type == 1,  # parent stations only
            StaticStop.stop_lat.between(lat - lat_delta, lat + lat_delta),
            StaticStop.stop_lon.between(lng - lng_delta, lng + lng_delta),
            distance_m <= radius,
        )
        .order_by("distance_m")
        .limit(limit)
        .all()
    )

    result = [
        {
            "stop_id": stop.stop_id,
            "stop_name": stop.stop_name,
            "stop_lat": stop.stop_lat,
            "stop_lon": stop.stop_lon,
            "location_type": stop.location_type,
            "distance_m": round(distance_m),
        }
        for stop, distance_m in stops
    ]

    set_cached(cache_key, result, ttl=86400)
    return result