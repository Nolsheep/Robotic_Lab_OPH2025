#!/usr/bin/env python3
import cv2
import mediapipe as mp
import numpy as np
import joblib
from extract import extract_features

model = joblib.load("/home/nolsheep/robotic/test1/gesture_model.pkl")
class_labels = ["Fighting", "MiniHeart", "ILY", "FU", "Like"]

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.9, min_tracking_confidence=0.6)

cap = cv2.VideoCapture(0)

while True:
    success, img = cap.read()
    if not success:
        break

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    prediction_text = ""

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            keypoints = [[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark]
            if len(keypoints) == 21:
                try:
                    features = extract_features(keypoints).reshape(1, -1)
                    prediction = model.predict(features)[0]
                    prediction_text = class_labels[prediction]
                except Exception as e:
                    prediction_text = "error"
            break

    if prediction_text:
        cv2.putText(img, f"Gesture: {prediction_text}", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)

    cv2.imshow("Test Gesture Model", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()