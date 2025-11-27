# detect.py
#!/usr/bin/env python3
import os, time, cv2, joblib
import numpy as np
import mediapipe as mp
from extract import extract_features
import audio_output as AO
import visual_output as VO
from hdmi_display import place_on_hdmi

# ---------- CONFIG ----------
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

STABLE_FRAMES_REQUIRED = int(os.environ.get("STABLE_FRAMES", 5))
EVENT_COOLDOWN_SEC = float(os.environ.get("EVENT_COOLDOWN", 2.0))
DISPLAY_DURATION_SEC = float(os.environ.get("DISPLAY_SEC", 2.0))
BANNER_POSITION = os.environ.get("BANNER_POS", "center")  # center/top-left/top-right/bottom-left/bottom-right

# Model / labels
MODEL_PATH = os.environ.get("MODEL_PATH", "gesture_model.pkl")
CLASS_LABELS = ["Fighting", "MiniHeart", "ILY", "FU", "Like"]

# MediaPipe conf
MIN_DET_CONF = float(os.environ.get("MP_DET", 0.9))
MIN_TRK_CONF = float(os.environ.get("MP_TRK", 0.6))

# HDMI window
WINDOW_NAME = os.environ.get("WIN_NAME", "Jetson Detection (Image Banner + Speaker Audio)")

# Camera config (USB / CSI)
CAMERA_TYPE = os.environ.get("CAMERA_TYPE", "USB").upper()  # "USB" | "CSI"
CAM_INDEX = int(os.environ.get("CAM_INDEX", 0))             # for USB
CSI_SENSOR_ID = int(os.environ.get("CSI_ID", 0))            # for CSI
CSI_W = int(os.environ.get("CSI_W", 1280))
CSI_H = int(os.environ.get("CSI_H", 720))
CSI_FPS = int(os.environ.get("CSI_FPS", 30))
# ---------------------------------

def open_camera():
    if CAMERA_TYPE == "CSI":
        gst = (
            f"nvarguscamerasrc sensor-id={CSI_SENSOR_ID} ! "
            f"video/x-raw(memory:NVMM), width={CSI_W}, height={CSI_H}, "
            f"framerate={CSI_FPS}/1, format=NV12 ! "
            f"nvvidconv ! video/x-raw, format=BGRx ! videoconvert ! appsink"
        )
        return cv2.VideoCapture(gst, cv2.CAP_GSTREAMER)
    else:
        cap = cv2.VideoCapture(CAM_INDEX)
        # optional: try set resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, CSI_W)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CSI_H)
        cap.set(cv2.CAP_PROP_FPS, CSI_FPS)
        return cap

def main():
    # init outputs
    AO.init_audio(AUDIO_MAP)
    VO.init_visual(ICON_MAP, display_sec=DISPLAY_DURATION_SEC, position=BANNER_POSITION, max_icon_w=480)

    # model
    model = joblib.load(MODEL_PATH)

    # mediapipe
    mp_hands = mp.solutions.hands
    mp_draw  = mp.solutions.drawing_utils
    hands = mp_hands.Hands(min_detection_confidence=MIN_DET_CONF,
                           min_tracking_confidence=MIN_TRK_CONF)

    cap = open_camera()
    if not cap or not cap.isOpened():
        print("[ERROR] cannot open camera")
        return

    # HDMI window
    place_on_hdmi(WINDOW_NAME)

    last_label = None
    stable_count = 0
    last_event_time = 0.0
    active_banner_label = None
    banner_end_time = 0.0

    while True:
        ok, frame = cap.read()
        if not ok:
            print("[WARN] camera read failed")
            break

        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)

        prediction_text = ""
        if results.multi_hand_landmarks:
            # ใช้มือตรวจเจอ “มือแรก”
            hand_landmarks = results.multi_hand_landmarks[0]
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            keypoints = [[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark]
            if len(keypoints) == 21:
                try:
                    feats = extract_features(keypoints).reshape(1, -1)
                    pred = model.predict(feats)[0]
                    prediction_text = CLASS_LABELS[pred]
                except Exception as e:
                    prediction_text = "Default"

        if prediction_text:
            cv2.putText(frame, f"Gesture: {prediction_text}", (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)

        # Debounce
        now = time.time()
        if prediction_text and prediction_text != "Default":
            if prediction_text == last_label:
                stable_count += 1
            else:
                last_label = prediction_text
                stable_count = 1
        else:
            last_label = None
            stable_count = 0

        # Trigger event
        if last_label and stable_count >= STABLE_FRAMES_REQUIRED:
            if (now - last_event_time) >= EVENT_COOLDOWN_SEC:
                # เสียง
                AO.handle_event(last_label)
                # ภาพ (ป้าย PNG)
                active_banner_label = last_label
                banner_end_time = now + DISPLAY_DURATION_SEC
                last_event_time = now

        # วาดป้าย PNG ถ้ายังอยู่ในเวลา
        if active_banner_label and now <= banner_end_time:
            frame = VO.apply_overlay(frame)
        else:
            active_banner_label = None

        cv2.imshow(WINDOW_NAME, frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
