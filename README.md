# mta-tracker

A REST API that serves real-time and static NYC subway data by consuming MTA GTFS feeds and exposing stop, route, and trip information with Redis caching.

## Technologies

- **FastAPI** — web framework
- **PostgreSQL** — persistent storage for static and realtime GTFS data
- **Docker** — containerized deployment

## Running Locally

**Prerequisites:** Python 3.11+, a running PostgreSQL instance, and a running Redis instance.

1. Clone the repo and create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate        # macOS/Linux
   venv\Scripts\activate           # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root:
   ```env
   DB_USER=
   DB_PASSWORD=
   DB_HOST=
   DB_PORT=
   DB_NAME=
   REDIS_HOST=
   REDIS_PORT=
   ```

4. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`. 

On first startup, static and realtime GTFS data are automatically downloaded and parsed into the database.

Every day at 12:00 AM, static GTFS data is updated and parsed into the database.

Every 30 seconds, realtime GTFS data is updated and parsed into the database.

## Running with Docker

**Prerequisites:** Docker and Docker Compose.

1. Create a `.env` file as shown above.

2. Build and start all services:
    ```bash
    docker compose up --build
    ```

The API will be available at `http://localhost:8000`. PostgreSQL is exposed on port `5433` and Redis on `6379`.

## Endpoints

### Stops

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/stops/` | List all stations |
| `GET` | `/stops/{stop_id}` | Get a single station |
| `GET` | `/stops/{stop_id}/routes` | List routes serving a stop |
| `GET` | `/stops/{stop_id}/wait` | Get upcoming arrival times at a stop. Optional query param: `route_id` |
| `GET` | `/stops/nearby` | Find stops within a radius. Query params: `lat`, `lon`, `radius_m`, `limit` |

### Routes

| Method | Path | Description                            |
|--------|------|----------------------------------------|
| `GET` | `/routes/` | List all routes                        |
| `GET` | `/routes/{route_id}` | Get a single route                     |
| `GET` | `/routes/{route_id}/stops` | List all stops served by a route       |
| `GET` | `/routes/{route_id}/trips` | List active realtime trips for a route |
| `GET` | `/{route_id}/map` | Get map data to display a route        |