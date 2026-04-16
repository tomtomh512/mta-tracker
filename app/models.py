from app.db import Base
from sqlalchemy import Integer, Column, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

class StaticRoute(Base):
    __tablename__ = 'StaticRoutes'

    route_id = Column(String, primary_key=True)
    agency_id = Column(String, nullable=False)
    route_short_name = Column(String, nullable=False)   # "A", "1", "G", etc.
    route_long_name = Column(String, nullable=False)    # "8 Avenue Express"
    route_desc = Column(String, nullable=True)
    route_type = Column(Integer, nullable=False)        # 1 = subway, 2 = rail
    route_url = Column(String, nullable=True)
    route_color = Column(String, nullable=True)         # hex, e.g. "0062CF"
    route_text_color = Column(String, nullable=True)    # hex, e.g. "FFFFFF"
    route_sort_order = Column(Integer, nullable=True)

    trips = relationship("StaticTrip", back_populates="route")


class StaticStop(Base):
    __tablename__ = 'StaticStops'

    stop_id = Column(String, primary_key=True)
    stop_name = Column(String, nullable=False)          # "Times Sq-42 St"
    stop_lat = Column(Float, nullable=False)
    stop_lon = Column(Float, nullable=False)
    location_type = Column(Integer, nullable=True)      # 0 = stop, 1 = station
    parent_station = Column(String, ForeignKey('StaticStops.stop_id'), nullable=True)


class StaticShape(Base):
    __tablename__ = 'StaticShapes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    shape_id = Column(String, nullable=False, index=True)
    shape_pt_lat = Column(Float, nullable=False)
    shape_pt_lon = Column(Float, nullable=False)
    shape_pt_sequence = Column(Integer, nullable=False)
    shape_dist_traveled = Column(Float, nullable=True)


class StaticTrip(Base):
    __tablename__ = 'StaticTrips'

    trip_id = Column(String, primary_key=True)
    route_id = Column(String, ForeignKey('StaticRoutes.route_id'), nullable=False)
    service_id = Column(String, nullable=False)         # "Weekday", "Saturday", "Sunday"
    shape_id = Column(String, nullable=False, index=True)  # links to StaticShapes
    trip_headsign = Column(String, nullable=True)       # destination display text
    direction_id = Column(Integer, nullable=True)       # 0 = outbound, 1 = inbound

    route = relationship("StaticRoute", back_populates="trips")


class StaticTransfer(Base):
    __tablename__ = 'StaticTransfers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    from_stop_id = Column(String, ForeignKey('StaticStops.stop_id'), nullable=False, index=True)
    to_stop_id = Column(String, ForeignKey('StaticStops.stop_id'), nullable=False, index=True)
    transfer_type = Column(Integer, nullable=False)
    min_transfer_time = Column(Integer, nullable=True)

    from_stop = relationship("StaticStop", foreign_keys=[from_stop_id])
    to_stop = relationship("StaticStop", foreign_keys=[to_stop_id])


class RealtimeTrip(Base):
    __tablename__ = 'RealtimeTrips'

    trip_id = Column(String, ForeignKey('StaticTrips.trip_id'), primary_key=True)
    route_id = Column(String, ForeignKey('StaticRoutes.route_id'), nullable=False, index=True)
    direction_id = Column(Integer, nullable=True)
    start_time = Column(String, nullable=True)
    start_date = Column(String, nullable=True)
    last_updated = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    static_trip = relationship("StaticTrip", backref="realtime_trip")
    stop_time_updates = relationship("StopTimeUpdate", back_populates="trip",
                                     cascade="all, delete-orphan")


class StopTimeUpdate(Base):
    __tablename__ = 'StopTimeUpdates'

    id = Column(Integer, primary_key=True, autoincrement=True)
    trip_id = Column(String, ForeignKey('RealtimeTrips.trip_id'), nullable=False, index=True)
    stop_id = Column(String, ForeignKey('StaticStops.stop_id'), nullable=False, index=True)
    arrival_time = Column(Integer, nullable=True)
    departure_time = Column(Integer, nullable=True)
    last_updated = Column(DateTime, nullable=False, default=datetime.utcnow)

    trip = relationship("RealtimeTrip", back_populates="stop_time_updates")
    stop = relationship("StaticStop")