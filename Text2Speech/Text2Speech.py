#!/usr/bin/env python3
from gtts import gTTS
from pydub import AudioSegment
import os

os.makedirs("mp3", exist_ok=True)
os.makedirs("audio", exist_ok=True)

texts = {
    "สู้ๆ นะครับ": "Fighting.wav",
    "ชูหา พ่อ หรอ งับฟู่วววว": "FU.wav",
    "ชอบเลย": "Like.wav",
    "I Love You": "MiniHeart.wav",
    "Rock Star": "ILY.wav"
}

for text, filename in texts.items():
    mp3_path = f"mp3/{filename.replace('.wav', '.mp3')}"
    tts = gTTS(text=text, lang='th')
    tts.save(mp3_path)

    wav_path = f"audio/{filename}"
    sound = AudioSegment.from_mp3(mp3_path)
    sound.export(wav_path, format="wav")

    print(f"{wav_path}")
