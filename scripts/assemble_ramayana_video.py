"""Assemble 9:16 vertical Ramayana video with Ken Burns motion, visual sync, and subtitles."""

import json
import subprocess
from pathlib import Path

PROJECT_DIR = Path("projects/ramayana-surpanakha-shorts")
CLIPS_DIR = PROJECT_DIR / "clips"
CLIPS_DIR.mkdir(parents=True, exist_ok=True)

FPS = 30
WIDTH = 1080
HEIGHT = 1920

# Scene definitions with exact start, duration, and motion
SCENES = [
    {
        "id": 1,
        "image": PROJECT_DIR / "scene_1.jpg",
        "duration": 7.5,
        "zoom_expr": "min(zoom+0.0008,1.15)",
        "x_expr": "(iw-iw/zoom)/2",
        "y_expr": "(ih-ih/zoom)/2",
    },
    {
        "id": 2,
        "image": PROJECT_DIR / "scene_2.jpg",
        "duration": 9.6,
        "zoom_expr": "min(zoom+0.0006,1.12)",
        "x_expr": "(iw-iw/zoom)/2",
        "y_expr": "(ih-ih/zoom)*0.3",
    },
    {
        "id": 3,
        "image": PROJECT_DIR / "scene_3.jpg",
        "duration": 7.8,
        "zoom_expr": "min(zoom+0.0012,1.25)",
        "x_expr": "(iw-iw/zoom)/2",
        "y_expr": "(ih-ih/zoom)*0.4",
    },
    {
        "id": 4,
        "image": PROJECT_DIR / "scene_4.jpg",
        "duration": 8.5,
        "zoom_expr": "min(zoom+0.0010,1.20)",
        "x_expr": "(iw-iw/zoom)*0.6",
        "y_expr": "(ih-ih/zoom)/2",
    },
    {
        "id": 5,
        "image": PROJECT_DIR / "scene_5.jpg",
        "duration": 9.5,
        "zoom_expr": "min(zoom+0.0015,1.28)",
        "x_expr": "(iw-iw/zoom)/2",
        "y_expr": "(ih-ih/zoom)*0.45",
    },
    {
        "id": 6,
        "image": PROJECT_DIR / "scene_6.jpg",
        "duration": 8.5,
        "zoom_expr": "max(1.18-0.0008*on,1.0)",
        "x_expr": "(iw-iw/zoom)/2",
        "y_expr": "(ih-ih/zoom)*0.3",
    },
]

# Step 1: Render each scene video clip
clip_paths = []
for sc in SCENES:
    num_frames = int(sc["duration"] * FPS)
    out_clip = CLIPS_DIR / f"clip_{sc['id']}.mp4"
    clip_paths.append(out_clip)

    print(f"Rendering Clip {sc['id']}: {sc['duration']}s ({num_frames} frames)...")
    
    # Scale image to 1080x1920 with zoompan filter
    vf = (
        f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={WIDTH}:{HEIGHT},"
        f"zoompan=z='{sc['zoom_expr']}':x='{sc['x_expr']}':y='{sc['y_expr']}':"
        f"d={num_frames}:s={WIDTH}x{HEIGHT}:fps={FPS},"
        f"format=yuv420p"
    )

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-t", str(sc["duration"]),
        "-i", str(sc["image"].resolve()),
        "-vf", vf,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-r", str(FPS),
        "-pix_fmt", "yuv420p",
        str(out_clip.resolve()),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error rendering clip {sc['id']}: {res.stderr[-400:]}")
        raise RuntimeError(f"FFmpeg failed on clip {sc['id']}")

print("All clips rendered successfully!")

# Step 2: Concat clips
concat_list = CLIPS_DIR / "concat.txt"
with open(concat_list, "w", encoding="utf-8") as f:
    for cp in clip_paths:
        f.write(f"file '{cp.resolve().as_posix()}'\n")

concat_video = PROJECT_DIR / "raw_visuals.mp4"
cmd_concat = [
    "ffmpeg", "-y",
    "-f", "concat",
    "-safe", "0",
    "-i", str(concat_list.resolve()),
    "-c", "copy",
    str(concat_video.resolve()),
]
subprocess.run(cmd_concat, check=True)
print("Concatenated visuals created:", concat_video)

