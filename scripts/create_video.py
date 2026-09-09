import subprocess
from datetime import datetime
from pathlib import Path
import math
import struct

import soundfile as sf
from kokoro_onnx import Kokoro


# ==================================================
# SETTINGS
# ==================================================

today = datetime.now().strftime("%Y-%m-%d")

videos = Path("videos")
videos.mkdir(exist_ok=True)

output = videos / f"{today}.mp4"

WIDTH = 720
HEIGHT = 1280
FPS = 30

print("🎬 Creating Daily AI Video...")
print("🎙️ Voice: Kokoro Adam")
print("🖼️ Visuals: Animated illustrations")


# ==================================================
# KOKORO
# ==================================================

kokoro = Kokoro(
    "kokoro-v1.0.int8.onnx",
    "voices-v1.0.bin"
)


# ==================================================
# VIDEO SCRIPT
# ==================================================

scenes = [
    {
        "voice": "The Sun is very far away.",
        "captions": ["THE SUN", "IS VERY", "FAR AWAY"],
        "visual": "sun"
    },
    {
        "voice": "Sunlight takes about eight minutes.",
        "captions": ["SUNLIGHT TAKES", "ABOUT 8", "MINUTES"],
        "visual": "light"
    },
    {
        "voice": "And twenty seconds to reach Earth.",
        "captions": ["AND 20", "SECONDS", "TO REACH", "EARTH"],
        "visual": "earth"
    },
    {
        "voice": "When you see the Sun.",
        "captions": ["WHEN YOU", "SEE THE", "SUN"],
        "visual": "sun"
    },
    {
        "voice": "You are seeing it as it was.",
        "captions": ["YOU ARE", "SEEING IT", "AS IT", "WAS"],
        "visual": "past"
    },
    {
        "voice": "More than eight minutes ago.",
        "captions": ["MORE THAN", "8 MINUTES", "AGO"],
        "visual": "time"
    }
]


# ==================================================
# CREATE SIMPLE VISUAL IMAGE
# ==================================================

def create_visual(filename, visual_type):

    width = WIDTH
    height = HEIGHT

    pixels = bytearray(width * height * 3)

    for y in range(height):
        for x in range(width):

            # Space background gradient
            r = int(5 + 8 * y / height)
            g = int(8 + 12 * y / height)
            b = int(25 + 35 * y / height)

            # Small stars
            if ((x * 17 + y * 31) % 997) < 2:
                r = 230
                g = 230
                b = 255

            # SUN
            if visual_type == "sun":

                cx = width // 2
                cy = 500

                dx = x - cx
                dy = y - cy
                distance = math.sqrt(dx * dx + dy * dy)

                if distance < 190:
                    r, g, b = 255, 190, 40

                elif distance < 220:
                    r, g, b = 255, 100, 20

                # Rays
                if (
                    abs(x - cx) < 18 and
                    (cy - 300 < y < cy - 200 or cy + 200 < y < cy + 300)
                ):
                    r, g, b = 255, 170, 30

                if (
                    abs(y - cy) < 18 and
                    (cx - 300 < x < cx - 200 or cx + 200 < x < cx + 300)
                ):
                    r, g, b = 255, 170, 30

            # LIGHT TRAVELING TO EARTH
            elif visual_type == "light":

                # Sun
                cx = 160
                cy = 600

                dx = x - cx
                dy = y - cy
                distance = math.sqrt(dx * dx + dy * dy)

                if distance < 100:
                    r, g, b = 255, 190, 40

                # Light beam
                if 480 < y < 720 and x > 200:
                    if abs(y - 600) < 25:
                        r, g, b = 255, 210, 90

                # Earth
                ex = 600
                ey = 600

                dx = x - ex
                dy = y - ey

                if math.sqrt(dx * dx + dy * dy) < 115:
                    r, g, b = 40, 100, 220

            # EARTH
            elif visual_type == "earth":

                cx = width // 2
                cy = 560

                dx = x - cx
                dy = y - cy
                distance = math.sqrt(dx * dx + dy * dy)

                if distance < 210:
                    r, g, b = 25, 100, 210

                    # Continents
                    if (
                        (x - 330) ** 2 + (y - 500) ** 2 < 55 ** 2
                        or
                        (x - 440) ** 2 + (y - 620) ** 2 < 70 ** 2
                        or
                        (x - 350) ** 2 + (y - 650) ** 2 < 40 ** 2
                    ):
                        r, g, b = 40, 170, 90

            # PAST / TIME
            elif visual_type in ["past", "time"]:

                # Large clock
                cx = width // 2
                cy = 520

                dx = x - cx
                dy = y - cy
                distance = math.sqrt(dx * dx + dy * dy)

                if distance < 210:
                    r, g, b = 225, 225, 235

                    # Clock hands
                    if abs(x - cx) < 10 and cy - 130 < y < cy:
                        r, g, b = 30, 30, 50

                    if abs(y - cy) < 10 and cx < x < cx + 120:
                        r, g, b = 30, 30, 50

            index = (y * width + x) * 3

            pixels[index] = r
            pixels[index + 1] = g
            pixels[index + 2] = b

    # Write PPM image
    with open(filename, "wb") as f:

        header = f"P6\n{width} {height}\n255\n".encode()

        f.write(header)
        f.write(pixels)


