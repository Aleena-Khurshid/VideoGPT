from sqlalchemy import (create_engine, Column, Integer, String,
                         Float, Boolean, DateTime, Text)
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/videogpt.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Camera(Base):
    __tablename__ = "cameras"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    camera_id   = Column(String, unique=True, nullable=False)
    location    = Column(String, default="")
    description = Column(String, default="")
    video_path  = Column(String, default="")
    created_at  = Column(DateTime, default=datetime.utcnow)


class VehicleSighting(Base):
    __tablename__ = "vehicle_sightings"
    id               = Column(Integer, primary_key=True, autoincrement=True)
    camera_id        = Column(String, nullable=False)
    plate_number     = Column(String, default="UNKNOWN")
    plate_confidence = Column(Float,  default=0.0)
    vehicle_type     = Column(String, default="car")
    vehicle_color    = Column(String, default="unknown")
    direction        = Column(String, default="unknown")
    timestamp_video  = Column(Float,  default=0.0)
    timestamp_real   = Column(DateTime, default=datetime.utcnow)
    frame_number     = Column(Integer, default=0)
    frame_path       = Column(String, default="")
    bbox_x           = Column(Integer, default=0)
    bbox_y           = Column(Integer, default=0)
    bbox_w           = Column(Integer, default=0)
    bbox_h           = Column(Integer, default=0)
    created_at       = Column(DateTime, default=datetime.utcnow)


class Investigation(Base):
    __tablename__ = "investigations"
    id             = Column(Integer, primary_key=True, autoincrement=True)
    query_text     = Column(Text,    default="")
    parsed_params  = Column(Text,    default="{}")
    result_summary = Column(Text,    default="")
    alert_sent     = Column(Boolean, default=False)
    created_at     = Column(DateTime, default=datetime.utcnow)


class PlateMatch(Base):
    __tablename__ = "plate_matches"
    id               = Column(Integer, primary_key=True, autoincrement=True)
    plate_number     = Column(String, default="")
    camera_ids       = Column(Text,   default="[]")
    match_confidence = Column(Float,  default=0.0)
    investigation_id = Column(Integer, default=0)
    created_at       = Column(DateTime, default=datetime.utcnow)


def init_db():
    """Create all tables and required data directories."""
    os.makedirs("data/videos/gate1", exist_ok=True)
    os.makedirs("data/videos/gate2", exist_ok=True)
    os.makedirs("data/videos/gate3", exist_ok=True)
    os.makedirs("data/frames",       exist_ok=True)
    os.makedirs("data/clips",        exist_ok=True)
    Base.metadata.create_all(bind=engine)
    print("[DB] All tables created successfully.")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