# Step 3: Write ASS Subtitles
ass_content = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: EpicSubtitle, Arial, 42, &H0000E6FF, &H000000FF, &H00000000, &H80000000, 1, 0, 0, 0, 100, 100, 1, 0, 1, 4, 3, 2, 70, 70, 260, 1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.10,0:00:07.50,EpicSubtitle,,0,0,0,,দণ্ডকারণ্যের শান্ত পঞ্চবটীতে শ্রীরাম, মাতা সীতা এবং লক্ষ্মণ বাস করছিলেন
Dialogue: 0,0:00:07.50,0:00:12.60,EpicSubtitle,,0,0,0,,হঠাৎ সেখানে উপস্থিত হলো লঙ্কার রাজা রাবণের বোন শূর্পণখা
Dialogue: 0,0:00:12.60,0:00:17.10,EpicSubtitle,,0,0,0,,শ্রীরামের রূপ দেখে সে মোহিত হয়ে বিবাহের প্রস্তাব দিল
Dialogue: 0,0:00:17.10,0:00:24.90,EpicSubtitle,,0,0,0,,শ্রীরামের প্রত্যাখ্যান ও পরিহাসে ক্ষিপ্ত হয়ে শূর্পণখা ধারণ করল ভয়াল রাক্ষসী রূপ!
Dialogue: 0,0:00:24.90,0:00:33.40,EpicSubtitle,,0,0,0,,মাতা সীতাকে আক্রমণ করতে উদ্যত হলে, বিদ্যুতের গতিতে লক্ষ্মণ কোষমুক্ত করলেন খড়্গ!
Dialogue: 0,0:00:33.40,0:00:38.80,EpicSubtitle,,0,0,0,,এক নিমেষে লক্ষ্মণের ধারালো তলোয়ার কেটে ফেলল শূর্পণখার নাক ও কান!
Dialogue: 0,0:00:38.80,0:00:42.90,EpicSubtitle,,0,0,0,,যন্ত্রণার তীব্র আর্তনাদে কেঁপে উঠল সমগ্র অরণ্য!
Dialogue: 0,0:00:42.90,0:00:51.40,EpicSubtitle,,0,0,0,,রক্তাক্ত শূর্পণখা প্রতিশোধের বিষবাষ্প ছড়িয়ে লঙ্কার দিকে পালিয়ে গেল...
"""

sub_file = PROJECT_DIR / "subtitles.ass"
sub_file.write_text(ass_content, encoding="utf-8")
print("Wrote ASS subtitle file:", sub_file)

# Step 4: Final Mix & Render with Audio and Subtitles
final_output = PROJECT_DIR / "ramayana_surpanakha_9x16.mp4"
narration_file = PROJECT_DIR / "narration.mp3"
ambient_file = PROJECT_DIR / "ambient_drone.mp3"

sub_path_escaped = str(sub_file.resolve()).replace("\\", "/").replace(":", "\\:")

cmd_final = [
    "ffmpeg", "-y",
    "-i", str(concat_video.resolve()),
    "-i", str(narration_file.resolve()),
    "-i", str(ambient_file.resolve()),
    "-filter_complex",
    f"[1:a]volume=1.0[narr];"
    f"[2:a]volume=0.20[bgm];"
    f"[narr][bgm]amix=inputs=2:duration=first[aout];"
    f"[0:v]subtitles='{sub_path_escaped}'[vout]",
    "-map", "[vout]",
    "-map", "[aout]",
    "-c:v", "libx264",
    "-preset", "medium",
    "-crf", "19",
    "-c:a", "aac",
    "-b:a", "192k",
    "-shortest",
    str(final_output.resolve()),
]

print("Executing final render with audio mix and subtitles...")
res_final = subprocess.run(cmd_final, capture_output=True, text=True)
if res_final.returncode != 0:
    print("Final render error, retrying without subtitle filter burning:")
    # Fallback to soft subtitles or direct audio mux
    cmd_fallback = [
        "ffmpeg", "-y",
        "-i", str(concat_video.resolve()),
        "-i", str(narration_file.resolve()),
        "-i", str(ambient_file.resolve()),
        "-filter_complex",
        "[1:a]volume=1.0[narr];[2:a]volume=0.20[bgm];[narr][bgm]amix=inputs=2:duration=first[aout]",
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(final_output.resolve()),
    ]
    subprocess.run(cmd_fallback, check=True)

print("Final video created successfully:", final_output)
