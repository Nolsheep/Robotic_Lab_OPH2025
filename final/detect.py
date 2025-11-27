#!/usr/bin/env python3
import cv2
import mediapipe as mp
import numpy as np
import joblib
import os
import time
import threading
import subprocess
from datetime import datetime
from extract import extract_features

# ============== CONFIG ==============
CAM_INDEX = 0
MIN_DET_CONF = 0.9
MIN_TRK_CONF = 0.6

# ต้องคงเดิมกี่เฟรมจึง “นับว่าเจอจริง”
STABLE_FRAMES_REQUIRED = 5

# พักกี่วินาทีก่อนยิงอีเวนต์เดิมได้อีกครั้ง
EVENT_COOLDOWN_SEC = 2.0

# โชว์ป้ายภาพตามคลาสนานกี่วินาที
DISPLAY_DURATION_SEC = 2.0

# ตำแหน่งวางป้ายภาพ (เลือก: "center" | "top-left" | "top-right" | "bottom-left" | "bottom-right")
BANNER_POSITION = "center"

# แมปคลาส -> ไฟล์เสียง/ภาพ
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
# ====================================

# โหลดโมเดล
model = joblib.load("gesture_model.pkl")
class_labels = ["Fighting", "MiniHeart", "ILY", "FU", "Like"]

# MediaPipe
mp_hands = mp.solutions.hands
mp_draw  = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=MIN_DET_CONF,
                       min_tracking_confidence=MIN_TRK_CONF)

# ---------- Utils ----------
def play_audio_async(wav_path):
    """เล่นเสียงแบบไม่บล็อกด้วย aplay (ALSA)"""
    if not wav_path or not os.path.isfile(wav_path):
        return
    try:
        subprocess.Popen(["aplay", "-q", wav_path])
    except Exception:
        pass

def load_icons_with_alpha(icon_map, target_max_width=380):
    """โหลด PNG (RGBA) ทั้งหมดไว้ในหน่วยความจำ และย่อให้กว้างสุดไม่เกิน target_max_width"""
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
        if w > target_max_width:
            scale = target_max_width / float(w)
            icon = cv2.resize(icon, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_AREA)
        cache[label] = icon
    return cache

def overlay_rgba(base_bgr, rgba_icon, pos="center", margin=20):
    """
    ซ้อน rgba_icon (RGBA) ลงบน base_bgr (BGR) ด้วย alpha
    pos: center | top-left | top-right | bottom-left | bottom-right
    """
    if rgba_icon is None:
        return base_bgr

    if rgba_icon.shape[2] == 3:
        # ไม่มี alpha → แปลงเป็นมี alpha
        bgr = rgba_icon
        alpha = np.ones((bgr.shape[0], bgr.shape[1]), dtype=np.float32) * 255
        rgba_icon = np.dstack([bgr, alpha])

    h_icon, w_icon = rgba_icon.shape[:2]
    h_frame, w_frame = base_bgr.shape[:2]

    # คำนวณตำแหน่งวาง
    if pos == "center":
        x = (w_frame - w_icon) // 2
        y = (h_frame - h_icon) // 2
    elif pos == "top-left":
        x, y = margin, margin
    elif pos == "top-right":
        x, y = w_frame - w_icon - margin, margin
    elif pos == "bottom-left":
        x, y = margin, h_frame - h_icon - margin
    else:  # bottom-right
        x, y = w_frame - w_icon - margin, h_frame - h_icon - margin

    # คลิปขอบเผื่อภาพใหญ่เกินเฟรม
    if x < 0 or y < 0 or x + w_icon > w_frame or y + h_icon > h_frame:
        # ย่อให้พอดีเฟรม
        scale = min(w_frame / float(w_icon), h_frame / float(h_icon)) * 0.95
        new_w, new_h = max(1, int(w_icon * scale)), max(1, int(h_icon * scale))
        rgba_icon = cv2.resize(rgba_icon, (new_w, new_h), interpolation=cv2.INTER_AREA)
        h_icon, w_icon = new_h, new_w
        x = (w_frame - w_icon) // 2
        y = (h_frame - h_icon) // 2

    # แยกช่อง
    b, g, r, a = cv2.split(rgba_icon)
    overlay_rgb = cv2.merge((b, g, r))
    alpha = a.astype(float) / 255.0

    # พื้นที่ที่จะซ้อน
    roi = base_bgr[y:y+h_icon, x:x+w_icon].astype(float)

    # alpha blend
    for c in range(3):
        roi[..., c] = (alpha * overlay_rgb[..., c] + (1 - alpha) * roi[..., c])

    base_bgr[y:y+h_icon, x:x+w_icon] = roi.astype(np.uint8)
    return base_bgr
# --------------------------

# โหลด icon PNG ล่วงหน้า
ICON_CACHE = load_icons_with_alpha(ICON_MAP, target_max_width=420)

# เปิดกล้อง
cap = cv2.VideoCapture(CAM_INDEX)

last_label = None
stable_count = 0
last_event_time = 0.0

# สำหรับจัดการป้ายภาพ
active_banner_label = None
banner_end_time = 0.0

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
            break  # ใช้มือแรกพอ

    # แสดงข้อความเล็ก ๆ มุมภาพ
    if prediction_text:
        cv2.putText(frame, f"Gesture: {prediction_text}", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)

    # Debounce ให้ค่าคงเดิมก่อนยืนยัน
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

    # ถึงเกณฑ์และพ้น cooldown → เล่นเสียง + เปิดป้ายภาพ
    if last_label and stable_count >= STABLE_FRAMES_REQUIRED:
        if (now - last_event_time) >= EVENT_COOLDOWN_SEC:
            # 1) เล่นเสียงตามคลาส
            wav = AUDIO_MAP.get(last_label)
            if wav:
                threading.Thread(target=play_audio_async, args=(wav,), daemon=True).start()

            # 2) ตั้งป้ายภาพให้แสดงช่วงเวลาหนึ่ง
            active_banner_label = last_label
            banner_end_time = now + DISPLAY_DURATION_SEC

            last_event_time = now

    # ถ้าป้ายภาพยังไม่หมดเวลา → ซ้อนภาพ PNG ลงเฟรม
    if active_banner_label and now <= banner_end_time:
        icon_rgba = ICON_CACHE.get(active_banner_label)
        frame = overlay_rgba(frame, icon_rgba, pos=BANNER_POSITION, margin=24)
    else:
        active_banner_label = None  # หมดเวลาแล้ว

    cv2.imshow("Jetson Detection (Image Banner + Speaker Audio)", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
