from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session

from app.services import services, static_services
from app.db import get_db, create_table, create_database_if_not_exists, SessionLocal

@asynccontextmanager
async def lifespan(_: FastAPI):
    create_database_if_not_exists()
    create_table()

    db = SessionLocal()
    try:
        static_services.populate_static_gtfs(db)
    finally:
        db.close()
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/")
def get_test(db: Session = Depends(get_db)):
    return services.get_test(db)