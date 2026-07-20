# """
# services/moviepy_backend.py

# VideoService implementation using MoviePy's Ken Burns pan/zoom, same
# logic as the original video_assembler.py, now behind the VideoService
# interface so it can be swapped for a real image-to-video model later
# without touching main.py.
# """

# import os
# import glob
# import random
# from moviepy.editor import (
#     ImageClip,
#     AudioFileClip,
#     CompositeVideoClip,
#     CompositeAudioClip,
#     TextClip,
#     concatenate_videoclips,
# )
# from moviepy.video.fx.resize import resize as fx_resize
# from PIL import Image, ImageDraw, ImageFont
# import numpy as np
# import config
# from services.base import VideoService

# W, H = 1080, 1920


# class MoviePyVideoService(VideoService):
#     def _ken_burns_clip(self, image_path, duration):
#         clip = ImageClip(image_path)
#         clip = fx_resize(clip, height=int(H * 1.15))
#         zoom_start, zoom_end = 1.0, 1.12

#         def resize_func(t):
#             progress = t / duration
#             return zoom_start + (zoom_end - zoom_start) * progress

#         clip = clip.resize(resize_func)
#         clip = clip.set_position(("center", "center"))
#         return clip.set_duration(duration)

#     def _caption_clips(self, words, duration, group_size=3):
#         clips = []
#         for i in range(0, len(words), group_size):
#             group = words[i : i + group_size]
#             if not group:
#                 continue
#             text = " ".join(w["word"].strip() for w in group)
#             start = group[0]["start"]
#             end = group[-1]["end"]
#             seg_duration = max(end - start, 0.4)

#             txt_clip = (
#                 TextClip(
#                     text,
#                     fontsize=70,
#                     color="white",
#                     font="DejaVu-Sans-Bold",
#                     stroke_color="black",
#                     stroke_width=3,
#                     method="caption",
#                     size=(int(W * 0.85), None),
#                 )
#                 .set_start(start)
#                 .set_duration(seg_duration)
#                 .set_position(("center", H * 0.78))
#             )
#             clips.append(txt_clip)
#         return clips

#     def build_scene(self, image_path, audio_path, words):
#         audio = AudioFileClip(audio_path)
#         duration = audio.duration

#         bg = self._ken_burns_clip(image_path, duration)
#         captions = self._caption_clips(words, duration)

#         scene = CompositeVideoClip([bg, *captions], size=(W, H))
#         scene = scene.set_audio(audio)
#         return scene.set_duration(duration)

#     def _add_background_music(self, video, volume=0.08):
#         music_files = glob.glob(os.path.join(config.DIRS["music"], "*.mp3"))
#         if not music_files:
#             return video

#         music_path = random.choice(music_files)
#         music = AudioFileClip(music_path).volumex(volume)

#         if music.duration < video.duration:
#             from moviepy.audio.fx.audio_loop import audio_loop
#             music = audio_loop(music, duration=video.duration)
#         else:
#             music = music.subclip(0, video.duration)

#         final_audio = CompositeAudioClip([video.audio, music])
#         return video.set_audio(final_audio)

#     def assemble(self, scene_clips, out_path: str) -> str:
#         full_video = concatenate_videoclips(scene_clips, method="compose")
#         full_video = self._add_background_music(full_video)
#         full_video.write_videofile(
#             out_path,
#             fps=30,
#             codec="libx264",
#             audio_codec="aac",
#             threads=4,
#         )
#         return out_path




"""
services/moviepy_backend.py

VideoService implementation using MoviePy.

This version removes the ImageMagick dependency completely by rendering
captions with Pillow instead of MoviePy's TextClip.
"""

import os
import glob
import random
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    CompositeVideoClip,
    CompositeAudioClip,
    concatenate_videoclips,
)
from moviepy.video.fx.resize import resize as fx_resize

import config
from services.base import VideoService

W, H = 1080, 1920


class MoviePyVideoService(VideoService):

    def _ken_burns_clip(self, image_path, duration):
        clip = ImageClip(image_path)

        clip = fx_resize(clip, height=int(H * 1.15))

        zoom_start = 1.0
        zoom_end = 1.12

        def resize_func(t):
            progress = t / duration
            return zoom_start + (zoom_end - zoom_start) * progress

        clip = clip.resize(resize_func)
        clip = clip.set_position(("center", "center"))

        return clip.set_duration(duration)

    # ----------------------------------------------------------

    def _load_font(self, size):

        possible_fonts = [
            "arial.ttf",
            "Arial.ttf",
            "DejaVuSans-Bold.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/ARIALBD.TTF",
            "C:/Windows/Fonts/segoeuib.ttf",
        ]

        for font in possible_fonts:
            try:
                return ImageFont.truetype(font, size)
            except Exception:
                pass

        return ImageFont.load_default()

    # ----------------------------------------------------------

    def _create_caption_image(self, text):

        width = int(W * 0.85)
        height = 220

        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        font = self._load_font(70)

        bbox = draw.textbbox((0, 0), text, font=font)

        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (width - text_width) // 2
        y = (height - text_height) // 2

        outline = 3

        for dx in range(-outline, outline + 1):
            for dy in range(-outline, outline + 1):
                if dx == 0 and dy == 0:
                    continue

                draw.text(
                    (x + dx, y + dy),
                    text,
                    font=font,
                    fill="black",
                )

        draw.text(
            (x, y),
            text,
            font=font,
            fill="white",
        )

        temp = tempfile.NamedTemporaryFile(
            suffix=".png",
            delete=False,
        )

        image.save(temp.name)

        return temp.name

    # ----------------------------------------------------------

    def _caption_clips(self, words, duration, group_size=3):

        clips = []

        for i in range(0, len(words), group_size):

            group = words[i:i + group_size]

            if not group:
                continue

            text = " ".join(
                w["word"].strip()
                for w in group
            )

            start = group[0]["start"]
            end = group[-1]["end"]

            seg_duration = max(end - start, 0.4)

            image_path = self._create_caption_image(text)

            clip = (
                ImageClip(image_path)
                .set_start(start)
                .set_duration(seg_duration)
                .set_position(("center", H * 0.78))
            )

            clips.append(clip)

        return clips

    # ----------------------------------------------------------

    def build_scene(self, image_path, audio_path, words):

        audio = AudioFileClip(audio_path)

        duration = audio.duration

        bg = self._ken_burns_clip(image_path, duration)

        captions = self._caption_clips(words, duration)

        scene = CompositeVideoClip(
            [bg, *captions],
            size=(W, H),
        )

        scene = scene.set_audio(audio)

        return scene.set_duration(duration)

    # ----------------------------------------------------------

    def _add_background_music(self, video, volume=0.08):

        music_files = glob.glob(
            os.path.join(config.DIRS["music"], "*.mp3")
        )

        if not music_files:
            return video

        music_path = random.choice(music_files)

        music = AudioFileClip(music_path).volumex(volume)

        if music.duration < video.duration:

            from moviepy.audio.fx.audio_loop import audio_loop

            music = audio_loop(
                music,
                duration=video.duration,
            )

        else:
            music = music.subclip(
                0,
                video.duration,
            )

        final_audio = CompositeAudioClip(
            [
                video.audio,
                music,
            ]
        )

        return video.set_audio(final_audio)

    # ----------------------------------------------------------

    def assemble(self, scene_clips, out_path):

        video = concatenate_videoclips(
            scene_clips,
            method="compose",
        )

        video = self._add_background_music(video)

        video.write_videofile(
            out_path,
            fps=30,
            codec="libx264",
            audio_codec="aac",
            threads=4,
        )

        return out_path
