import cv2
import numpy as np
import easyocr
import re
from loguru import logger

_reader = None


def get_reader():
    global _reader
    if _reader is None:
        logger.info("[ALPR] Loading EasyOCR (CPU mode)...")
        _reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        logger.info("[ALPR] EasyOCR ready.")
    return _reader


def preprocess_plate_crop(crop: np.ndarray) -> np.ndarray:
    if crop is None or crop.size == 0:
        return crop
    h, w = crop.shape[:2]
    if w < 100:
        scale = 200 / max(w, 1)
        crop = cv2.resize(crop, None, fx=scale, fy=scale,
                          interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    _, thresh = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh


def clean_plate_text(raw: str) -> str:
    cleaned = re.sub(r"[^A-Z0-9\-]", "", raw.upper().strip())
    return cleaned if len(cleaned) >= 3 else "UNKNOWN"


def read_plate(crop: np.ndarray) -> tuple:
    if crop is None or crop.size == 0:
        return "UNKNOWN", 0.0
    try:
        processed = preprocess_plate_crop(crop)
        reader = get_reader()
        results = reader.readtext(processed, detail=1, paragraph=False)
        if not results:
            return "UNKNOWN", 0.0
        best = max(results, key=lambda r: r[2])
        text = clean_plate_text(best[1])
        conf = round(float(best[2]), 3)
        return text, conf
    except Exception as e:
        logger.warning(f"[ALPR] OCR error: {e}")
        return "UNKNOWN", 0.0


def detect_and_read_plate(vehicle_crop: np.ndarray) -> tuple:
    return read_plate(vehicle_crop)
