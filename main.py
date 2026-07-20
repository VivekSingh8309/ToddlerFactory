"""
main.py
Runs the full Tiny Trails factory pipeline end to end, entirely
through the service abstraction layer (services/factory.py). This
file never imports OpenAI, MoviePy, or any other provider directly —
it only knows about StoryService, ImageService, VoiceService,
SubtitleService, and VideoService.

Usage:
  python main.py                 # produce 1 episode
  python main.py --count 5       # produce 5 episodes in a row
"""

import argparse
import os
import json
import traceback

import config
import pipeline_utils
from services.factory import get_services
from services.youtube_backend import YouTubeUploader


def run_one_episode(services, episode_number):
    episode_id = f"episode_{episode_number:04d}"
    print(f"\n=== {episode_id} ===")

    print("[1/5] Generating story...")
    combo = pipeline_utils.pick_random_combo()
    episode = services["story"].generate_episode(combo)
    story_path = os.path.join(config.DIRS["stories"], f"{episode_id}.json")
    with open(story_path, "w") as f:
        json.dump(episode, f, indent=2)
    print(f"  title: {episode['title']}")

    character_key = combo["character"]
    image_paths, audio_paths, all_words = [], [], []

    for scene in episode["scenes"]:
        n = scene["scene_number"]

        print(f"[2/5] Generating image for scene {n}...")
        image_prompt = pipeline_utils.build_image_prompt(
            scene["image_prompt"], character_key
        )
        image_path = os.path.join(
            config.DIRS["images"], f"{episode_id}_scene{n:02d}.png"
        )
        services["image"].generate_image(image_prompt, image_path)
        image_paths.append(image_path)

        print(f"[3/5] Generating narration for scene {n}...")
        audio_path = os.path.join(
            config.DIRS["audio"], f"{episode_id}_scene{n:02d}.mp3"
        )
        services["voice"].synthesize(scene["narration"], audio_path)
        audio_paths.append(audio_path)

        print(f"[4/5] Generating captions for scene {n}...")
        words = services["subtitle"].get_word_timestamps(audio_path)
        caption_path = os.path.join(
            config.DIRS["captions"], f"{episode_id}_scene{n:02d}.json"
        )
        with open(caption_path, "w") as f:
            json.dump(words, f, indent=2)
        all_words.append(words)

    print("[5/5] Assembling final video...")
    scene_clips = [
        services["video"].build_scene(img, aud, words)
        for img, aud, words in zip(image_paths, audio_paths, all_words)
    ]
    final_path = os.path.join(config.DIRS["final"], f"{episode_id}.mp4")
    services["video"].assemble(scene_clips, final_path)

    print(f"\nDone: {final_path}")
    return final_path


# def main():
#     parser = argparse.ArgumentParser()
#     parser.add_argument("--count", type=int, default=1, help="number of episodes to produce")
#     parser.add_argument("--start", type=int, default=1, help="starting episode number")
#     args = parser.parse_args()

#     if "openai" in config.BACKENDS.values() and not config.OPENAI_API_KEY:
#         raise SystemExit(
#             "One or more BACKENDS is set to 'openai' but OPENAI_API_KEY "
#             "is not set. Either set OPENAI_API_KEY, or switch that stage "
#             "back to its free/local default in config.py / via env var."
#         )

#     services = get_services()
#     uploader = YouTubeUploader()
#     print("Active backends:", config.BACKENDS)

#     results = []
#     for i in range(args.start, args.start + args.count):
#         try:
#             path = run_one_episode(services, i)
#             results.append(path)
#         except Exception as e:
#             print(f"Episode {i} failed: {e}")
#             traceback.print_exc()
#             continue

#     print(f"\n{len(results)}/{args.count} episodes completed successfully.")


# if __name__ == "__main__":
#     main()

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of episodes to produce",
    )

    parser.add_argument(
        "--start",
        type=int,
        default=1,
        help="Starting episode number",
    )

    args = parser.parse_args()

    if "openai" in config.BACKENDS.values() and not config.OPENAI_API_KEY:
        raise SystemExit(
            "One or more BACKENDS is set to 'openai' but "
            "OPENAI_API_KEY is not set."
        )

    services = get_services()

    # Authenticate YouTube once
    uploader = YouTubeUploader()

    print("Active backends:", config.BACKENDS)

    generated = 0
    uploaded = 0

    for episode_num in range(args.start, args.start + args.count):

        print("\n" + "=" * 70)
        print(f"EPISODE {episode_num}")
        print("=" * 70)

        # ---------------------------------------------------
        # STEP 1 : Generate Video
        # ---------------------------------------------------

        try:
            video_path = run_one_episode(services, episode_num)
            generated += 1

        except Exception as e:
            print("\n❌ Video generation failed")
            print(e)
            traceback.print_exc()
            continue

        # ---------------------------------------------------
        # STEP 2 : Upload Video
        # ---------------------------------------------------

        try:

            title = (
                f"Tiny Trails Episode {episode_num} "
                f"| Educational Toddler Story #Shorts"
            )

            description = f"""
🌈 Tiny Trails Episode {episode_num}

Join Piko 🐰 and Lumi 🐤 on another fun learning adventure!

Perfect for toddlers and preschool children.

✨ Educational Stories
✨ Learning Through Play
✨ Safe Kids Entertainment
✨ AI Animated Cartoons

Subscribe for new stories every day!

#Shorts
#Kids
#Toddler
#Learning
#Education
#Cartoon
"""

            tags = [
                "toddlers",
                "kids",
                "learning",
                "education",
                "cartoon",
                "preschool",
                "shorts",
                "bedtime stories",
            ]

            print("\nUploading to YouTube...")

            video_id = uploader.upload(
                video_path=video_path,
                title=title,
                description=description,
                tags=tags,
                privacy="public",     # <-- Change to public after testing
            )

            uploaded += 1

            print("\n✅ Upload Successful")
            print(f"https://youtube.com/watch?v={video_id}")

        except Exception as e:

            print("\n⚠ Video generated successfully")
            print("⚠ But YouTube upload failed.")
            print(e)
            traceback.print_exc()

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)
    print(f"Videos Generated : {generated}")
    print(f"Videos Uploaded  : {uploaded}")

if __name__ == "__main__":
     main()

