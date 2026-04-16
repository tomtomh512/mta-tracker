from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler

from app.scheduler import scheduled_jobs
from app.services import static_service, realtime_service, stop_service, trip_service, map_service
from app.db import get_db, create_table, create_database_if_not_exists, SessionLocal

@asynccontextmanager
async def lifespan(_: FastAPI):
    create_database_if_not_exists()
    create_table()

    db = SessionLocal()
    try:
        static_service.populate_static_gtfs(db)
        # realtime_service.populate_trips(db)
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

@app.get("/trip/{route_id}")
def get_trips(route_id: str, db: Session = Depends(get_db)):
    return trip_service.get_active_trips_by_route(db, route_id)

@app.get("/stop/{stop_id}")
def get_wait_times(stop_id: str, db: Session = Depends(get_db)):
    return stop_service.get_wait_times(db, stop_id)

@app.get("/map/{route_id}")
def get_wait_times(route_id: str, db: Session = Depends(get_db)):
    return map_service.get_route_map_data(db, route_id)
