#!/usr/bin/env python3
import cv2, mediapipe as mp, numpy as np, joblib, time
from extract import extract_features
import audio_output as AO
import visual_output as VO

# -------- CONFIG ----------
CAM_INDEX = 0
MIN_DET_CONF = 0.9
MIN_TRK_CONF = 0.6
STABLE_FRAMES_REQUIRED = 5
EVENT_COOLDOWN_SEC = 2.0

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
# --------------------------

# init outputs
AO.init_audio(AUDIO_MAP)
VO.init_visual(ICON_MAP, display_sec=2.0, position="center", max_icon_w=420)

# model
model = joblib.load("/home/nolsheep/robotic/test2/gesture_model.pkl")
class_labels = ["Fighting", "MiniHeart", "ILY", "FU", "Like"]

# mediapipe
mp_hands = mp.solutions.hands
mp_draw  = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=MIN_DET_CONF,
                       min_tracking_confidence=MIN_TRK_CONF)

cap = cv2.VideoCapture(CAM_INDEX)

last_label = None
stable_count = 0
last_event_time = 0.0

while True:
    ok, frame = cap.read()
    if not ok:
        break

    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    prediction_text = ""

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            keypoints = [[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark]
            if len(keypoints) == 21:
                try:
                    feats = extract_features(keypoints).reshape(1, -1)
                    pred = model.predict(feats)[0]
                    prediction_text = class_labels[pred]
                except Exception:
                    prediction_text = "error"
            break

    if prediction_text:
        cv2.putText(frame, f"Gesture: {prediction_text}", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)

    now = time.time()
    if prediction_text and prediction_text != "error":
        if prediction_text == last_label:
            stable_count += 1
        else:
            last_label = prediction_text
            stable_count = 1
    else:
        last_label = None
        stable_count = 0

    if last_label and stable_count >= STABLE_FRAMES_REQUIRED:
        if (now - last_event_time) >= EVENT_COOLDOWN_SEC:
            # ส่งคลาสไป “ไฟล์เสียง” และ “ไฟล์ภาพ”
            AO.handle_event(last_label)   # → เล่นเสียงตามคลาส (async)
            VO.handle_event(last_label)   # → ตั้งให้โชว์ PNG ตามคลาส
            last_event_time = now

    # ให้ visual module ซ้อน PNG ถ้ายังอยู่ในช่วงเวลาแสดง
    frame = VO.apply_overlay(frame)

    cv2.imshow("Jetson Detection (Image PNG + Speaker Audio)", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
