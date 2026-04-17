from pydantic import BaseModel

class StopBase(BaseModel):
    stop_id: str
    stop_name: str
    stop_lat: float
    stop_lon: float
    location_type: int | None

    class Config:
        from_attributes = True

class RouteBase(BaseModel):
    route_id: str
    agency_id: str
    route_short_name: str
    route_long_name: str
    route_desc: str | None
    route_type: int
    route_url: str | None
    route_sort_order: int | None

    class Config:
        from_attributes = True


class Stop(StopBase):
    pass

class Route(RouteBase):
    pass

class WaitTime(BaseModel):
    route: str | None
    to: str
    direction_id: int | None
    arrival_time: str
    arrival_timestamp: int | None
    stop_id: str
    is_transfer: bool

class WaitTimes(BaseModel):
    stop_id: str
    route_id: str | None
    results: list[WaitTime]

class NearbyStop(StopBase):
    distance_m: int

class RouteStops(BaseModel):
    route_id: str
    stops: list[StopBase]

    class Config:
        from_attributes = True

class TripStop(BaseModel):
    stop_id: str
    stop_name: str | None
    arrival_time: str
    departure_time: str
    arrival_timestamp: int | None
    departure_timestamp: int | None


class Trip(BaseModel):
    trip_id: str
    to: str
    direction_id: int | None
    stops: list[TripStop]


class ActiveTrips(BaseModel):
    route_id: str
    trips: list[Trip]

class ShapePoint(BaseModel):
    lat: float
    lon: float

class RouteStop(BaseModel):
    stop_id: str
    stop_name: str
    lat: float
    lon: float

class RouteMapData(BaseModel):
    route_id: str
    route_short_name: str
    route_color: str | None
    route_text_color: str | None
    shapes: list[list[ShapePoint]]  # list of polylines, one per shape_id
    stops: list[RouteStop]