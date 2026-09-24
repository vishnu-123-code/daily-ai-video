import json
import os
import re
import subprocess
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
VIDEOS = ROOT / "videos"

STORY_FILE = DATA / "story.json"
STATE_FILE = DATA / "state.json"

VIDEOS.mkdir(exist_ok=True)

TEXT_API = "https://gen.pollinations.ai/v1/chat/completions"
IMAGE_API = "https://image.pollinations.ai/prompt/"

API_KEY = os.getenv("POLLINATIONS_API_KEY", "")


def load_json(path, default):
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def generate_text(prompt):
    headers = {"Content-Type": "application/json"}

    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"

    payload = {
        "model": "openai/gpt-oss-120b",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a Mahabharata storyteller. "
                    "Write historically ordered Mahabharata narration. "
                    "Never jump forward, never repeat earlier events, "
                    "and never invent a different chronology."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.7,
    }

    try:
        response = requests.post(
            TEXT_API,
            headers=headers,
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        result = response.json()

        return result["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print("Text generation failed:", e)
        return ""


def create_episode(episode_number, title, story):
    prompt = f"""
Create Episode {episode_number} of an automatic Mahabharata series.

TITLE:
{title}

STORY BEAT:
{story}

Requirements:

1. Narration must be natural Hindi in Devanagari.
2. Length should be approximately 110-130 Hindi words.
3. It should sound like a professional YouTube Shorts storyteller.
4. Follow ONLY the supplied story beat.
5. Do not jump to future Mahabharata events.
6. Do not repeat earlier events.
7. End naturally so the next episode can continue.
8. Return ONLY the narration.
"""

    narration = generate_text(prompt)

    if not narration:
        narration = story

    return narration


def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()


def make_image(prompt, output):
    encoded_prompt = requests.utils.quote(prompt)

    url = (
        IMAGE_API
        + encoded_prompt
        + "?width=720&height=1280&nologo=true"
    )

    try:
        response = requests.get(url, timeout=180)
        response.raise_for_status()

        with open(output, "wb") as f:
            f.write(response.content)

        return True

    except Exception as e:
        print("Image generation failed:", e)
        return False


def make_video(episode_number, narration, title):
    work = ROOT / f".episode_{episode_number}"
    work.mkdir(exist_ok=True)

    image_files = []

    scenes = [
        f"Ancient Indian epic Mahabharata, {title}, cinematic realistic historical Indian setting, dramatic lighting, detailed costumes, vertical composition",
        f"Mahabharata ancient Hastinapura, {title}, royal palace and characters, cinematic Indian epic, realistic, vertical 9:16",
        f"Ancient India during the Mahabharata era, {title}, emotional character scene, cinematic realism, detailed environment, vertical 9:16",
        f"Mahabharata epic scene, {title}, dramatic atmosphere, realistic ancient Indian costumes and architecture, vertical 9:16",
        f"Beautiful cinematic Mahabharata scene, {title}, ancient India, realistic characters, dramatic lighting, vertical 9:16",
    ]

    for i, scene in enumerate(scenes, 1):
        image_path = work / f"scene_{i}.jpg"

        if make_image(scene, image_path):
            image_files.append(image_path)

        time.sleep(2)

    if not image_files:
        print("No images generated.")
        return False

    concat_file = work / "images.txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        duration = max(8, min(12, 58 // len(image_files)))

        for image in image_files:
            f.write(f"file '{image.resolve()}'\n")
            f.write(f"duration {duration}\n")

        f.write(f"file '{image_files[-1].resolve()}'\n")

    output = VIDEOS / f"episode-{episode_number:04d}.mp4"

    command = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
        "-vf",
        "scale=720:1280:force_original_aspect_ratio=increase,"
        "crop=720:1280,format=yuv420p",
        "-r",
        "30",
        "-t",
        "60",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "28",
        str(output),
    ]

    try:
        subprocess.run(command, check=True)
        print("Created:", output)
        return True
    except Exception as e:
        print("FFmpeg failed:", e)
        return False


def main():
    story_data = load_json(STORY_FILE, {"episodes": []})
    state = load_json(STATE_FILE, {"next_episode": 1})

    episodes = story_data.get("episodes", [])
    next_episode = int(state.get("next_episode", 1))

    selected = [
        item for item in episodes
        if int(item.get("episode", 0)) >= next_episode
    ][:3]

    if not selected:
        print("No more story beats available.")
        return

    for item in selected:
        episode_number = int(item["episode"])
        title = item["title"]
        story = item["story"]

        print(f"Generating Episode {episode_number}: {title}")

        narration = create_episode(
            episode_number,
            title,
            story,
        )

        narration = clean_text(narration)

        print(narration)

        make_video(
            episode_number,
            narration,
            title,
        )

        metadata = {
            "episode": episode_number,
            "title": title,
            "story": story,
            "narration": narration,
        }

        save_json(
            VIDEOS / f"episode-{episode_number:04d}.json",
            metadata,
        )

        state["next_episode"] = episode_number + 1
        save_json(STATE_FILE, state)

        print(f"Episode {episode_number} complete.")


if __name__ == "__main__":
    main()
