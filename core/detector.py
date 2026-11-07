import cv2
import numpy as np
from ultralytics import YOLO
from loguru import logger

VEHICLE_CLASSES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
_model = None


def load_model():
    global _model
    if _model is None:
        logger.info("[DETECTOR] Loading YOLOv8n model...")
        _model = YOLO("yolov8n.pt")
        logger.info("[DETECTOR] YOLOv8n loaded.")
    return _model


def detect_vehicles(frame: np.ndarray, conf: float = 0.45):
    model = load_model()
    results = model(frame, verbose=False, conf=conf)[0]
    detections = []
    for box in results.boxes:
        cls_id = int(box.cls[0])
        if cls_id not in VEHICLE_CLASSES:
            continue
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        conf_val = float(box.conf[0])
        label = VEHICLE_CLASSES[cls_id]
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            continue
        detections.append({
            "bbox": [x1, y1, x2, y2],
            "label": label,
            "confidence": round(conf_val, 3),
            "crop": crop
        })
    return detections


def draw_detections(frame: np.ndarray, detections: list,
                    plate_texts: list = None):
    colors = {
        "car":        (0, 255, 0),
        "truck":      (255, 165, 0),
        "bus":        (0, 165, 255),
        "motorcycle": (255, 0, 255)
    }
    for i, det in enumerate(detections):
        x1, y1, x2, y2 = det["bbox"]
        color = colors.get(det["label"], (0, 255, 0))
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        plate = ""
        if plate_texts and i < len(plate_texts):
            plate = plate_texts[i]
        label_text = f"{det['label']} {det['confidence']:.2f}"
        if plate and plate != "UNKNOWN":
            label_text += f" | {plate}"
        cv2.putText(frame, label_text, (x1, max(y1 - 8, 0)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
    return frame
