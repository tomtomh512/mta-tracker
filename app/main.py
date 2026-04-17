from fastapi import FastAPI
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.limiter import limiter
from app.scheduler import scheduled_jobs
from app.services import static_service, realtime_service
from app.db import create_table, create_database_if_not_exists, SessionLocal
from app.api import stops, routes

@asynccontextmanager
async def lifespan(_: FastAPI):
    create_database_if_not_exists()
    create_table()

    db = SessionLocal()
    try:
        static_service.populate_static_gtfs(db)
        realtime_service.populate_trips(db)
    finally:
        db.close()

    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduled_jobs.scheduled_static_gtfs_update, "cron", hour=0, minute=0)
    scheduler.add_job(scheduled_jobs.scheduled_trip_update, "interval", seconds=30)
    scheduler.add_job(scheduled_jobs.scheduled_trips_cleanup, "interval", minutes=30)
    scheduler.start()

    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(stops.router)
app.include_router(routes.router)