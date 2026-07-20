"""
services/ollama_backend.py

StoryService implementation backed by a locally-running Ollama server
instead of the OpenAI API. No API key, no per-call cost, runs entirely
on your machine.

Prerequisite:
    1. Install Ollama: https://ollama.com
    2. Pull a model once:  ollama pull qwen3:4b
    3. Ollama must be running (it starts a local server on
       http://localhost:11434 automatically after install).

Method signature matches services.base.StoryService exactly, so
services/factory.py can swap this in for OpenAIStoryService with no
changes anywhere else in the pipeline.
"""

import json
import requests

import config
from services.base import StoryService


class OllamaStoryService(StoryService):
    def __init__(self, model=None, base_url=None):
        self.model = model or config.OLLAMA_MODEL
        self.base_url = (base_url or config.OLLAMA_URL).rstrip("/")

    def _system_prompt(self):
        return (
            "You write scripts for a toddler (ages 2-5) educational video "
            "series called Tiny Trails. Rules:\n"
            "- Use very short, simple sentences (toddler attention span).\n"
            "- Include gentle pauses and direct participation prompts "
            "('can you clap too?', 'say it with me').\n"
            "- Repeat the signature phrase "
            f"'{config.SIGNATURE_PHRASE}' at least twice.\n"
            "- Absolutely no violence, scary content, or complex vocabulary.\n"
            "- Warm, calm, encouraging tone throughout.\n"
            "- Return ONLY a raw JSON object. No markdown code fences, no "
            "<think> tags, no commentary before or after the JSON."
        )

    def _user_prompt(self, combo):
        char = config.CHARACTERS[combo["character"]]
        return f"""
Create one Tiny Trails episode as JSON with this exact schema:

{{
  "title": "string",
  "character": "{char['name']}",
  "theme": "{combo['theme']}",
  "scenes": [
    {{
      "scene_number": 1,
      "narration": "string (1-2 short sentences)",
      "image_prompt": "string (visual description of this scene ONLY)"
    }}
  ]
}}

The "scenes" array must contain exactly {config.SCENES_PER_EPISODE} scenes,
numbered 1 through {config.SCENES_PER_EPISODE}.

Episode setup:
- Main character: {char['description']}
- Setting: {combo['location']}
- Main activity: {combo['activity']}
- Educational focus: {combo['theme']}

Beginning (greeting), middle (activity + educational moment), end
(warm goodbye using the signature phrase). Total narration should read
aloud in about 30-45 seconds.

Respond with the JSON object only.
"""

    @staticmethod
    def _extract_json(raw_text: str) -> dict:
        """
        Small local models (and reasoning models like qwen3) sometimes
        wrap JSON in stray text or <think>...</think> traces even when
        asked not to. This pulls out the outermost {...} block before
        parsing, so a slightly chatty model doesn't break the pipeline.
        """
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise ValueError(f"No JSON object found in model output:\n{raw_text}")
        return json.loads(raw_text[start : end + 1])

    def generate_episode(self, combo: dict) -> dict:
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self._system_prompt()},
                    {"role": "user", "content": self._user_prompt(combo)},
                ],
                "format": "json",
                "stream": False,
                "options": {"temperature": 0.9},
            },
            timeout=600,
        )
        response.raise_for_status()
        content = response.json()["message"]["content"]
        episode = self._extract_json(content)
        episode["_combo"] = combo
        return episode
