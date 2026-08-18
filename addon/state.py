from __future__ import annotations

from typing import Any, TypedDict


class DockState(TypedDict):
    visible: bool
    area: str
    width: int
    floating: bool
    geometry: str
    zoom_factor: float


DEFAULT_STATE: DockState = {
    "visible": True,
    "area": "right",
    "width": 460,
    "floating": False,
    "geometry": "",
    "zoom_factor": 1.0,
}


def normalize_state(value: Any) -> DockState:
    raw = value if isinstance(value, dict) else {}
    area = raw.get("area")
    width = raw.get("width")
    zoom_factor = raw.get("zoom_factor")
    visible = raw.get("visible")
    floating = raw.get("floating")
    geometry = raw.get("geometry")

    return {
        "visible": visible if isinstance(visible, bool) else DEFAULT_STATE["visible"],
        "area": area if area in {"left", "right"} else DEFAULT_STATE["area"],
        "width": max(320, min(1200, width))
        if isinstance(width, int) and not isinstance(width, bool)
        else DEFAULT_STATE["width"],
        "floating": floating
        if isinstance(floating, bool)
        else DEFAULT_STATE["floating"],
        "geometry": geometry
        if isinstance(geometry, str)
        else DEFAULT_STATE["geometry"],
        "zoom_factor": max(0.5, min(2.0, float(zoom_factor)))
        if isinstance(zoom_factor, int | float) and not isinstance(zoom_factor, bool)
        else DEFAULT_STATE["zoom_factor"],
    }
