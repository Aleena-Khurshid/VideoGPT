import cv2
import numpy as np
from sklearn.cluster import KMeans


def dominant_color_kmeans(crop: np.ndarray, k: int = 3) -> str:
    if crop is None or crop.size == 0:
        return "unknown"
    try:
        h, w = crop.shape[:2]
        roi = crop[h // 5: 4 * h // 5, w // 8: 7 * w // 8]
        if roi.size == 0:
            roi = crop
        small = cv2.resize(roi, (60, 60))
        hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
        pixels = hsv.reshape(-1, 3).astype(np.float32)
        km = KMeans(n_clusters=k, n_init=3, random_state=0)
        km.fit(pixels)
        labels, counts = np.unique(km.labels_, return_counts=True)
        dominant = km.cluster_centers_[labels[np.argmax(counts)]]
        return _hsv_to_name(dominant)
    except Exception:
        return "unknown"


def _hsv_to_name(hsv_pixel: np.ndarray) -> str:
    h, s, v = hsv_pixel
    if v < 50:
        return "black"
    if s < 30 and v > 180:
        return "white"
    if s < 40:
        return "silver"
    if (0 <= h <= 10) or (160 <= h <= 180):
        return "red"
    if 11 <= h <= 22:
        return "orange"
    if 23 <= h <= 35:
        return "yellow"
    if 36 <= h <= 85:
        return "green"
    if 86 <= h <= 130:
        return "blue"
    return "unknown"
