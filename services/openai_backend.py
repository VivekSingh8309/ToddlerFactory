"""
services/openai_backend.py

Concrete implementations of every service interface, backed entirely
by the OpenAI API. This is today's default backend — everything you
already had working (GPT-4o, gpt-image-1, TTS, Whisper) just
reorganized behind the interfaces in services/base.py.
"""

import json
import base64
from openai import OpenAI

import config
from services.base import StoryService, ImageService, VoiceService, SubtitleService


class OpenAIStoryService(StoryService):
    def __init__(self):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)

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
            "- Return ONLY valid JSON, no markdown fences, no commentary."
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
    // exactly {config.SCENES_PER_EPISODE} scenes total
  ]
}}

Episode setup:
- Main character: {char['description']}
- Setting: {combo['location']}
- Main activity: {combo['activity']}
- Educational focus: {combo['theme']}

Beginning (greeting), middle (activity + educational moment), end
(warm goodbye using the signature phrase). Total narration should read
aloud in about 30-45 seconds.
"""

    def generate_episode(self, combo: dict) -> dict:
        response = self.client.chat.completions.create(
            model=config.STORY_MODEL,
            messages=[
                {"role": "system", "content": self._system_prompt()},
                {"role": "user", "content": self._user_prompt(combo)},
            ],
            temperature=0.9,
            response_format={"type": "json_object"},
        )
        episode = json.loads(response.choices[0].message.content)
        episode["_combo"] = combo
        return episode


class OpenAIImageService(ImageService):
    def __init__(self):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)

    def generate_image(self, prompt: str, out_path: str) -> str:
        result = self.client.images.generate(
            model=config.IMAGE_MODEL,
            prompt=prompt,
            size="1024x1536",
            n=1,
        )
        image_bytes = base64.b64decode(result.data[0].b64_json)
        with open(out_path, "wb") as f:
            f.write(image_bytes)
        return out_path


class OpenAIVoiceService(VoiceService):
    def __init__(self):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)

    def synthesize(self, text: str, out_path: str) -> str:
        response = self.client.audio.speech.create(
            model=config.TTS_MODEL,
            voice=config.TTS_VOICE,
            input=text,
            speed=0.9,
        )
        response.stream_to_file(out_path)
        return out_path


class OpenAISubtitleService(SubtitleService):
    def __init__(self):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)

    def get_word_timestamps(self, audio_path: str) -> list:
        with open(audio_path, "rb") as f:
            transcript = self.client.audio.transcriptions.create(
                model=config.STT_MODEL,
                file=f,
                response_format="verbose_json",
                timestamp_granularities=["word"],
            )
        return [
            {"word": w.word, "start": w.start, "end": w.end}
            for w in transcript.words
        ]
