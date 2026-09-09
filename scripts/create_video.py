import subprocess
from datetime import datetime
from pathlib import Path

today = datetime.now().strftime("%Y-%m-%d")

Path("videos").mkdir(exist_ok=True)

output = f"videos/{today}.mp4"

print("🎬 Creating today's video...")
print(f"📅 Date: {today}")

text = f"DAILY AI VIDEO\\n{today}\\n\\nA new video every day!"

command = [
    "ffmpeg",
    "-y",
    "-f", "lavfi",
    "-i", "color=c=black:s=1280x720:r=30",
    "-t", "8",
    "-vf",
    f"drawtext=text='{text}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2:line_spacing=20",
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    output
]

subprocess.run(command, check=True)

print(f"✅ Video created: {output}")
