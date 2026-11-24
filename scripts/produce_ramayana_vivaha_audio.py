"""Produce mastered narration and timestamps for Ramayana Episode 6.

Uses Fish Audio s2-pro with Sanjay Deep Authoritative Baritone Voice.
Applies broadcast mastering chain: 75Hz highpass, +2.5dB@120Hz warmth, opto compression, -14 LUFS.
Outputs:
- projects/ramayana-vivaha-ayodhya/audio/audio_mix.mp3
- projects/ramayana-vivaha-ayodhya/artifacts/timestamps.json
"""

import json
import os
import subprocess
import sys
from pathlib import Path

from tools.audio.fish_audio_tts import FishAudioTTS

PROJECT_DIR = Path(__file__).resolve().parent.parent / "projects" / "ramayana-vivaha-ayodhya"
SCRIPT_FILE = PROJECT_DIR / "artifacts" / "script.json"
AUDIO_DIR = PROJECT_DIR / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
    script_data = json.load(f)

scenes = script_data["scenes"]
tts = FishAudioTTS()
VOICE_ID = "28dcd01c14684153842b6d0b4713af80"

scene_audio_files = []

for scene in scenes:
    sid = scene["id"]
    text = scene["narration"]
    out_file = AUDIO_DIR / f"scene_{sid}.mp3"
    print(f"Generating scene {sid} audio...")
    res = tts.execute({
        "text": text,
        "reference_id": VOICE_ID,
        "model": "s2-pro",
        "output_path": str(out_file),
    })
    if not res.success:
        print(f"ERROR generating scene {sid}: {res.error}")
        sys.exit(1)
    scene_audio_files.append(out_file)
    print(f"  Saved: {out_file.name}")

# Measure durations via ffprobe
def get_duration(fpath):
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(fpath)
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(p.stdout.strip())

durations = [get_duration(f) for f in scene_audio_files]

# Build timestamps
timestamps = []
current_time = 0.0
for scene, dur, fpath in zip(scenes, durations, scene_audio_files):
    end_time = current_time + dur
    timestamps.append({
        "id": scene["id"],
        "subtitle": scene["subtitle"],
        "narration": scene["narration"],
        "start_time": round(current_time, 2),
        "end_time": round(end_time, 2),
        "duration": round(dur, 2),
        "file": str(fpath.name),
    })
    current_time = end_time

total_duration = round(current_time, 2)
print(f"Total narration duration: {total_duration}s across {len(scenes)} scenes")

# Create concat list for ffmpeg
concat_txt = AUDIO_DIR / "concat_list.txt"
with open(concat_txt, "w", encoding="utf-8") as f:
    for fpath in scene_audio_files:
        f.write(f"file '{fpath.name}'\n")

raw_concat = AUDIO_DIR / "raw_concat.mp3"
concat_cmd = [
    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
    "-i", str(concat_txt), "-c", "copy", str(raw_concat)
]
subprocess.run(concat_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Master audio chain: 75Hz highpass, 120Hz boost, opto compression, -14 LUFS
master_audio = AUDIO_DIR / "audio_mix.mp3"
af_filter = (
    "highpass=f=75,"
    "equalizer=f=120:width_type=q:w=1.2:g=2.5,"
    "equalizer=f=3500:width_type=q:w=1.0:g=1.8,"
    "acompressor=threshold=-18dB:ratio=3:attack=25:release=120,"
    "loudnorm=I=-14:LRA=7:tp=-1.0"
)
master_cmd = [
    "ffmpeg", "-y", "-i", str(raw_concat),
    "-af", af_filter, "-b:a", "192k", str(master_audio)
]
print("Mastering audio with broadcast chain...")
subprocess.run(master_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
print(f"Master audio produced: {master_audio}")

# Save timestamps.json
ts_out = PROJECT_DIR / "artifacts" / "timestamps.json"
with open(ts_out, "w", encoding="utf-8") as f:
    json.dump({
        "project_id": "ramayana-vivaha-ayodhya",
        "total_duration": total_duration,
        "scenes": timestamps,
    }, f, indent=2, ensure_ascii=False)

print(f"Saved timestamps: {ts_out}")
