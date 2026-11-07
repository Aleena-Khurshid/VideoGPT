import json
from database.crud import (get_sightings_by_plate, search_sightings,
                            save_investigation)
from loguru import logger


def run_investigation(parsed: dict) -> dict:
    plate  = parsed.get("plate")
    cameras = parsed.get("cameras")
    action  = parsed.get("action", "search")

    if action == "investigate" and plate:
        return _investigate_plate(plate, cameras)
    return _general_search(parsed)


def _investigate_plate(plate: str, cameras: list) -> dict:
    sightings = get_sightings_by_plate(plate, cameras)

    camera_data: dict = {}
    for s in sightings:
        camera_data.setdefault(s.camera_id, []).append(s)

    timeline = []
    for s in sorted(sightings, key=lambda x: x.timestamp_video):
        timeline.append({
            "camera_id":      s.camera_id,
            "plate":          s.plate_number,
            "vehicle_type":   s.vehicle_type,
            "color":          s.vehicle_color,
            "timestamp_video": s.timestamp_video,
            "timestamp_real": (s.timestamp_real.strftime("%Y-%m-%d %H:%M:%S")
                               if s.timestamp_real else ""),
            "direction":      s.direction,
            "frame_path":     s.frame_path,
            "id":             s.id
        })

    all_cams = cameras if cameras else list(camera_data.keys())
    comparison = {}
    for cam in all_cams:
        plates_in = [s.plate_number for s in camera_data.get(cam, [])]
        comparison[cam] = {
            "found":         cam in camera_data,
            "sighting_count": len(camera_data.get(cam, [])),
            "plates":        list(set(plates_in))
        }

    gaps      = _compute_gaps(camera_data)
    found_in  = [c for c in all_cams if c in camera_data]
    match_pct = int((len(found_in) / max(len(all_cams), 1)) * 100)

    summary = (
        f"Plate {plate} found in {len(found_in)}/{len(all_cams)} cameras: "
        f"{', '.join(found_in) if found_in else 'none'}. "
        f"Match score: {match_pct}%."
    )

    save_investigation(
        query_text=f"investigate {plate} cameras={cameras}",
        parsed_params={"plate": plate, "cameras": cameras},
        result_summary=summary
    )

    return {
        "type":             "investigation",
        "plate":            plate,
        "cameras_searched": all_cams,
        "cameras_found":    found_in,
        "match_pct":        match_pct,
        "timeline":         timeline,
        "comparison":       comparison,
        "gaps":             gaps,
        "summary":          summary,
        "total_sightings":  len(sightings)
    }


def _general_search(parsed: dict) -> dict:
    filters = {}
    if parsed.get("plate"):
        filters["plate"] = parsed["plate"]
    if parsed.get("vehicle_type"):
        filters["vehicle_type"] = parsed["vehicle_type"]
    if parsed.get("vehicle_color"):
        filters["vehicle_color"] = parsed["vehicle_color"]
    if parsed.get("cameras"):
        filters["camera_ids"] = parsed["cameras"]

    sightings = search_sightings(filters)
    results = []
    for s in sightings:
        results.append({
            "camera_id":       s.camera_id,
            "plate":           s.plate_number,
            "vehicle_type":    s.vehicle_type,
            "color":           s.vehicle_color,
            "timestamp_video": s.timestamp_video,
            "timestamp_real":  (s.timestamp_real.strftime("%Y-%m-%d %H:%M:%S")
                                if s.timestamp_real else ""),
            "direction":       s.direction,
            "frame_path":      s.frame_path,
            "id":              s.id
        })

    return {
        "type":    "search",
        "filters": parsed,
        "results": results,
        "total":   len(results),
        "summary": f"Found {len(results)} sighting(s) matching your query."
    }


def _compute_gaps(camera_data: dict) -> list:
    first = {}
    for cam, sightings in camera_data.items():
        if sightings:
            first[cam] = min(s.timestamp_video for s in sightings)

    cams = sorted(first.keys(), key=lambda c: first[c])
    gaps = []
    for i in range(len(cams) - 1):
        c1, c2 = cams[i], cams[i + 1]
        diff = first[c2] - first[c1]
        gaps.append({
            "from":        c1,
            "to":          c2,
            "gap_seconds": round(diff, 1),
            "gap_str":     _fmt(diff)
        })
    return gaps


def _fmt(seconds: float) -> str:
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m}m {s}s" if m > 0 else f"{s}s"
