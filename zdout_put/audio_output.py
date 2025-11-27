# audio_output.py
import os, time, threading, subprocess, shutil
from pathlib import Path

EVENT_COOLDOWN_SEC = 1.0

# ★ ตั้งพอร์ตเสียงที่นี่ (หรือใช้ env: AUDIO_DEVICE)
#   ตัวอย่าง: "plughw:1,0" (USB speaker พบบ่อย), หรือปล่อยว่าง "" ให้ใช้ default
AUDIO_DEVICE = os.environ.get("AUDIO_DEVICE", "plughw:3,0")


_AUDIO_MAP = {}
_LAST_PLAY = {}
_LOCK = threading.Lock()
DEBUG = True  # เปิด log วินิจฉัย

def _abs(p: str) -> str:
    """คืน path แบบ absolute อิงจากโฟลเดอร์ไฟล์นี้"""
    return str((Path(__file__).parent / p).resolve())

def init_audio(audio_map: dict):
    """ลงทะเบียนแมปคลาส -> ไฟล์ wav (เก็บเป็น absolute path)"""
    global _AUDIO_MAP
    _AUDIO_MAP = {k: _abs(v) for k, v in audio_map.items()}
    if DEBUG:
        print(f"[audio] map: {_AUDIO_MAP}")
        print(f"[audio] device: {AUDIO_DEVICE}")

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
        if DEBUG: print(f"[audio] aplay spawn: {' '.join(cmd)}")
        return True
    except Exception as e:
        if DEBUG: print(f"[audio] aplay error: {e}")
        return False

def _try_paplay(wav_path: str) -> bool:
    if shutil.which("paplay") is None:
        if DEBUG: print("[audio] paplay not found")
        return False
    # ใช้ PulseAudio/PipeWire sink ผ่าน env PULSE_SINK ได้ถ้าตั้งไว้
    cmd = ["paplay", wav_path]
    try:
        subprocess.Popen(cmd)
        if DEBUG: print(f"[audio] paplay spawn: {' '.join(cmd)}")
        return True
    except Exception as e:
        if DEBUG: print(f"[audio] paplay error: {e}")
        return False

def _play(wav_path: str):
    if not os.path.isfile(wav_path):
        if DEBUG: print(f"[audio] file not found: {wav_path}")
        return
    # ลอง aplay ก่อน → ไม่ได้ค่อย paplay
    if not _try_aplay(wav_path):
        _try_paplay(wav_path)

def handle_event(label: str):
    """เรียกเมื่อมีคลาส → เล่นเสียงตามคลาสแบบไม่บล็อก"""
    wav = _AUDIO_MAP.get(label)
    if not wav:
        if DEBUG: print(f"[audio] label not in map: {label}")
        return
    now = time.time()
    with _LOCK:
        last = _LAST_PLAY.get(label, 0.0)
        if now - last < EVENT_COOLDOWN_SEC:
            return
        _LAST_PLAY[label] = now
    threading.Thread(target=_play, args=(wav,), daemon=True).start()
