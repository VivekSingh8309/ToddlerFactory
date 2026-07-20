"""
services/whisper_backend.py

SubtitleService implementation using faster-whisper, an offline
reimplementation of OpenAI's Whisper model (CTranslate2-based, fast
even on CPU for clips this short). No API key, no per-call cost.

Prerequisite:
    pip install faster-whisper

The model weights (e.g. "base") download automatically on first use
and are cached locally afterward — no manual download step needed.

Method signature matches services.base.SubtitleService exactly, so
services/factory.py can swap this in for OpenAISubtitleService with no
changes anywhere else in the pipeline.
"""

import config
from services.base import SubtitleService

_model_cache = {}


def _load_model():
    """Loading the Whisper model is the slow part; cache it across
    calls within the same process instead of reloading per scene."""
    key = (config.WHISPER_MODEL, config.WHISPER_DEVICE, config.WHISPER_COMPUTE_TYPE)
    if key not in _model_cache:
        from faster_whisper import WhisperModel  # deferred import
        _model_cache[key] = WhisperModel(
            config.WHISPER_MODEL,
            device=config.WHISPER_DEVICE,
            compute_type=config.WHISPER_COMPUTE_TYPE,
        )
    return _model_cache[key]


class FasterWhisperSubtitleService(SubtitleService):
    def __init__(self):
        self.model = _load_model()

    def get_word_timestamps(self, audio_path: str) -> list:
        segments, _info = self.model.transcribe(audio_path, word_timestamps=True)
        words = []
        for segment in segments:
            for word in segment.words:
                words.append(
                    {
                        "word": word.word,
                        "start": word.start,
                        "end": word.end,
                    }
                )
        return words
