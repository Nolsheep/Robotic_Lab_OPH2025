# audio_output.py
import os, time, threading, subprocess, shutil
from pathlib import Path

EVENT_COOLDOWN_SEC = 1.0

# ★ ตั้งพอร์ตเสียง (หรือใช้ ENV: AUDIO_DEVICE) ★
# ตัวอย่าง: "plughw:1,0" (USB ลำโพงพบบ่อย), หรือ "default"
AUDIO_DEVICE = os.environ.get("AUDIO_DEVICE", "plughw:1,0")

_AUDIO_MAP = {}
_LAST_PLAY = {}
_LOCK = threading.Lock()
DEBUG = os.environ.get("AUDIO_DEBUG", "0") == "1"

def _abs(p: str) -> str:
    return str((Path(__file__).parent / p).resolve())

def init_audio(audio_map: dict):
    global _AUDIO_MAP
    _AUDIO_MAP = {k: _abs(v) for k, v in audio_map.items()}
    if DEBUG:
        print(f"[audio] device={AUDIO_DEVICE}")
        print(f"[audio] map={_AUDIO_MAP}")

def _try_aplay(wav_path: str) -> bool:
    if shutil.which("aplay") is None:
        if DEBUG: print("[audio] aplay not found")
        return False
    cmd = ["aplay", "-q"]
    if AUDIO_DEVICE:
        cmd += ["-D", AUDIO_DEVICE]
    cmd += [wav_path]
    try:
        subprocess.Popen(cmd)
        if DEBUG: print("[audio] aplay ->", " ".join(cmd))
        return True
    except Exception as e:
        if DEBUG: print("[audio] aplay error:", e)
        return False

def _try_paplay(wav_path: str) -> bool:
    if shutil.which("paplay") is None:
        if DEBUG: print("[audio] paplay not found")
        return False
    cmd = ["paplay", wav_path]
    try:
        subprocess.Popen(cmd)
        if DEBUG: print("[audio] paplay ->", " ".join(cmd))
        return True
    except Exception as e:
        if DEBUG: print("[audio] paplay error:", e)
        return False

def _play(wav_path: str):
    if not os.path.isfile(wav_path):
        if DEBUG: print("[audio] file not found:", wav_path)
        return
    if not _try_aplay(wav_path):
        _try_paplay(wav_path)

def handle_event(label: str):
    wav = _AUDIO_MAP.get(label)
    if not wav:
        if DEBUG: print("[audio] label not in map:", label)
        return
    now = time.time()
    with _LOCK:
        last = _LAST_PLAY.get(label, 0.0)
        if now - last < EVENT_COOLDOWN_SEC:
            return
        _LAST_PLAY[label] = now
    threading.Thread(target=_play, args=(wav,), daemon=True).start()
