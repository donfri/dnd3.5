"""Server-side narration using Piper, a free, offline neural text-to-speech engine.

Browser speech (the Web Speech API) relies on each computer's built-in voices,
and some of them (notably macOS) click or pop at sentence boundaries. Generating
the audio on the server gives every player the same clean voice.

Piper is optional. If it isn't installed or no voice models are found, the
web page falls back to the browser's own voices.

Voices are .onnx files plus .onnx.json configs in PIPER_VOICE_DIR
(default: <repo>/voices). The Dockerfile downloads them at build time.
"""
from __future__ import annotations

import hashlib
import io
import os
import threading
import wave
from collections import OrderedDict
from typing import Dict, Optional

VOICE_DIR = os.environ.get("PIPER_VOICE_DIR") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "voices")

# role -> preferred model file names (first one found wins)
ROLES = {
    "gm": ["en_US-ryan-medium", "en_GB-alan-medium", "en_US-lessac-medium"],
    "npc": ["en_GB-alba-medium", "en_US-amy-medium", "en_US-lessac-medium"],
}

_lock = threading.Lock()
_voices: Dict[str, object] = {}
_cache: "OrderedDict[str, bytes]" = OrderedDict()
_CACHE_MAX = 300
_status: Optional[dict] = None


def _find_model(role: str) -> Optional[str]:
    if not os.path.isdir(VOICE_DIR):
        return None
    for name in ROLES[role]:
        path = os.path.join(VOICE_DIR, name + ".onnx")
        if os.path.exists(path) and os.path.exists(path + ".json"):
            return path
    for f in sorted(os.listdir(VOICE_DIR)):  # any voice at all
        if f.endswith(".onnx") and os.path.exists(os.path.join(VOICE_DIR, f + ".json")):
            return os.path.join(VOICE_DIR, f)
    return None


def status() -> dict:
    """Which roles have a server voice available (cached after first check)."""
    global _status
    if _status is None:
        import importlib.util
        ok = importlib.util.find_spec("piper") is not None
        roles = {r: (os.path.basename(_find_model(r))[:-5] if ok and _find_model(r) else None)
                 for r in ROLES}
        _status = {"available": ok and any(roles.values()), "voices": roles}
    return _status


def _voice(role: str):
    with _lock:
        if role in _voices:
            return _voices[role]
        from piper import PiperVoice
        path = _find_model(role)
        if not path:
            raise RuntimeError("no Piper voice installed")
        v = PiperVoice.load(path)
        _voices[role] = v
        return v


def synthesize(text: str, role: str = "gm", speed: float = 1.0) -> bytes:
    """Return WAV bytes for text. Results are cached."""
    role = role if role in ROLES else "gm"
    text = " ".join(str(text).split())[:1500]
    speed = max(0.6, min(1.6, float(speed)))
    key = hashlib.sha1(f"{role}|{speed:.2f}|{text}".encode()).hexdigest()
    with _lock:
        if key in _cache:
            _cache.move_to_end(key)
            return _cache[key]
    from piper import SynthesisConfig
    voice = _voice(role)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        voice.synthesize_wav(text, wf, syn_config=SynthesisConfig(length_scale=1.0 / speed))
    data = buf.getvalue()
    with _lock:
        _cache[key] = data
        while len(_cache) > _CACHE_MAX:
            _cache.popitem(last=False)
    return data


VOICE_URLS = {
    "en_US-ryan-medium": "en/en_US/ryan/medium/en_US-ryan-medium",
    "en_GB-alba-medium": "en/en_GB/alba/medium/en_GB-alba-medium",
}
HF_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main/"


def download_voices(dest: str = VOICE_DIR) -> None:
    """Fetch the default narrator and character voices (about 60 MB each)."""
    import urllib.request
    os.makedirs(dest, exist_ok=True)
    for name, path in VOICE_URLS.items():
        for ext in (".onnx", ".onnx.json"):
            out = os.path.join(dest, name + ext)
            if os.path.exists(out) and os.path.getsize(out) > 0:
                continue
            print(f"downloading {name}{ext} ...", flush=True)
            urllib.request.urlretrieve(HF_BASE + path + ext, out)
    print(f"voices ready in {dest}")


if __name__ == "__main__":
    import sys
    if "--download" in sys.argv:
        download_voices()
    elif "--say" in sys.argv:
        text = " ".join(a for a in sys.argv[1:] if a != "--say") or "The narrator is ready."
        with open("narrator-test.wav", "wb") as f:
            f.write(synthesize(text))
        print("wrote narrator-test.wav")
    else:
        print(status())
