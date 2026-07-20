"""
services/local_backend.py

STUBS ONLY — not implemented. This file exists to show exactly where
a future GPU-based stack (ComfyUI + FLUX + IP-Adapter, Wan/LTX video)
would plug into the pipeline, without you having to touch main.py,
config.py, or any other service when you're ready to build it.

Note: Piper TTS is no longer a stub here — it has a real
implementation in services/piper_backend.py and is the default voice
backend. This file now only covers the two stages that still don't
have a free/local implementation: true character-locked image
generation (ComfyUI + IP-Adapter) and real AI video generation
(Wan/LTX), as opposed to Pollinations images + MoviePy pan/zoom.

To activate one of these later:
  1. Fill in the method body (usually: call a local HTTP API that
     ComfyUI exposes, or shell out to a CLI tool).
  2. Set the matching backend in config.py, e.g. BACKENDS["image"] = "comfyui"
  3. Nothing else in the codebase changes — services/factory.py already
     knows to route to these classes once selected.
"""

from services.base import ImageService, VideoService


class ComfyUIImageService(ImageService):
    """
    Would call a locally-running ComfyUI server's HTTP API (default
    http://127.0.0.1:8188) with a saved workflow JSON (FLUX.1 Dev +
    IP-Adapter loaded with your character reference image), poll for
    completion, and download the resulting PNG to out_path.
    """

    def __init__(self, comfyui_url="http://127.0.0.1:8188"):
        self.comfyui_url = comfyui_url

    def generate_image(self, prompt: str, out_path: str) -> str:
        raise NotImplementedError(
            "Wire this up to your ComfyUI workflow API once you have "
            "FLUX.1 Dev + IP-Adapter running locally. See "
            "https://github.com/comfyanonymous/ComfyUI for the HTTP API."
        )


class WanVideoService(VideoService):
    """
    Would replace the Ken Burns pan/zoom with a real image-to-video
    model (Wan 2.x or LTX Video) running through ComfyUI, generating a
    genuine 5-second animated clip per scene instead of zooming a
    still image.
    """

    def build_scene(self, image_path: str, audio_path: str, words: list):
        raise NotImplementedError(
            "Wire this up to a Wan/LTX image-to-video ComfyUI workflow. "
            "Keep the same signature so main.py doesn't need to change."
        )

    def assemble(self, scene_clips: list, out_path: str) -> str:
        raise NotImplementedError(
            "Once scene clips are real video files instead of MoviePy "
            "clip objects, this becomes an FFmpeg concat + mux step."
        )
