# hdmi_display.py
import cv2, subprocess, re, os

HDMI_NAME = os.environ.get("HDMI_NAME", "HDMI-0")  # เช่น "HDMI-0"; ไม่รู้ให้ลอง None
FULLSCREEN = os.environ.get("HDMI_FULLSCREEN", "1") == "1"
MANUAL_FALLBACK = os.environ.get("HDMI_MANUAL", "0") == "1"
MANUAL_POS = (int(os.environ.get("HDMI_X", 1920)), int(os.environ.get("HDMI_Y", 0)))

def _parse_xrandr_for_output(target_name=None):
    try:
        out = subprocess.check_output(["xrandr", "-q"], text=True)
    except Exception:
        return None
    lines = out.splitlines()

    if target_name:
        for line in lines:
            if target_name in line and " connected" in line:
                m = re.search(r"(\d+)x(\d+)\+(\d+)\+(\d+)", line)
                if m:
                    w, h, x, y = map(int, m.groups())
                    return {"name": target_name, "w": w, "h": h, "x": x, "y": y}

    for line in lines:
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
        print(f"[HDMI] {window_name} -> {info['name']} @ {info['w']}x{info['h']}+{info['x']}+{info['y']}")
    else:
        if MANUAL_FALLBACK:
            cv2.moveWindow(window_name, MANUAL_POS[0], MANUAL_POS[1])
            if FULLSCREEN:
                cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            print(f"[HDMI] {window_name} -> manual {MANUAL_POS}")
        else:
            print("[HDMI] not found (xrandr). Showing on primary display.")
