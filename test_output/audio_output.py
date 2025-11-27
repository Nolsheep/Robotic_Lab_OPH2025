# audio_output.py
import os, time, threading, subprocess

# กันยิงซ้ำถี่
EVENT_COOLDOWN_SEC = 1.5

# ★★ เลือกพอร์ตเสียงตรงนี้ ★★
# - "default"    = อุปกรณ์เสียงเริ่มต้นของระบบ
# - "plughw:1,0" = การ์ด 1 ดีไวซ์ 0 (บ่อยครั้งคือ USB speaker)
# - ดูรายชื่อด้วย: aplay -l  หรือ aplay -L
AUDIO_DEVICE = "plughw:1,0"   # ← เปลี่ยนให้ตรงกับลำโพง USB ของคุณ

_audio_map = {}
_last_play = {}
_lock = threading.Lock()

def init_audio(audio_map: dict):
    """ลงทะเบียนแมปคลาส -> ไฟล์ wav"""
    global _audio_map
    _audio_map = audio_map.copy()

def _play(wav_path: str):
    if not os.path.isfile(wav_path):
        return
    try:
        cmd = ["aplay", "-q"]
        if AUDIO_DEVICE:
            cmd += ["-D", AUDIO_DEVICE]
        cmd += [wav_path]
        subprocess.Popen(cmd)
    except Exception:
        pass

def handle_event(label: str):
    """เรียกเมื่อมีคลาส → เล่นเสียงตามคลาสแบบไม่บล็อก"""
    wav = _audio_map.get(label)
    if not wav:
        return
    now = time.time()
    with _lock:
        last = _last_play.get(label, 0.0)
        if now - last < EVENT_COOLDOWN_SEC:
            return
        _last_play[label] = now
    threading.Thread(target=_play, args=(wav,), daemon=True).start()
