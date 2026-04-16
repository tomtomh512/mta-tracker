from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models import StopTimeUpdate, RealtimeTrip
from app.utils import utils


def get_all_stop_ids(db: Session, stop_id: str):
    stop = utils.get_parent_stop(db, stop_id)
    parent_stop_id = stop.stop_id

    children = utils.get_children_stops(db, parent_stop_id)
    child_ids = [s.stop_id for s in children]

    stop_ids = list(set([parent_stop_id] + child_ids))

    transfer_stop_ids = []

    for current_stop_id in stop_ids:
        current_transfers = utils.get_transfers(db, current_stop_id, True)
        current_transfer_stop_ids = [s.stop_id for s in current_transfers]
        transfer_stop_ids.extend(current_transfer_stop_ids)

    all_stop_ids = list(set(stop_ids + transfer_stop_ids))

    return parent_stop_id, stop_ids, all_stop_ids


def get_wait_times(
    db: Session,
    stop_id: str,
    num: int = 5,
    route_id: str | None = None,
):
    parent_stop_id, stop_ids, all_stop_ids = get_all_stop_ids(db, stop_id)

    query = (
        db.query(StopTimeUpdate)
        .join(RealtimeTrip)
        .filter(StopTimeUpdate.stop_id.in_(all_stop_ids))
    )

    if route_id:
        query = query.filter(RealtimeTrip.route_id == route_id)

    updates = query.all()

    now = datetime.now(timezone.utc).timestamp()

    upcoming = [u for u in updates if u.arrival_time and u.arrival_time >= now]
    upcoming.sort(key=lambda x: x.arrival_time)

    results = []

    for u in upcoming[:num]:
        is_transfer = u.stop_id not in stop_ids

        terminal_stop = utils.get_last_stop_for_trip(db, u.trip_id)
        terminal_name = terminal_stop.stop_name if terminal_stop else "Unknown"

        results.append({
            "route": u.trip.route_id,
            "to": terminal_name,
            "arrival_time": utils.format_time(u.arrival_time),
            "arrival_timestamp": u.arrival_time,
            "stop_id": u.stop_id,
            "is_transfer": is_transfer,
        })

    return {
        "stop_id": parent_stop_id,
        "route_id": route_id,
        "results": results,
    }