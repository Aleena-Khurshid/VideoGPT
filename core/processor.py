import cv2
import os
import time
from datetime import datetime
from loguru import logger
from core.detector import detect_vehicles, draw_detections
from core.alpr import detect_and_read_plate
from core.color_extractor import dominant_color_kmeans
from database.crud import insert_sighting, get_camera
from dotenv import load_dotenv

load_dotenv()

FRAME_SKIP          = int(os.getenv("FRAME_SKIP", 5))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 0.45))


def process_video(camera_id: str, video_path: str,
                  progress_callback=None) -> dict:
    if not os.path.exists(video_path):
        logger.error(f"[PROCESSOR] Video not found: {video_path}")
        return {"error": "Video not found", "processed": 0, "detections": 0}

    cam = get_camera(camera_id)
    if not cam:
        logger.error(f"[PROCESSOR] Camera {camera_id} not registered.")
        return {"error": "Camera not registered", "processed": 0, "detections": 0}

    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps          = cap.get(cv2.CAP_PROP_FPS) or 25.0
    frame_count  = 0
    detection_count = 0
    saved_count  = 0

    os.makedirs(f"data/frames/{camera_id}", exist_ok=True)
    logger.info(
        f"[PROCESSOR] Starting {camera_id} | Frames:{total_frames} | "
        f"FPS:{fps:.1f} | Skip:{FRAME_SKIP}")

    start_time = time.time()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1

        if progress_callback and frame_count % 30 == 0:
            pct = int((frame_count / max(total_frames, 1)) * 100)
            progress_callback(min(pct, 99))

        if frame_count % FRAME_SKIP != 0:
            continue

        h, w = frame.shape[:2]
        if w > 640:
            scale       = 640 / w
            frame_small = cv2.resize(frame, None, fx=scale, fy=scale)
        else:
            frame_small = frame.copy()

        detections = detect_vehicles(frame_small, conf=CONFIDENCE_THRESHOLD)
        if not detections:
            continue

        plates = []
        for det in detections:
            crop       = det["crop"]
            plate_text, plate_conf = detect_and_read_plate(crop)
            color      = dominant_color_kmeans(crop)
            plates.append(plate_text)

            timestamp_sec  = frame_count / fps
            timestamp_real = datetime.utcnow()

            x1, y1, x2, y2 = det["bbox"]
            frame_path = ""
            if saved_count % 5 == 0:
                fname = (f"data/frames/{camera_id}/"
                         f"f{frame_count}_{plate_text}.jpg")
                annotated = draw_detections(
                    frame_small.copy(), [det], [plate_text])
                cv2.imwrite(fname, annotated)
                frame_path = fname

            insert_sighting({
                "camera_id":        camera_id,
                "plate_number":     plate_text,
                "plate_confidence": plate_conf,
                "vehicle_type":     det["label"],
                "vehicle_color":    color,
                "direction":        _estimate_direction(x1, w),
                "timestamp_video":  round(timestamp_sec, 2),
                "timestamp_real":   timestamp_real,
                "frame_number":     frame_count,
                "frame_path":       frame_path,
                "bbox_x":           x1,
                "bbox_y":           y1,
                "bbox_w":           x2 - x1,
                "bbox_h":           y2 - y1,
            })
            detection_count += 1
            saved_count     += 1

    cap.release()
    elapsed = time.time() - start_time
    logger.info(
        f"[PROCESSOR] Done {camera_id} | Detections:{detection_count} | "
        f"Time:{elapsed:.1f}s")

    return {
        "camera_id":        camera_id,
        "frames_processed": frame_count // FRAME_SKIP,
        "detections":       detection_count,
        "elapsed_sec":      round(elapsed, 1)
    }


def _estimate_direction(x1: int, frame_width: int) -> str:
    return "entering" if x1 < frame_width // 2 else "exiting"
