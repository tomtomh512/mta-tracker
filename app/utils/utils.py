from sqlalchemy.orm import Session
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import List

NY_TZ = ZoneInfo("America/New_York")

from app.models import StaticStop, StaticTransfer, StopTimeUpdate


def format_time(ts):
    if ts is None:
        return "—"

    return datetime.fromtimestamp(ts, tz=NY_TZ).strftime("%Y-%m-%d %I:%M:%S %p")

# Given a stop id, return a staticstop of the stop's parent
# If the stop is a parent, return its own staticstop
def get_parent_stop(db: Session, stop_id: str) -> StaticStop:
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
def get_children_stops(db: Session, stop_id: str) -> List[StaticStop]:
    return (
        db.query(StaticStop)
        .filter(StaticStop.parent_station == stop_id)
        .all()
    )

# Given a stop id, return a list of staticstops of the stop's transfers
def get_transfers(db: Session, stop_id: str, includeChildren: bool) -> List[StaticStop]:
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

# Returns the terminal (last known) stop for a RealtimeTrip based on max arrival_time in StopTimeUpdates
def get_last_stop_for_trip(db: Session, trip_id: str) -> List[StaticStop]:
    updates = (
        db.query(StopTimeUpdate)
        .filter(StopTimeUpdate.trip_id == trip_id)
        .all()
    )

    if not updates:
        return None

    terminal_update = max(
        (u for u in updates if u.arrival_time is not None),
        key=lambda x: x.arrival_time,
        default=None
    )

    return terminal_update.stop if terminal_update else None

def get_all_stop_ids(db: Session, stop_id: str):
    stop = get_parent_stop(db, stop_id)
    parent_stop_id = stop.stop_id

    children = get_children_stops(db, parent_stop_id)
    child_ids = [s.stop_id for s in children]

    stop_ids = list(set([parent_stop_id] + child_ids))

    transfer_stop_ids = []

    for current_stop_id in stop_ids:
        current_transfers = get_transfers(db, current_stop_id, True)
        current_transfer_stop_ids = [s.stop_id for s in current_transfers]
        transfer_stop_ids.extend(current_transfer_stop_ids)

    all_stop_ids = list(set(stop_ids + transfer_stop_ids))

    return parent_stop_id, stop_ids, all_stop_ids