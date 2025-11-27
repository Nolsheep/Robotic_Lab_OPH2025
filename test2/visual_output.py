# visual_output.py
import cv2, os, time
import numpy as np
from typing import Dict

DISPLAY_DURATION_SEC = 2.0
BANNER_POSITION = "center"  # "center" | "top-left" | "top-right" | "bottom-left" | "bottom-right"
MAX_ICON_WIDTH = 420

_icon_cache: Dict[str, np.ndarray] = {}
_active_label = None
_banner_end_time = 0.0

def init_visual(icon_map: dict, display_sec: float = 2.0, position: str = "center", max_icon_w: int = 420):
    global DISPLAY_DURATION_SEC, BANNER_POSITION, MAX_ICON_WIDTH, _icon_cache
    DISPLAY_DURATION_SEC = display_sec
    BANNER_POSITION = position
    MAX_ICON_WIDTH = max_icon_w
    _icon_cache = _load_icons(icon_map)

def handle_event(label: str):
    """เรียกเมื่อ detect เจอคลาส → ตั้งให้แสดงป้าย PNG ของคลาสนั้นชั่วคราว"""
    global _active_label, _banner_end_time
    _active_label = label
    _banner_end_time = time.time() + DISPLAY_DURATION_SEC

def apply_overlay(frame):
    """เรียกทุกลูป: ถ้ายังอยู่ในช่วงเวลาแสดงป้าย → ซ้อน PNG ลงบนเฟรม"""
    global _active_label, _banner_end_time
    if not _active_label or time.time() > _banner_end_time:
        _active_label = None
        return frame
    icon = _icon_cache.get(_active_label)
    if icon is None:
        return frame
    return _overlay_rgba(frame, icon, BANNER_POSITION, margin=24)

# ----------------- helpers -----------------
def _load_icons(icon_map: dict):
    cache = {}
    for label, p in icon_map.items():
        if not os.path.isfile(p):
            cache[label] = None
            continue
        icon = cv2.imread(p, cv2.IMREAD_UNCHANGED)  # RGBA
        if icon is None: 
            cache[label] = None
            continue
        h, w = icon.shape[:2]
        if w > MAX_ICON_WIDTH:
            s = MAX_ICON_WIDTH / float(w)
            icon = cv2.resize(icon, (int(w*s), int(h*s)), interpolation=cv2.INTER_AREA)
        cache[label] = icon
    return cache

def _overlay_rgba(base_bgr, rgba_icon, pos="center", margin=20):
    if rgba_icon is None: return base_bgr
    if rgba_icon.shape[2] == 3:  # ไม่มี alpha
        bgr = rgba_icon
        a = (np.ones((bgr.shape[0], bgr.shape[1])) * 255).astype(np.uint8)
        rgba_icon = np.dstack([bgr, a])

    hI, wI = rgba_icon.shape[:2]
    hF, wF = base_bgr.shape[:2]

    if pos == "center":
        x, y = (wF - wI)//2, (hF - hI)//2
    elif pos == "top-left":
        x, y = margin, margin
    elif pos == "top-right":
        x, y = wF - wI - margin, margin
    elif pos == "bottom-left":
        x, y = margin, hF - hI - margin
    else:
        x, y = wF - wI - margin, hF - hI - margin

    # ถ้าหลุดเฟรม → ย่อให้พอดี
    if x < 0 or y < 0 or x + wI > wF or y + hI > hF:
        s = min(wF / float(wI), hF / float(hI)) * 0.95
        wI2, hI2 = max(1, int(wI*s)), max(1, int(hI*s))
        rgba_icon = cv2.resize(rgba_icon, (wI2, hI2), interpolation=cv2.INTER_AREA)
        hI, wI = hI2, wI2
        x, y = (wF - wI)//2, (hF - hI)//2

    b, g, r, a = cv2.split(rgba_icon)
    overlay_rgb = cv2.merge((b, g, r))
    alpha = a.astype(float)/255.0

    roi = base_bgr[y:y+hI, x:x+wI].astype(float)
    for c in range(3):
        roi[..., c] = alpha * overlay_rgb[..., c] + (1 - alpha) * roi[..., c]
    base_bgr[y:y+hI, x:x+wI] = roi.astype(np.uint8)
    return base_bgr
