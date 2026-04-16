from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler

from app.scheduler import scheduled_jobs
from app.services import services, static_services, realtime_services
from app.db import get_db, create_table, create_database_if_not_exists, SessionLocal

@asynccontextmanager
async def lifespan(_: FastAPI):
    create_database_if_not_exists()
    create_table()

    db = SessionLocal()
    try:
        static_services.populate_static_gtfs(db)
        realtime_services.populate_trips(db)
    finally:
        db.close()

    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduled_jobs.scheduled_static_gtfs_update, "cron", hour=0, minute=0)
    # scheduler.add_job(scheduled_jobs.scheduled_trip_update, "interval", seconds=30)
    # scheduler.add_job(scheduled_jobs.scheduled_trips_cleanup, "interval", minutes=30)
    scheduler.start()

    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

@app.get("/test_static")
def test_static(db: Session = Depends(get_db)):
    return services.test_static(db)

@app.get("/test_realtime/{route_id}")
def test_realtime(route_id: str, db: Session = Depends(get_db)):
    return services.test_realtime(db, route_id)

@app.get("/test_station_wait/{stop_id}")
def test_station_wait(stop_id: str, db: Session = Depends(get_db)):
    return services.get_next_trains_at_station(db, stop_id)