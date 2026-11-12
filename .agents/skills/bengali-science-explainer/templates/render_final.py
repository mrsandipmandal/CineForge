"""
render_final.py — Science Explainer final compose script (multi-language, multi-format)
Usage: python render_final.py <project_dir> <num_scenes> <output_path> [width] [height]

Reads: assets/images/scene_{i}_*.png, assets/audio/scene_{i}_narration.mp3
       assets/audio/full_ambient.mp3 (or full_ocean_ambient.mp3), assets/subtitles.ass
Writes: renders/final.mp4

Defaults: 1080x1920 (vertical Short)
"""
import sys
import os
import subprocess
import glob

def find_scene_image(assets_dir, scene_num):
    pattern = os.path.join(assets_dir, "images", f"scene_{scene_num}_*.png")
    matches = glob.glob(pattern)
    if not matches:
        raise FileNotFoundError(f"No image found for scene {scene_num}: {pattern}")
    return matches[0].replace("\\", "/")

def get_audio_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_streams", path],
        capture_output=True, text=True
    )
    import json
    data = json.loads(result.stdout)
    for s in data.get("streams", []):
        if "duration" in s:
            return float(s["duration"])
    return 13.0

def render_final(project_dir, num_scenes, output_path, width=1080, height=1920):
    project_dir = project_dir.replace("\\", "/")
    assets_dir = f"{project_dir}/assets"
    temp_dir = f"{project_dir}/assets/temp_segments"
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(f"{project_dir}/renders", exist_ok=True)

    segments = []

    for i in range(1, num_scenes + 1):
        img = find_scene_image(assets_dir, i)
        narration = f"{assets_dir}/audio/scene_{i}_narration.mp3"
        seg_out = f"{temp_dir}/seg_{i:02d}.mp4"

        dur = get_audio_duration(narration) + 0.6
        frames = int(dur * 30)

        zoom_filter = (
            f"zoompan=z='min(zoom+0.0005,1.18)':"
            f"x='iw/2-(iw/zoom/2)':y='ih*0.30-(ih/zoom*0.30)':"
            f"d={frames}:s={width}x{height}:fps=30"
        )

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", img,
            "-i", narration,
            "-filter_complex",
            f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},{zoom_filter}[v]",
            "-map", "[v]",
            "-map", "1:a",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k",
            "-t", str(dur),
            seg_out
        ]
        subprocess.run(cmd, check=True)
        segments.append(seg_out)

    # Concat list
    concat_list = f"{temp_dir}/concat_list.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for seg in segments:
            f.write(f"file '{seg}'\n")

    concat_out = f"{temp_dir}/concat.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_list,
        "-c", "copy",
        concat_out
    ], check=True)

    # Locate ambient audio
    ambient = f"{assets_dir}/audio/full_ambient.mp3"
    if not os.path.exists(ambient):
        ambient_alt = f"{assets_dir}/audio/full_ocean_ambient.mp3"
        if os.path.exists(ambient_alt):
            ambient = ambient_alt

    # Get total duration
    total_dur = get_audio_duration(concat_out)

    # Build ambient if missing
    if not os.path.exists(ambient):
        ambient_script = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "ambient_synthesis.py"
        )
        subprocess.run(
            ["python", ambient_script, ambient, str(int(total_dur) + 5), "ocean"],
            check=True
        )

    # Re-extract audio from concat_out and mix with ambient
    final_mix = f"{temp_dir}/final_mix.mp3"
    subprocess.run([
        "ffmpeg", "-y",
        "-i", concat_out,
        "-i", ambient,
        "-filter_complex",
        f"[0:a]volume=1.0[narr];"
        f"[1:a]volume=0.15,atrim=0:{total_dur},asetpts=PTS-STARTPTS[ambi];"
        "[narr][ambi]amix=inputs=2:duration=first[mix]",
        "-map", "[mix]",
        "-c:a", "libmp3lame", "-b:a", "192k",
        final_mix
    ], check=True)

    # Subtitles handling with safe escaping for Windows paths
    sub_file = f"{assets_dir}/subtitles.ass"
    if not os.path.exists(sub_file):
        sub_file_alt = f"{assets_dir}/subtitles.srt"
        if os.path.exists(sub_file_alt):
            sub_file = sub_file_alt

    if os.path.exists(sub_file):
        escaped_sub = sub_file.replace("\\", "/").replace(":", "\\:")
        vf = f"ass='{escaped_sub}'"
    else:
        vf = "null"

    final_cmd = [
        "ffmpeg", "-y",
        "-i", concat_out,
        "-i", final_mix,
        "-vf", vf,
        "-map", "0:v",
        "-map", "1:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        output_path
    ]
    subprocess.run(final_cmd, check=True)
    print(f"\nFinal video successfully rendered: {output_path}")

if __name__ == "__main__":
    proj = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    out = sys.argv[3] if len(sys.argv) > 3 else f"{proj}/renders/final.mp4"
    w = int(sys.argv[4]) if len(sys.argv) > 4 else 1080
    h = int(sys.argv[5]) if len(sys.argv) > 5 else 1920
    render_final(proj, n, out, w, h)