# ==================================================
# CREATE SCENES
# ==================================================

parts = []

for i, scene in enumerate(scenes, start=1):

    audio = Path(f"audio{i}.wav")
    image = Path(f"scene{i}.ppm")
    video = Path(f"part{i}.mp4")

    print(f"🎙️ Creating Adam narration {i}...")

    # ----------------------------------------------
    # KOKORO ADAM
    # ----------------------------------------------

    samples, sample_rate = kokoro.create(
        scene["voice"],
        voice="am_adam",
        speed=0.95,
        lang="en-us"
    )

    sf.write(str(audio), samples, sample_rate)

    # ----------------------------------------------
    # AUDIO DURATION
    # ----------------------------------------------

    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio)
        ],
        capture_output=True,
        text=True,
        check=True
    )

    duration = float(result.stdout.strip()) + 0.3

    print(f"⏱️ Scene {i}: {duration:.2f} seconds")

    # ----------------------------------------------
    # CREATE VISUAL
    # ----------------------------------------------

    print(f"🖼️ Creating visual {i}...")

    create_visual(
        str(image),
        scene["visual"]
    )

    # ----------------------------------------------
    # DYNAMIC CAPTIONS
    # ----------------------------------------------

    caption_count = len(scene["captions"])
    caption_duration = duration / caption_count

    filters = []

    for index, caption in enumerate(scene["captions"]):

        start = index * caption_duration
        end = (index + 1) * caption_duration

        safe_caption = (
            caption
            .replace("\\", "\\\\")
            .replace(":", "\\:")
            .replace("'", "\\'")
        )

        filters.append(
            "drawtext=text='"
            + safe_caption
            + "':"
            "fontcolor=white:"
            "fontsize=62:"
            "fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
            "borderw=5:"
            "bordercolor=black:"
            "x=(w-text_w)/2:"
            "y=900:"
            "enable='between(t,"
            + str(start)
            + ","
            + str(end)
            + ")'"
        )

    filter_text = ",".join(filters)

    # ----------------------------------------------
    # ANIMATED VISUAL + VOICE + CAPTIONS
    # ----------------------------------------------

    subprocess.run(
        [
            "ffmpeg",
            "-y",

            "-loop",
            "1",

            "-i",
            str(image),

            "-i",
            str(audio),

            "-t",
            str(duration),

            "-vf",
            "scale=720:1280,"
            "zoompan="
            "z='min(zoom+0.0007,1.12)':"
            "d=1:"
            "s=720x1280:"
            "fps=30,"
            + filter_text,

            "-c:v",
            "libx264",

            "-c:a",
            "aac",

            "-pix_fmt",
            "yuv420p",

            "-shortest",

            str(video)
        ],
        check=True
    )

    parts.append(video)


# ==================================================
# JOIN EVERYTHING
# ==================================================

print("🎬 Joining scenes...")

scenes_file = Path("scenes.txt")

with open(scenes_file, "w") as f:

    for part in parts:
        f.write(f"file '{part}'\n")


subprocess.run(
    [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(scenes_file),
        "-c",
        "copy",
        str(output)
    ],
    check=True
)


print(f"✅ VIDEO CREATED: {output}")


# ==================================================
# CLEANUP
# ==================================================

for i in range(1, len(scenes) + 1):

    for file in [
        Path(f"audio{i}.wav"),
        Path(f"scene{i}.ppm"),
        Path(f"part{i}.mp4")
    ]:

        if file.exists():
            file.unlink()


if scenes_file.exists():
    scenes_file.unlink()


print("🧹 Temporary files cleaned.")
print("🎉 Daily AI Video completed successfully!")
