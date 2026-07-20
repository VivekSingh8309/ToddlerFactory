"""
pipeline_utils.py

Small helpers used by main.py that aren't tied to any one backend, so
they don't belong inside services/ — they're pipeline-level logic, not
provider logic.
"""

import random
import config


def pick_random_combo():
    character_key = random.choice(list(config.CHARACTERS.keys()))
    return {
        "character": character_key,
        "location": random.choice(config.LOCATIONS),
        "activity": random.choice(config.ACTIVITIES),
        "theme": random.choice(config.EDUCATIONAL_THEMES),
    }


def build_image_prompt(scene_image_prompt: str, character_key: str) -> str:
    """
    Always reuses the exact character description string from the
    character bible (see config.CHARACTERS) — this is what keeps a
    character visually consistent across scenes without needing
    IP-Adapter/LoRA. Don't paraphrase this at the call site.

    Combines, in order: character description -> scene description ->
    locked art style -> toddler-safe/vertical/vibrant quality tags.
    Everything here is pulled from config.py, nothing is hardcoded, so
    tuning the look of the whole series only ever means editing
    config.ART_STYLE / config.IMAGE_QUALITY_TAGS in one place.
    """
    character_desc = config.CHARACTERS[character_key]["description"]
    return (
        f"{character_desc}. {scene_image_prompt}. "
        f"Style: {config.ART_STYLE}. {config.IMAGE_QUALITY_TAGS}."
    )
