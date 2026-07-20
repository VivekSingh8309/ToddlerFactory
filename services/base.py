"""
services/base.py

Abstract interfaces for every stage of the pipeline. Nothing in main.py
or in any other service should ever import a concrete implementation
(OpenAI, ComfyUI, Piper, etc) directly — everything talks to these
interfaces. That's the whole point of the layer: swap the concrete
class in services/factory.py and nothing else in the codebase changes.

Each interface takes and returns plain Python types (str, dict, list,
file paths) rather than provider-specific objects, so a swap never
leaks provider details into the rest of the pipeline.
"""

from abc import ABC, abstractmethod


class StoryService(ABC):
    @abstractmethod
    def generate_episode(self, combo: dict) -> dict:
        """
        combo: {"character": str, "location": str, "activity": str, "theme": str}
        returns: {"title": str, "character": str, "theme": str,
                  "scenes": [{"scene_number": int, "narration": str,
                              "image_prompt": str}, ...]}
        """
        raise NotImplementedError


class ImageService(ABC):
    @abstractmethod
    def generate_image(self, prompt: str, out_path: str) -> str:
        """
        Renders one image to out_path and returns out_path.
        `prompt` is already the fully-built prompt (character
        description + scene description + style), assembled by the
        caller — this method just needs to render it.
        """
        raise NotImplementedError


class VoiceService(ABC):
    @abstractmethod
    def synthesize(self, text: str, out_path: str) -> str:
        """
        Renders narration audio for `text` to out_path (mp3/wav) and
        returns out_path.
        """
        raise NotImplementedError


class SubtitleService(ABC):
    @abstractmethod
    def get_word_timestamps(self, audio_path: str) -> list:
        """
        Returns [{"word": str, "start": float, "end": float}, ...]
        for the given audio file.
        """
        raise NotImplementedError


class VideoService(ABC):
    @abstractmethod
    def build_scene(self, image_path: str, audio_path: str, words: list):
        """
        Returns a single scene clip (a MoviePy clip object today; if
        you swap to a real video-generation backend later, this is
        the method that would call e.g. an image-to-video model
        instead of doing a pan/zoom on a still image).
        """
        raise NotImplementedError

    @abstractmethod
    def assemble(self, scene_clips: list, out_path: str) -> str:
        """
        Concatenates scene clips, adds music, exports final video to
        out_path, and returns out_path.
        """
        raise NotImplementedError
