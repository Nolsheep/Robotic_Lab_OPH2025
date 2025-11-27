#!/usr/bin/env python3
from gtts import gTTS
from pydub import AudioSegment

text = "ชอบเลยอ่ะ"

tts = gTTS(text=text, lang='th')
tts.save("temp.mp3")  

sound = AudioSegment.from_mp3("temp.mp3")
sound.export("Like.wav", format="wav")

print("บันทึกเสียงเป็นไฟล์ .wav เรียบร้อยแล้ว")
