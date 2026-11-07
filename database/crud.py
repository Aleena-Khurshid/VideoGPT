from database.models import SessionLocal, Camera, VehicleSighting, Investigation, PlateMatch
from datetime import datetime
from loguru import logger
import json


def get_session():
    return SessionLocal()


# ── Camera ────────────────────────────────────────────────────────────────────

def register_camera(camera_id: str, location: str,
                    description: str, video_path: str):
    db = get_session()
    try:
        existing = db.query(Camera).filter(
            Camera.camera_id == camera_id).first()
        if existing:
            existing.location    = location
            existing.description = description
            existing.video_path  = video_path
            db.commit()
            logger.info(f"[CRUD] Camera {camera_id} updated.")
            return existing
        cam = Camera(camera_id=camera_id, location=location,
                     description=description, video_path=video_path)
        db.add(cam)
        db.commit()
        db.refresh(cam)
        logger.info(f"[CRUD] Camera {camera_id} registered.")
        return cam
    finally:
        db.close()


def get_all_cameras():
    db = get_session()
    try:
        return db.query(Camera).all()
    finally:
        db.close()


def get_camera(camera_id: str):
    db = get_session()
    try:
        return db.query(Camera).filter(
            Camera.camera_id == camera_id).first()
    finally:
        db.close()


def delete_camera(camera_id: str):
    db = get_session()
    try:
        cam = db.query(Camera).filter(
            Camera.camera_id == camera_id).first()
        if cam:
            db.delete(cam)
            db.commit()
    finally:
        db.close()


# ── Sightings ─────────────────────────────────────────────────────────────────

def insert_sighting(data: dict):
    db = get_session()
    try:
        sighting = VehicleSighting(**data)
        db.add(sighting)
        db.commit()
        db.refresh(sighting)
        return sighting
    finally:
        db.close()


def get_sightings_by_camera(camera_id: str):
    db = get_session()
    try:
        return (db.query(VehicleSighting)
                  .filter(VehicleSighting.camera_id == camera_id)
                  .order_by(VehicleSighting.timestamp_video)
                  .all())
    finally:
        db.close()


def get_sightings_by_plate(plate: str, cameras: list = None):
    db = get_session()
    try:
        q = db.query(VehicleSighting).filter(
            VehicleSighting.plate_number.ilike(f"%{plate}%"))
        if cameras:
            q = q.filter(VehicleSighting.camera_id.in_(cameras))
        return q.order_by(VehicleSighting.timestamp_video).all()
    finally:
        db.close()


def search_sightings(filters: dict):
    db = get_session()
    try:
        q = db.query(VehicleSighting)
        if filters.get("plate"):
            q = q.filter(
                VehicleSighting.plate_number.ilike(f"%{filters['plate']}%"))
        if filters.get("vehicle_type"):
            q = q.filter(
                VehicleSighting.vehicle_type == filters["vehicle_type"])
        if filters.get("vehicle_color"):
            q = q.filter(
                VehicleSighting.vehicle_color == filters["vehicle_color"])
        if filters.get("camera_ids"):
            q = q.filter(
                VehicleSighting.camera_id.in_(filters["camera_ids"]))
        return q.order_by(VehicleSighting.timestamp_video).all()
    finally:
        db.close()


def get_all_sightings():
    db = get_session()
    try:
        return (db.query(VehicleSighting)
                  .order_by(VehicleSighting.created_at.desc())
                  .all())
    finally:
        db.close()


def get_all_plates_by_camera(camera_id: str):
    db = get_session()
    try:
        rows = (db.query(VehicleSighting.plate_number)
                  .filter(VehicleSighting.camera_id == camera_id,
                          VehicleSighting.plate_number != "UNKNOWN")
                  .distinct()
                  .all())
        return [r[0] for r in rows]
    finally:
        db.close()


def clear_camera_sightings(camera_id: str):
    db = get_session()
    try:
        (db.query(VehicleSighting)
           .filter(VehicleSighting.camera_id == camera_id)
           .delete())
        db.commit()
    finally:
        db.close()


# ── Investigations ────────────────────────────────────────────────────────────

def save_investigation(query_text: str, parsed_params: dict,
                       result_summary: str, alert_sent: bool = False):
    db = get_session()
    try:
        inv = Investigation(
            query_text=query_text,
            parsed_params=json.dumps(parsed_params),
            result_summary=result_summary,
            alert_sent=alert_sent
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)
        return inv
    finally:
        db.close()


def get_all_investigations():
    db = get_session()
    try:
        return (db.query(Investigation)
                  .order_by(Investigation.created_at.desc())
                  .all())
    finally:
        db.close()
