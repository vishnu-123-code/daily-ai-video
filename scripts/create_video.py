import subprocess
from datetime import datetime
from pathlib import Path

today = datetime.now().strftime("%Y-%m-%d")

videos = Path("videos")
videos.mkdir(exist_ok=True)

output = videos / f"{today}.mp4"

print("🎬 Creating today's Daily AI Video...")

# --------------------------------------------------
# 1. SCRIPT
# --------------------------------------------------

scenes = [
    {
        "title": "DID YOU KNOW?",
        "text": "The Sun is very far away.",
        "voice": "The Sun is very far away."
    },
    {
        "title": "AMAZING FACT",
        "text": "Sunlight takes about 8 minutes",
        "voice": "Sunlight takes about eight minutes"
    },
    {
        "title": "TO REACH EARTH",
        "text": "and 20 seconds to reach Earth.",
        "voice": "and twenty seconds to reach Earth."
    },
    {
        "title": "THINK ABOUT THIS",
        "text": "When you see the Sun,",
        "voice": "When you see the Sun,"
    },
    {
        "title": "YOU ARE SEEING THE PAST",
        "text": "you are seeing it as it was",
        "voice": "you are seeing it as it was"
    },
    {
        "title": "8 MINUTES AGO",
        "text": "more than 8 minutes ago.",
        "voice": "more than eight minutes ago."
    }
]

# --------------------------------------------------
# 2. CREATE VIDEO PARTS
# --------------------------------------------------

parts = []

for i, scene in enumerate(scenes, start=1):

    audio = Path(f"audio{i}.wav")
    image = Path(f"scene{i}.png")
    video = Path(f"part{i}.mp4")

    print(f"🎙️ Creating narration {i}...")

    # Create clear, slower narration
    subprocess.run([
        "espeak-ng",
        "-w", str(audio),
        "-s", "125",
        "-p", "50",
        "-a", "180",
        "-v", "en-us",
        scene["voice"]
    ], check=True)

    # Get audio duration
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

    # Create vertical 9:16 image
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
            "y=400:"
            "text_align=center,"
            "drawtext=text='"
            + scene["text"]
            + "':"
            "fontcolor=white:"
            "fontsize=38:"
            "x=(w-text_w)/2:"
            "y=620:"
            "text_align=center"
        ),
        str(image)
    ], check=True)

    # Make video exactly as long as narration
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
# 3. JOIN ALL SCENES
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
# 4. CLEAN TEMPORARY FILES
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
