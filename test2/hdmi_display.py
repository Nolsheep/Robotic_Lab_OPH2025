# hdmi_display.py
#!/usr/bin/env python3
import cv2, subprocess, re

HDMI_NAME = "HDMI-0"   # ตั้งชื่อพอร์ตจอ เช่น "HDMI-0"; ถ้าไม่รู้ปล่อย None ให้ค้นหา
FULLSCREEN = True
MANUAL_FALLBACK = False
MANUAL_POS = (1920, 0) # ใช้เมื่อ MANUAL_FALLBACK=True (ตัวอย่างจอ2อยู่ขวา)

def _parse_xrandr_for_output(target_name=None):
    try:
        out = subprocess.check_output(["xrandr", "-q"], text=True)
    except Exception:
        return None
    for line in out.splitlines():
        if target_name and target_name in line and " connected" in line:
            m = re.search(r"(\d+)x(\d+)\+(\d+)\+(\d+)", line)
            if m:
                w, h, x, y = map(int, m.groups())
                return {"name": target_name, "w": w, "h": h, "x": x, "y": y}
    for line in out.splitlines():
        if "HDMI" in line and " connected" in line:
            name = re.match(r"^(\S+)\s+connected", line).group(1)
            m = re.search(r"(\d+)x(\d+)\+(\d+)\+(\d+)", line)
            if m:
                w, h, x, y = map(int, m.groups())
                return {"name": name, "w": w, "h": h, "x": x, "y": y}
    return None

def place_on_hdmi(window_name: str):
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    info = _parse_xrandr_for_output(HDMI_NAME)
    if info:
        cv2.moveWindow(window_name, info["x"], info["y"])
        try:
            cv2.resizeWindow(window_name, info["w"], info["h"])
        except Exception:
            pass
        if FULLSCREEN:
            cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        print(f"[INFO] Window -> {info['name']} @ {info['w']}x{info['h']}+{info['x']}+{info['y']}")
    else:
        if MANUAL_FALLBACK:
            cv2.moveWindow(window_name, MANUAL_POS[0], MANUAL_POS[1])
            if FULLSCREEN:
                cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            print(f"[INFO] Window -> manual position {MANUAL_POS[0]},{MANUAL_POS[1]}")
        else:
            print("[WARN] ไม่พบจอ HDMI (xrandr) และ MANUAL_FALLBACK=False → เปิดบนจอหลัก")
