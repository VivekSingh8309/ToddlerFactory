# Tiny Trails Factory

An automated pipeline that produces short toddler-education videos
(colors, counting, kindness, etc.) end to end using a **free/local
default stack** — no paid API key required — behind a service
abstraction layer, so any stage can still be swapped for OpenAI (or a
future GPU-based backend) later without touching the rest of the
codebase.

## Default stack (free, no API key)

| Stage    | Backend                        | Runs where          |
|----------|---------------------------------|----------------------|
| Story    | Ollama (`qwen3:4b`, configurable) | locally, via HTTP  |
| Image    | Pollinations AI                 | free public endpoint |
| Voice    | Piper TTS                       | locally, offline     |
| Subtitle | faster-whisper                  | locally, offline     |
| Video    | MoviePy (Ken Burns pan/zoom)    | locally              |

OpenAI implementations still exist (`services/openai_backend.py`) and
can be selected per-stage via env var if you ever want them — see
"Switching backends" below.

## Pipeline

```
config.py (character bible + story building blocks + backend selection)
        │
        ▼
main.py -----> services/factory.py -----> concrete backend for each stage
        │
        ├── StoryService     (ollama_backend.OllamaStoryService)          [default]
        ├── ImageService      (pollinations_backend.PollinationsImageService) [default]
        ├── VoiceService        (piper_backend.PiperVoiceService)         [default]
        ├── SubtitleService      (whisper_backend.FasterWhisperSubtitleService) [default]
        └── VideoService           (moviepy_backend.MoviePyVideoService)  [default]
        │
        ▼
output/final/episode_XXXX.mp4
```

`main.py` never imports any provider (Ollama's HTTP API, Pollinations,
Piper, faster-whisper, OpenAI, MoviePy) directly — it only calls
`services["story"].generate_episode(...)`,
`services["image"].generate_image(...)`, etc., against the abstract
interfaces in `services/base.py`. `services/factory.py` is the only
file that knows which concrete class backs each interface.

## Setup

### 1. Python environment

```bash
cd toddler_factory
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. FFmpeg (required by MoviePy)

- macOS: `brew install ffmpeg`
- Ubuntu: `sudo apt install ffmpeg`
- Windows: `winget install ffmpeg`, or download from
  https://www.gyan.dev/ffmpeg/builds/ and add its `bin` folder to PATH
- Verify: `ffmpeg -version`

### 3. Ollama (story generation)

- Install from https://ollama.com
- Pull the default model once: `ollama pull qwen3:4b`
- Ollama runs its own local server automatically
  (`http://localhost:11434`) — nothing else to start manually.
- Want a different/smaller model? `export OLLAMA_MODEL=llama3.2:3b`
  (or any model you've pulled).

### 4. Piper (voice narration)

- Already installed via `requirements.txt` (`piper-tts`).
- Download a voice model — a `.onnx` + `.onnx.json` pair — from
  https://github.com/rhasspy/piper/blob/master/VOICES.md
  (e.g. `en_US-lessac-medium.onnx`), keep both files in the same
  folder.
- Point the pipeline at it:
  `export PIPER_MODEL=/full/path/to/en_US-lessac-medium.onnx`

### 5. Pollinations (images)

Nothing to install or configure — it's a public endpoint, called over
plain HTTPS with no key.

### 6. faster-whisper (captions)

Already installed via `requirements.txt`. The model weights (`base` by
default) download automatically the first time it runs and are cached
afterward.

Optional: drop a few royalty-free instrumental loops (mp3) into
`assets/music/` — the video assembler picks one at random per episode
and mixes it under the narration at low volume.

## Run

```bash
python main.py                    # produce 1 episode
python main.py --count 5          # produce 5 episodes in a row
python main.py --count 5 --start 11   # start numbering from episode 11
```

Each run creates, per episode:

- `output/stories/episode_XXXX.json` – the script
- `output/images/episode_XXXX_sceneNN.png` – one image per scene
- `output/audio/episode_XXXX_sceneNN.mp3` – narration per scene (Piper
  writes real WAV bytes into this `.mp3`-named file — MoviePy reads
  audio via ffmpeg, which detects format from content, not extension,
  so this works as-is)
- `output/captions/episode_XXXX_sceneNN.json` – word timings
- `output/final/episode_XXXX.mp4` – the finished vertical video

## Switching backends

Every stage is chosen in `config.BACKENDS`, overridable per env var:

```bash
export STORY_BACKEND=openai       # instead of "ollama"
export IMAGE_BACKEND=openai       # instead of "pollinations"
export VOICE_BACKEND=openai       # instead of "piper"
export SUBTITLE_BACKEND=openai    # instead of "faster_whisper"
```

If you select `openai` for any stage, set `OPENAI_API_KEY` and install
the `openai` package (commented out in `requirements.txt` by default,
since it's not needed for the free path).

## Things to know / tune

- **Story quality**: `qwen3:4b` is small and fast but noticeably less
  capable than GPT-4o at following the JSON schema and toddler-tone
  rules. `services/ollama_backend.py` already strips stray text around
  the JSON to reduce parse failures, but if you see malformed episodes
  often, try a larger local model (`ollama pull qwen3:8b` or similar)
  via `OLLAMA_MODEL`.
- **Image quality/consistency**: Pollinations doesn't offer
  character-locking (no IP-Adapter equivalent) — consistency still
  comes entirely from reusing the same character description string
  every time (see `pipeline_utils.build_image_prompt`, now also
  appending `config.IMAGE_QUALITY_TAGS` for toddler-safe, vertical,
  vibrant, text-free output). Expect more visual drift between scenes
  than a paid model would give you. `services/local_backend.py` has a
  `ComfyUIImageService` stub for when you're ready to add real
  character-locking via FLUX + IP-Adapter.
- **Motion**: still a Ken Burns pan/zoom, not true AI video generation
  — unchanged from before. `services/local_backend.py` has a
  `WanVideoService` stub for later.
- **Piper voice selection**: swap `PIPER_MODEL` to any voice from the
  Piper voices list to change narrator language/accent/gender.
- **Speed**: faster-whisper and Piper both run on CPU by default and
  are fast enough for clips this short; if you have a CUDA GPU,
  `export WHISPER_DEVICE=cuda` for a speed boost.
- **Cost**: $0 per episode on the default stack — only your own
  compute time.
- **Upload automation**: still not included — each platform needs its
  own developer API credentials and app review. Ask if you want a
  follow-up `UploadService` for a specific platform.
- **Safety**: since this is content for very young children, keep a
  human review step before publishing anything publicly, even after
  the pipeline is fully automated — this matters more with a free
  image model than it did with a paid one, since output quality/safety
  filtering is less predictable.
