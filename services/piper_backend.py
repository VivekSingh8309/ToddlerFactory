"""
services/piper_backend.py

VoiceService implementation using Piper, an offline neural TTS engine.
No API key, no per-call cost, runs entirely on your machine (CPU is
fine — Piper is small and fast).

Prerequisite:
    1. pip install piper-tts
    2. Download a voice model (.onnx + .onnx.json pair) from
       https://github.com/rhasspy/piper/blob/master/VOICES.md
       e.g. en_US-lessac-medium.onnx + en_US-lessac-medium.onnx.json
       (both files must sit in the same folder)
    3. Point config.PIPER_MODEL at the .onnx file's path.

Note on file format: Piper produces WAV audio. This writes real WAV
bytes to out_path even though main.py names that path with a .mp3
extension. That's not a bug — MoviePy reads audio through ffmpeg,
which sniffs the actual file format from its contents, not its
extension, so downstream steps (captioning, video assembly) work
unmodified. If you want a byte-for-byte real .mp3 on disk, pipe the
output through an extra ffmpeg conversion step.

Method signature matches services.base.VoiceService exactly, so
services/factory.py can swap this in for OpenAIVoiceService with no
changes anywhere else in the pipeline.
"""

import wave

import config
from services.base import VoiceService

_voice_cache = {}


def _load_voice(model_path):
    """Loading a Piper voice model is slow-ish; cache it across calls
    within the same process instead of reloading per scene."""
    if model_path not in _voice_cache:
        from piper import PiperVoice  # deferred import, only needed here
        _voice_cache[model_path] = PiperVoice.load(model_path)
    return _voice_cache[model_path]


class PiperVoiceService(VoiceService):
    def __init__(self, model_path=None):
        self.model_path = model_path or config.PIPER_MODEL
        self.voice = _load_voice(self.model_path)

    import wave
    def synthesize(self, text: str, out_path: str) -> str:
        with wave.open(out_path, "wb") as wav_file:
            self.voice.synthesize_wav(
            text=text,
            wav_file=wav_file,
            set_wav_format=True
        )

        return out_path
