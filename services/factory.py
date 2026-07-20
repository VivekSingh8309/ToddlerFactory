"""
services/factory.py

The single place that knows which concrete implementation backs each
interface. main.py (and everything else) only ever calls
get_services() and talks to the returned objects through their
abstract interface — it never imports a concrete backend module
directly.

All backends are imported lazily, inside each _build_* function, so
installing (or not installing) any one provider's package (openai,
piper-tts, faster-whisper, ...) only matters if you actually select
that backend. The default backends require no paid API key.

To switch a stage to a different backend, change config.BACKENDS (or
set the matching env var) — nothing else in the codebase changes.
"""

import config


def _build_story_service():
    backend = config.BACKENDS["story"]
    if backend == "ollama":
        from services.ollama_backend import OllamaStoryService
        return OllamaStoryService()
    if backend == "openai":
        from services.openai_backend import OpenAIStoryService
        return OpenAIStoryService()
    raise ValueError(f"Unknown story backend: {backend}")


def _build_image_service():
    backend = config.BACKENDS["image"]
    if backend == "pollinations":
        from services.pollinations_backend import PollinationsImageService
        return PollinationsImageService()
    if backend == "openai":
        from services.openai_backend import OpenAIImageService
        return OpenAIImageService()
    if backend == "comfyui":
        from services.local_backend import ComfyUIImageService
        return ComfyUIImageService()
    raise ValueError(f"Unknown image backend: {backend}")


def _build_voice_service():
    backend = config.BACKENDS["voice"]
    if backend == "piper":
        from services.piper_backend import PiperVoiceService
        return PiperVoiceService()
    if backend == "openai":
        from services.openai_backend import OpenAIVoiceService
        return OpenAIVoiceService()
    raise ValueError(f"Unknown voice backend: {backend}")


def _build_subtitle_service():
    backend = config.BACKENDS["subtitle"]
    if backend == "faster_whisper":
        from services.whisper_backend import FasterWhisperSubtitleService
        return FasterWhisperSubtitleService()
    if backend == "openai":
        from services.openai_backend import OpenAISubtitleService
        return OpenAISubtitleService()
    raise ValueError(f"Unknown subtitle backend: {backend}")


def _build_video_service():
    backend = config.BACKENDS["video"]
    if backend == "moviepy":
        from services.moviepy_backend import MoviePyVideoService
        return MoviePyVideoService()
    if backend == "wan":
        from services.local_backend import WanVideoService
        return WanVideoService()
    raise ValueError(f"Unknown video backend: {backend}")


def get_services():
    """
    Returns a dict of ready-to-use service instances:
      {"story": StoryService, "image": ImageService,
       "voice": VoiceService, "subtitle": SubtitleService,
       "video": VideoService}
    """
    return {
        "story": _build_story_service(),
        "image": _build_image_service(),
        "voice": _build_voice_service(),
        "subtitle": _build_subtitle_service(),
        "video": _build_video_service(),
    }
