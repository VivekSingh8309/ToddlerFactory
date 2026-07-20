"""
config.py
Character bible + story building blocks.

Keeping character descriptions IDENTICAL every time they're used in an
image prompt is the #1 trick for visual consistency without needing
IP-Adapter / LoRA. Never paraphrase these strings — reuse verbatim.
"""

import os

# ── OpenAI (optional — only needed if you switch a backend to "openai") ─
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
STORY_MODEL = "gpt-4o"
IMAGE_MODEL = "gpt-image-1"     # falls back to "dall-e-3" if unavailable
TTS_MODEL = "tts-1"
TTS_VOICE = "alloy"             # alloy, nova, shimmer, echo, fable, onyx
STT_MODEL = "whisper-1"

# ── Ollama (default story backend — local, free, no API key) ──────────
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")

# ── Pollinations (default image backend — free, no API key) ───────────
POLLINATIONS_ENDPOINT = os.environ.get(
    "POLLINATIONS_ENDPOINT", "https://image.pollinations.ai/prompt"
)

# ── Piper (default voice backend — local, free, no API key) ───────────
# Path to a downloaded .onnx voice model (its .onnx.json must sit next
# to it). See services/piper_backend.py for where to get one.

PIPER_MODEL = os.path.join(
    "assets",
    "voices",
    "en_US-lessac-medium.onnx",
)

# ── faster-whisper (default subtitle backend — local, free) ───────────
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "base")
WHISPER_DEVICE = os.environ.get("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.environ.get("WHISPER_COMPUTE_TYPE", "int8")

# ── Visual style locked across every episode ────────────────────────
ART_STYLE = (
    "soft 3D Pixar-style children's cartoon illustration, warm pastel "
    "lighting, rounded friendly shapes, clean simple background, "
    "high quality, toddler-safe, no text in image"
)

# Extra tags appended to every image prompt to steer the free/open
# image model toward safe, consistent, toddler-appropriate output.
# Kept separate from ART_STYLE so the two can be tuned independently.
IMAGE_QUALITY_TAGS = (
    "vibrant vivid colors, vertical 9:16 portrait composition, "
    "clean uncluttered background, no text, no letters, no words, "
    "no watermark, safe and appropriate for toddlers ages 2-5, "
    "consistent character design across scenes"
)

# ── Character bible ──────────────────────────────────────────────────
# Reuse `description` verbatim in every image prompt that includes this
# character. Do not vary the wording between scenes.
CHARACTERS = {
    "piko": {
        "name": "Piko the Bunny",
        "description": (
            "Piko, a small white bunny rabbit with big round brown eyes, "
            "a light blue shirt, floppy ears, and brown shoes, always "
            "smiling"
        ),
    },
    "lumi": {
        "name": "Lumi the Bird",
        "description": (
            "Lumi, a tiny yellow bird with fluffy round feathers, a "
            "small orange beak, and big friendly eyes"
        ),
    },
}

LOCATIONS = [
    "a sunny forest meadow",
    "a quiet sandy beach",
    "a soft fluffy cloud in the sky",
    "a colorful rainbow clearing",
    "a cozy farm with a red barn",
    "a gentle snowy hill",
    "a green jungle with big leaves",
    "a starry moon garden",
]

ACTIVITIES = [
    "jumping happily",
    "counting shiny objects",
    "dancing together",
    "finding a hidden treasure",
    "singing a cheerful song",
    "sharing a snack with a friend",
    "painting a picture",
    "helping a friend carry something",
]

EDUCATIONAL_THEMES = [
    "colors",
    "counting numbers",
    "shapes",
    "animal sounds",
    "the alphabet",
    "naming emotions",
    "kindness",
    "sharing",
]

# ── Backend selection ────────────────────────────────────────────────
# Which concrete implementation backs each stage of the pipeline.
# Defaults are all free/local — no paid API key required. Override any
# of these via env var to swap backends, e.g.:
#   export IMAGE_BACKEND=openai
# Valid values today:
#   story:    ollama (default) | openai
#   image:    pollinations (default) | openai | comfyui (stub)
#   voice:    piper (default) | openai
#   subtitle: faster_whisper (default) | openai
#   video:    moviepy (default) | wan (stub)
BACKENDS = {
    "story": os.environ.get("STORY_BACKEND", "ollama"),
    "image": os.environ.get("IMAGE_BACKEND", "pollinations"),
    "voice": os.environ.get("VOICE_BACKEND", "piper"),
    "subtitle": os.environ.get("SUBTITLE_BACKEND", "faster_whisper"),
    "video": os.environ.get("VIDEO_BACKEND", "moviepy"),
}

# ── Episode structure ────────────────────────────────────────────────
SCENES_PER_EPISODE = 6      # ~5 seconds of narration each -> ~30-45s reel
SIGNATURE_PHRASE = "Tiny hands, big hearts!"

# ── Folders ──────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIRS = {
    "stories": os.path.join(BASE_DIR, "output", "stories"),
    "images": os.path.join(BASE_DIR, "output", "images"),
    "audio": os.path.join(BASE_DIR, "output", "audio"),
    "captions": os.path.join(BASE_DIR, "output", "captions"),
    "music": os.path.join(BASE_DIR, "assets", "music"),
    "final": os.path.join(BASE_DIR, "output", "final"),
}
for path in DIRS.values():
    os.makedirs(path, exist_ok=True)
