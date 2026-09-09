import subprocess
from datetime import datetime
from pathlib import Path

import soundfile as sf
from kokoro_onnx import Kokoro


# --------------------------------------------------
# 1. SETTINGS
# --------------------------------------------------

today = datetime.now().strftime("%Y-%m-%d")

videos = Path("videos")
videos.mkdir(exist_ok=True)

output = videos / f"{today}.mp4"

print("🎬 Creating Daily AI Video...")
print("🎙️ Voice: Kokoro Adam")


# --------------------------------------------------
# 2. LOAD KOKORO
# --------------------------------------------------

kokoro = Kokoro(
    "kokoro-v1.0.int8.onnx",
    "voices-v1.0.bin"
)


# --------------------------------------------------
# 3. SCRIPT + SHORT CAPTION CHUNKS
# --------------------------------------------------

scenes = [
    {
        "voice": "The Sun is very far away.",
        "captions": ["THE SUN", "IS VERY", "FAR AWAY"]
    },
    {
        "voice": "Sunlight takes about eight minutes.",
        "captions": ["SUNLIGHT TAKES", "ABOUT 8", "MINUTES"]
    },
    {
        "voice": "And twenty seconds to reach Earth.",
        "captions": ["AND 20", "SECONDS", "TO REACH", "EARTH"]
    },
    {
        "voice": "When you see the Sun.",
        "captions": ["WHEN YOU", "SEE THE", "SUN"]
    },
    {
        "voice": "You are seeing it as it was.",
        "captions": ["YOU ARE", "SEEING IT", "AS IT", "WAS"]
    },
    {
        "voice": "More than eight minutes ago.",
        "captions": ["MORE THAN", "8 MINUTES", "AGO"]
    }
]


# --------------------------------------------------
# 4. CREATE EACH SCENE
# --------------------------------------------------

parts = []

for i, scene in enumerate(scenes, start=1):

    audio = Path(f"audio{i}.wav")
    video = Path(f"part{i}.mp4")

    print(f"🎙️ Creating Adam narration {i}...")

    # Generate Adam voice
    samples, sample_rate = kokoro.create(
        scene["voice"],
        voice="am_adam",
        speed=0.95,
        lang="en-us"
    )

    sf.write(str(audio), samples, sample_rate)

    # Get narration duration
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

    # --------------------------------------------------
    # CREATE CAPTION TIMING
    # --------------------------------------------------

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
            "fontsize=58:"
            "x=(w-text_w)/2:"
            "y=(h-text_h)/2:"
            "enable='between(t,"
            + str(start)
            + ","
            + str(end)
            + ")'"
        )

    filter_text = ",".join(filters)

    # --------------------------------------------------
    # CREATE VIDEO
    # --------------------------------------------------

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "color=c=0x111827:s=720x1280:r=30",
        "-i", str(audio),
        "-t", str(duration),
        "-vf", filter_text,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(video)
    ], check=True)

    parts.append(video)


# --------------------------------------------------
# 5. JOIN SCENES
# --------------------------------------------------

print("🎬 Joining scenes...")

scenes_file = Path("scenes.txt")

with open(scenes_file, "w") as f:
    for part in parts:
        f.write(f"file '{part}'\n")

subprocess.run([
    "ffmpeg", "-y",
    "-f", "concat",
    "-safe", "0",
    "-i", str(scenes_file),
    "-c", "copy",
    str(output)
], check=True)


print(f"✅ VIDEO CREATED: {output}")


# --------------------------------------------------
# 6. CLEAN TEMPORARY FILES
# --------------------------------------------------

for i in range(1, len(scenes) + 1):

    for file in [
        Path(f"audio{i}.wav"),
        Path(f"part{i}.mp4")
    ]:
        if file.exists():
            file.unlink()

if scenes_file.exists():
    scenes_file.unlink()

print("🧹 Temporary files cleaned.")
print("🎉 Daily AI Video completed successfully!")
