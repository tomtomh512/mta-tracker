from app.db import SessionLocal
from app.services import static_services, realtime_services

def scheduled_static_gtfs_update():
    db = SessionLocal()
    try:
        static_services.update_static_gtfs(db)
    except Exception as e:
        print("Scheduled GTFS update failed:")
    finally:
        db.close()

def scheduled_trip_update():
    db = SessionLocal()
    try:
        realtime_services.populate_trips(db)
    except Exception as e:
        print("Scheduled realtime update failed:")
    finally:
        db.close()

def scheduled_trips_cleanup():
    db = SessionLocal()
    try:
        realtime_services.cleanup_trips(db)
    except Exception as e:
        print("Scheduled realtime update failed:")
    finally:
        db.close()