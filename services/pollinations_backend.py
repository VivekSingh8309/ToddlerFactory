"""
services/pollinations_backend.py

ImageService implementation using Pollinations AI's free public image
generation endpoint (https://pollinations.ai). No API key, no signup,
no cost. A plain GET request to a URL-encoded prompt returns image
bytes directly.

Method signature matches services.base.ImageService exactly, so
services/factory.py can swap this in for OpenAIImageService with no
changes anywhere else in the pipeline.
"""

import urllib.parse
import requests

import config
from services.base import ImageService


class PollinationsImageService(ImageService):
    def __init__(self, endpoint=None, width=1024, height=1536):
        self.endpoint = (endpoint or config.POLLINATIONS_ENDPOINT).rstrip("/")
        # 1024x1536 keeps the same vertical 2:3-ish aspect used by the
        # original gpt-image-1 calls, good for Shorts/Reels cropping.
        self.width = width
        self.height = height

    def generate_image(self, prompt: str, out_path: str) -> str:
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"{self.endpoint}/{encoded_prompt}"
        params = {
            "width": self.width,
            "height": self.height,
            "nologo": "true",
        }

        response = requests.get(url, params=params, timeout=120)
        response.raise_for_status()

        with open(out_path, "wb") as f:
            f.write(response.content)

        return out_path
