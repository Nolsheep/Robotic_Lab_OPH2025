# audio_output.py
import os, time, threading, subprocess

# ปรับได้
EVENT_COOLDOWN_SEC = 1.5

_audio_map = {}
_last_play = {}
_lock = threading.Lock()

def init_audio(audio_map: dict):
    """audio_map: {"Fighting":"audio/Fighting.wav", ...}"""
    global _audio_map
    _audio_map = audio_map.copy()

def _play(wav_path: str):
    if not os.path.isfile(wav_path):
        return
    try:
        subprocess.Popen(["aplay", "-q", wav_path])  # Jetson/ALSA
    except Exception:
        pass

def handle_event(label: str):
    """เรียกเมื่อ detect เจอคลาส → จะเล่นเสียงตามคลาส (ไม่บล็อกเฟรม)"""
    wav = _audio_map.get(label)
    if not wav:
        return
    now = time.time()
    with _lock:
        last = _last_play.get(label, 0.0)
        if now - last < EVENT_COOLDOWN_SEC:
            return  # ยังไม่พ้นคูลดาวน์
        _last_play[label] = now
    threading.Thread(target=_play, args=(wav,), daemon=True).start()
