from sqlalchemy.orm import Session

from app.models import StaticRoute, StaticShape, StaticStop, StaticTrip


def get_test(db: Session):

    # temp function to test static info injection
    route_count = db.query(StaticRoute).count()
    stop_count = db.query(StaticStop).count()
    trip_count = db.query(StaticTrip).count()
    shape_count = db.query(StaticShape).count()

    print(f"Routes:         {route_count}")
    print(f"Stops:          {stop_count}")
    print(f"Trips:          {trip_count}")
    print(f"Shape points:   {shape_count}")

    sample_route = db.query(StaticRoute).first()
    if sample_route:
        print(f"Sample route: [{sample_route.route_id}] {sample_route.route_long_name} (#{sample_route.route_color})")

    sample_stop = db.query(StaticStop).first()
    if sample_stop:
        print(f"Sample stop:  {sample_stop.stop_name} ({sample_stop.stop_lat}, {sample_stop.stop_lon})")