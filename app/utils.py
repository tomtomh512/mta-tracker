from sqlalchemy.orm import Session
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

NY_TZ = ZoneInfo("America/New_York")

from app.models import StaticStop, StaticTransfer

def format_time(ts):
    if ts is None:
        return "—"

    return datetime.fromtimestamp(ts, tz=NY_TZ).strftime("%Y-%m-%d %I:%M:%S %p")

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