# test_output.py
#!/usr/bin/env python3
import sys, time, cv2, numpy as np, os
import audio_output as AO
import visual_output as VO
from hdmi_display import place_on_hdmi

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
WIN_ONE = "Test Output (No Detect)"
WIN_INT  = "Test Output (Interactive)"

def check_assets():
    ok = True
    for lbl, p in AUDIO_MAP.items():
        if not os.path.isfile(p):
            print(f"[WARN] missing audio for {lbl}: {p}"); ok = False
    for lbl, p in ICON_MAP.items():
        if not os.path.isfile(p):
            print(f"[WARN] missing icon for {lbl}: {p}"); ok = False
    return ok

def one_shot_test(label: str):
    AO.init_audio(AUDIO_MAP)
    VO.init_visual(ICON_MAP, display_sec=DISPLAY_DURATION_SEC, position="center", max_icon_w=480)

    place_on_hdmi(WIN_ONE)

    AO.handle_event(label)
    VO.handle_event(label)

    t_end = time.time() + DISPLAY_DURATION_SEC + 0.3
    while time.time() <= t_end:
        frame = np.zeros((FRAME_H, FRAME_W, 3), dtype=np.uint8)
        frame = VO.apply_overlay(frame)
        cv2.putText(frame, f"TEST CLASS: {label}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,255,0), 2)
        cv2.imshow(WIN_ONE, frame)
        if cv2.waitKey(1) & 0xFF == 27: break
    cv2.destroyAllWindows()

def interactive_mode():
    AO.init_audio(AUDIO_MAP)
    VO.init_visual(ICON_MAP, display_sec=DISPLAY_DURATION_SEC, position="center", max_icon_w=480)

    key2label = {ord('1'):"Fighting", ord('2'):"MiniHeart", ord('3'):"ILY", ord('4'):"FU", ord('5'):"Like"}
    print("Interactive Mode: 1=Fighting, 2=MiniHeart, 3=ILY, 4=FU, 5=Like, ESC=ออก")

    place_on_hdmi(WIN_INT)

    while True:
        frame = np.zeros((FRAME_H, FRAME_W, 3), dtype=np.uint8)
        frame = VO.apply_overlay(frame)
        cv2.putText(frame, "Press 1..5 to trigger class, ESC to exit", (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (200,200,200), 2)
        cv2.imshow(WIN_INT, frame)
        k = cv2.waitKey(15) & 0xFF
        if k == 27: break
        if k in key2label:
            lbl = key2label[k]
            print("->", lbl)
            AO.handle_event(lbl)
            VO.handle_event(lbl)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    _ = check_assets()
    if len(sys.argv) >= 2:
        label = sys.argv[1]
        valid = set(AUDIO_MAP.keys())
        if label not in valid:
            print(f"[ERROR] invalid label: {label}\nvalid: {sorted(list(valid))}")
            sys.exit(1)
        one_shot_test(label)
    else:
        interactive_mode()
