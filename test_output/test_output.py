# test_output.py
#!/usr/bin/env python3
import sys, time, cv2, numpy as np, os, subprocess, re

import audio_output as AO
import visual_output as VO

# ---------------- CONFIG ----------------
AUDIO_MAP = {
    "Fighting":  "audio/Fighting.wav",
    "MiniHeart": "audio/MiniHeart.wav",
    "ILY":       "audio/ILY.wav",
    "FU":        "audio/FU.wav",
    "Like":      "audio/Like.wav",
}
ICON_MAP = {
    "Fighting":  "icons/Fighting.png",
    "MiniHeart": "icons/MiniHeart.png",
    "ILY":       "icons/ILY.png",
    "FU":        "icons/FU.png",
    "Like":      "icons/Like.png",
}

FRAME_W, FRAME_H = 1280, 720
DISPLAY_DURATION_SEC = 2.0

WINDOW_ONESHOT = "Test Output (No Detect)"
WINDOW_INTERACTIVE = "Test Output (Interactive)"

# ★★ จอ HDMI ★★
FORCE_HDMI_NAME = None    # ใส่เช่น "HDMI-0" หากรู้ชื่อ; ถ้าไม่รู้ปล่อย None ให้ค้นหา "HDMI" อัตโนมัติ
FORCE_FULLSCREEN = True

# ★★ Fallback (Wayland/Windows/ไม่มี xrandr) ให้ย้ายหน้าต่างด้วยพิกัดเอง ★★
MANUAL_MOVE = False       # ตั้ง True เพื่อใช้ค่าด้านล่าง
MANUAL_X, MANUAL_Y = 1920, 0   # ตัวอย่าง: จอ 2 อยู่ขวา (offset x=1920, y=0)
# ----------------------------------------


# ---------- HDMI Helpers ----------
def _parse_xrandr_for_output(target_name=None):
    """คืนค่า dict {'name','w','h','x','y'} ของจอ HDMI หรือ None"""
    try:
        out = subprocess.check_output(["xrandr", "-q"], text=True)
    except Exception:
        return None

    lines = out.splitlines()

    # ถ้าบังคับชื่อพอร์ตไว้ ลองหาอันนั้นก่อน
    if target_name:
        for line in lines:
            if target_name in line and " connected" in line:
                m = re.search(r"(\d+)x(\d+)\+(\d+)\+(\d+)", line)
                if m:
                    w, h, x, y = map(int, m.groups())
                    return {"name": target_name, "w": w, "h": h, "x": x, "y": y}

    # หาเอาชื่อที่มี HDMI
    for line in lines:
        if "HDMI" in line and " connected" in line:
            name_match = re.match(r"^(\S+)\s+connected", line)
            geo_match  = re.search(r"(\d+)x(\d+)\+(\d+)\+(\d+)", line)
            if name_match and geo_match:
                name = name_match.group(1)
                w, h, x, y = map(int, geo_match.groups())
                return {"name": name, "w": w, "h": h, "x": x, "y": y}
    return None

def place_window_on_hdmi(window_name):
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    info = _parse_xrandr_for_output(FORCE_HDMI_NAME)
    if info:
        cv2.moveWindow(window_name, info["x"], info["y"])
        try:
            cv2.resizeWindow(window_name, info["w"], info["h"])
        except Exception:
            pass
        if FORCE_FULLSCREEN:
            cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        print(f"[INFO] Window -> {info['name']} @ {info['w']}x{info['h']}+{info['x']}+{info['y']}")
    else:
        if MANUAL_MOVE:
            cv2.moveWindow(window_name, MANUAL_X, MANUAL_Y)
            if FORCE_FULLSCREEN:
                cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            print(f"[INFO] Window -> manual position {MANUAL_X},{MANUAL_Y}")
        else:
            print("[WARN] ไม่พบจอ HDMI ด้วย xrandr และ MANUAL_MOVE=False → เปิดบนจอหลัก")
# ----------------------------------


def check_assets():
    ok = True
    for lbl, p in AUDIO_MAP.items():
        if not os.path.isfile(p):
            print(f"[WARN] ไม่พบไฟล์เสียงสำหรับ {lbl}: {p}")
            ok = False
    for lbl, p in ICON_MAP.items():
        if not os.path.isfile(p):
            print(f"[WARN] ไม่พบไฟล์ภาพสำหรับ {lbl}: {p}")
            ok = False
    return ok


def one_shot_test(label: str):
    """เทสครั้งเดียว: เล่นเสียง+โชว์ภาพสำหรับ label ที่ส่งเข้ามา"""
    AO.init_audio(AUDIO_MAP)
    VO.init_visual(ICON_MAP, display_sec=DISPLAY_DURATION_SEC, position="center", max_icon_w=420)

    # บังคับให้หน้าต่างไปจอ HDMI
    place_window_on_hdmi(WINDOW_ONESHOT)

    # ยิงอีเวนต์
    AO.handle_event(label)
    VO.handle_event(label)

    t_end = time.time() + DISPLAY_DURATION_SEC + 0.2
    while time.time() <= t_end:
        frame = np.zeros((FRAME_H, FRAME_W, 3), dtype=np.uint8)
        frame = VO.apply_overlay(frame)
        cv2.putText(frame, f"TEST CLASS: {label}", (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)
        cv2.imshow(WINDOW_ONESHOT, frame)
        if cv2.waitKey(1) & 0xFF == 27:  # ESC
            break
    cv2.destroyAllWindows()


def interactive_mode():
    """โต้ตอบ: 1..5 ยิงคลาสซ้ำได้"""
    AO.init_audio(AUDIO_MAP)
    VO.init_visual(ICON_MAP, display_sec=DISPLAY_DURATION_SEC, position="center", max_icon_w=420)

    label_keys = {
        ord('1'): "Fighting",
        ord('2'): "MiniHeart",
        ord('3'): "ILY",
        ord('4'): "FU",
        ord('5'): "Like",
    }

    print("Interactive Test Mode")
    print("กด 1=Fighting, 2=MiniHeart, 3=ILY, 4=FU, 5=Like, ESC=ออก")

    place_window_on_hdmi(WINDOW_INTERACTIVE)

    while True:
        frame = np.zeros((FRAME_H, FRAME_W, 3), dtype=np.uint8)
        frame = VO.apply_overlay(frame)
        cv2.putText(frame, "Press 1..5 to trigger class, ESC to exit",
                    (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (200, 200, 200), 2)
        cv2.imshow(WINDOW_INTERACTIVE, frame)

        k = cv2.waitKey(15) & 0xFF
        if k == 27:
            break
        if k in label_keys:
            lbl = label_keys[k]
            print(f"-> Trigger: {lbl}")
            AO.handle_event(lbl)
            VO.handle_event(lbl)

    cv2.destroyAllWindows()


if __name__ == "__main__":
    _ = check_assets()
    if len(sys.argv) >= 2:
        label = sys.argv[1]
        valid = set(AUDIO_MAP.keys())
        if label not in valid:
            print(f"[ERROR] label ไม่ถูกต้อง: {label}")
            print(f"ใช้ได้: {sorted(list(valid))}")
            sys.exit(1)
        one_shot_test(label)
    else:
        interactive_mode()
