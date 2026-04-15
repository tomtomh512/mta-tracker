from app.db import SessionLocal
from app.services import static_services

def scheduled_static_gtfs_update():
    db = SessionLocal()
    try:
        static_services.update_static_gtfs(db)
    except Exception as e:
        print("Scheduled GTFS update failed:", e)
    finally:
        db.close()