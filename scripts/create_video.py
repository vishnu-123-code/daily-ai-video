import subprocess
from datetime import datetime
from pathlib import Path

import soundfile as sf
from kokoro_onnx import Kokoro


# --------------------------------------------------
# 1. BASIC SETTINGS
# --------------------------------------------------

today = datetime.now().strftime("%Y-%m-%d")

videos = Path("videos")
videos.mkdir(exist_ok=True)

output = videos / f"{today}.mp4"

print("🎬 Creating Daily AI Video...")
print("🎙️ Voice: Kokoro Adam (am_adam)")


# --------------------------------------------------
# 2. LOAD KOKORO
# --------------------------------------------------

kokoro = Kokoro(
    "kokoro-v1.0.int8.onnx",
    "voices-v1.0.bin"
)


# --------------------------------------------------
# 3. VIDEO SCRIPT
# --------------------------------------------------

scenes = [
    {
        "title": "DID YOU KNOW?",
        "text": "The Sun is very far away.",
        "voice": "The Sun is very far away."
    },
    {
        "title": "AMAZING FACT",
        "text": "Sunlight takes about 8 minutes.",
        "voice": "Sunlight takes about eight minutes."
    },
    {
        "title": "TO REACH EARTH",
        "text": "And 20 seconds to reach Earth.",
        "voice": "And twenty seconds to reach Earth."
    },
    {
        "title": "THINK ABOUT THIS",
        "text": "When you see the Sun...",
        "voice": "When you see the Sun..."
    },
    {
        "title": "YOU ARE SEEING THE PAST",
        "text": "You are seeing it as it was.",
        "voice": "You are seeing it as it was."
    },
    {
        "title": "8 MINUTES AGO",
        "text": "More than 8 minutes ago.",
        "voice": "More than eight minutes ago."
    }
]


# --------------------------------------------------
# 4. CREATE EACH SCENE
# --------------------------------------------------

parts = []

for i, scene in enumerate(scenes, start=1):

    audio = Path(f"audio{i}.wav")
    image = Path(f"scene{i}.png")
    video = Path(f"part{i}.mp4")

    print(f"🎙️ Creating Adam narration {i}...")

    # Generate AI voice with Kokoro Adam
    samples, sample_rate = kokoro.create(
        scene["voice"],
        voice="am_adam",
        speed=0.95,
        lang="en-us"
    )

    # Save narration
    sf.write(str(audio), samples, sample_rate)

    # --------------------------------------------------
    # GET AUDIO DURATION
    # --------------------------------------------------

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

    duration = float(result.stdout.strip()) + 0.4

    print(f"⏱️ Scene {i}: {duration:.2f} seconds")


    # --------------------------------------------------
    # CREATE VERTICAL IMAGE
    # --------------------------------------------------

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "color=c=0x111827:s=720x1280",
        "-frames:v", "1",
        "-vf",
        (
            "drawtext=text='"
            + scene["title"]
            + "':"
            "fontcolor=white:"
            "fontsize=48:"
            "x=(w-text_w)/2:"
            "y=400,"
            "drawtext=text='"
            + scene["text"]
            + "':"
            "fontcolor=white:"
            "fontsize=38:"
            "x=(w-text_w)/2:"
            "y=620"
        ),
        str(image)
    ], check=True)


    # --------------------------------------------------
    # CREATE VIDEO WITH ADAM AUDIO
    # --------------------------------------------------

    subprocess.run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(image),
        "-i", str(audio),
        "-t", str(duration),
        "-r", "30",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(video)
    ], check=True)

    parts.append(video)


# --------------------------------------------------
# 5. JOIN ALL SCENES
# --------------------------------------------------

print("🎬 Joining all scenes...")

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
        Path(f"scene{i}.png"),
        Path(f"part{i}.mp4")
    ]:
        if file.exists():
            file.unlink()

if scenes_file.exists():
    scenes_file.unlink()

print("🧹 Temporary files cleaned.")
print("🎉 Daily AI Video completed successfully!")
