from sqlalchemy.orm import Session
from collections import defaultdict

from app.models import StopTimeUpdate, RealtimeTrip, StaticRoute, StaticStopTime, StaticTrip, StaticStop, StaticShape
from app.utils import utils
from app.cache import get_cached, set_cached

def get_routes(db: Session):
    cache_key = "routes"
    cached = get_cached(cache_key)
    if cached:
        return cached

    routes = db.query(StaticRoute).all()

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

    set_cached(cache_key, result, ttl=86400)
    return result

def get_route(db: Session, route_id: str):
    cache_key = f"route:{route_id}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    route = utils.get_route_info(db, route_id)

    result = {
        "route_long_name": route.route_long_name,
        "route_type": route.route_type,
        "route_sort_order": route.route_sort_order,
        "route_id": route.route_id,
        "agency_id": route.agency_id,
        "route_short_name": route.route_short_name,
        "route_desc": route.route_desc,
        "route_url": route.route_url,
    }

    set_cached(cache_key, result, ttl=86400)
    return result

def get_route_stops(db: Session, route_id: str):
    cache_key = f"route_stops:{route_id}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    utils.get_route_info(db, route_id)

    # get all stops served by any trip on this route
    stops = (
        db.query(StaticStop)
        .join(StaticStopTime, StaticStopTime.stop_id == StaticStop.stop_id)
        .join(StaticTrip, StaticTrip.trip_id == StaticStopTime.trip_id)
        .filter(StaticTrip.route_id == route_id)
        .distinct()
        .all()
    )

    result = {
        "route_id": route_id,
        "stops": [
            {
                "stop_id": s.stop_id,
                "stop_name": s.stop_name,
                "stop_lat": s.stop_lat,
                "stop_lon": s.stop_lon,
                "location_type": s.location_type,
            }
            for s in stops
        ]
    }

    set_cached(cache_key, result, ttl=86400)
    return result

def get_active_trips(db: Session, route_id: str):
    cache_key = f"active_trips:{route_id}"
    cached = get_cached(cache_key)
    if cached:
        return cached

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

    result = {
        "route_id": route_id,
        "trips": results,
    }

    set_cached(cache_key, result, ttl=15)
    return result

def get_route_map_data(db: Session, route_id: str):
    cache_key = f"route_map:{route_id}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    route = utils.get_route_info(db, route_id)

    # get all shape_ids used by trips on this route
    shape_ids = (
        db.query(StaticTrip.shape_id)
        .filter(StaticTrip.route_id == route_id)
        .distinct()
        .all()
    )
    shape_ids = [row.shape_id for row in shape_ids]

    # fetch and group shape points by shape_id, ordered by sequence
    all_shape_points = (
        db.query(StaticShape)
        .filter(StaticShape.shape_id.in_(shape_ids))
        .order_by(StaticShape.shape_id, StaticShape.shape_pt_sequence)
        .all()
    )

    grouped: dict[str, list] = {}
    for pt in all_shape_points:
        grouped.setdefault(pt.shape_id, []).append({
            "lat": pt.shape_pt_lat,
            "lon": pt.shape_pt_lon,
        })

    shapes = list(grouped.values())

    # get all stops served by this route (parent stations only)
    stops = (
        db.query(StaticStop)
        .join(StaticStopTime, StaticStopTime.stop_id == StaticStop.stop_id)
        .join(StaticTrip, StaticTrip.trip_id == StaticStopTime.trip_id)
        .filter(StaticTrip.route_id == route_id)
        .distinct()
        .all()
    )

    stopsResult = []
    for stop in stops:
        stopsResult.append({
            "stop_id": stop.stop_id,
            "stop_name": stop.stop_name,
            "lat": stop.stop_lat,
            "lon": stop.stop_lon,
        })

    result = {
        "route_id": route.route_id,
        "route_short_name": route.route_short_name,
        "route_color": f"#{route.route_color}" if route.route_color else None,
        "route_text_color": f"#{route.route_text_color}" if route.route_text_color else None,
        "shapes": shapes,
        "stops": stopsResult
    }

    set_cached(cache_key, result, ttl=86400)
    return result