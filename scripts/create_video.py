import subprocess
from datetime import datetime
from pathlib import Path

today = datetime.now().strftime("%Y-%m-%d")

videos = Path("videos")
videos.mkdir(exist_ok=True)

output = videos / f"{today}.mp4"
audio = Path("narration.wav")

print("🎬 Creating today's short video...")

# Narration
narration = (
    "Welcome to Daily AI Video. "
    "Did you know that the light from the Sun takes about eight minutes "
    "and twenty seconds to reach Earth? "
    "That means when you look at the Sun, you are seeing it as it was "
    "more than eight minutes ago. "
    "Follow Daily AI Video for a new interesting fact every day."
)

subprocess.run([
    "espeak-ng",
    "-w", str(audio),
    "-s", "145",
    "-v", "en",
    narration
], check=True)

# Scene 1
scene1 = Path("scene1.png")
subprocess.run([
    "ffmpeg", "-y",
    "-f", "lavfi",
    "-i", "color=c=0x111827:s=1280x720",
    "-frames:v", "1",
    "-vf",
    "drawtext=text='DAILY AI VIDEO':"
    "fontcolor=white:fontsize=70:"
    "x=(w-text_w)/2:y=220,"
    "drawtext=text='Amazing Space Fact':"
    "fontcolor=white:fontsize=48:"
    "x=(w-text_w)/2:y=340",
    str(scene1)
], check=True)

# Scene 2
scene2 = Path("scene2.png")
subprocess.run([
    "ffmpeg", "-y",
    "-f", "lavfi",
    "-i", "color=c=0x172554:s=1280x720",
    "-frames:v", "1",
    "-vf",
    "drawtext=text='THE SUN':"
    "fontcolor=yellow:fontsize=80:"
    "x=(w-text_w)/2:y=180,"
    "drawtext=text='☀':"
    "fontcolor=yellow:fontsize=150:"
    "x=(w-text_w)/2:y=300",
    str(scene2)
], check=True)

# Scene 3
scene3 = Path("scene3.png")
subprocess.run([
    "ffmpeg", "-y",
    "-f", "lavfi",
    "-i", "color=c=0x0f172a:s=1280x720",
    "-frames:v", "1",
    "-vf",
    "drawtext=text='8 MINUTES 20 SECONDS':"
    "fontcolor=white:fontsize=65:"
    "x=(w-text_w)/2:y=220,"
    "drawtext=text='Sunlight takes this long to reach Earth':"
    "fontcolor=white:fontsize=38:"
    "x=(w-text_w)/2:y=340",
    str(scene3)
], check=True)

# Create each scene as a 4-second video
for number in range(1, 4):
    subprocess.run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", f"scene{number}.png",
        "-t", "4",
        "-r", "30",
        "-pix_fmt", "yuv420p",
        f"part{number}.mp4"
    ], check=True)

# Join the scenes
Path("scenes.txt").write_text(
    "file 'part1.mp4'\n"
    "file 'part2.mp4'\n"
    "file 'part3.mp4'\n"
)

subprocess.run([
    "ffmpeg", "-y",
    "-f", "concat",
    "-safe", "0",
    "-i", "scenes.txt",
    "-c", "copy",
    "visual.mp4"
], check=True)

# Add narration
subprocess.run([
    "ffmpeg", "-y",
    "-i", "visual.mp4",
    "-i", str(audio),
    "-c:v", "copy",
    "-c:a", "aac",
    "-shortest",
    str(output)
], check=True)

print(f"✅ Finished: {output}")

# Clean temporary files
for file in [
    audio, scene1, scene2, scene3,
    Path("part1.mp4"), Path("part2.mp4"),
    Path("part3.mp4"), Path("visual.mp4"),
    Path("scenes.txt")
]:
    if file.exists():
        file.unlink()
