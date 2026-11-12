"""
ambient_synthesis.py — Science Explainer ambient audio generator (multi-theme)
Usage: python ambient_synthesis.py <output_path> <duration_seconds> [theme]

Themes:
  ocean (default): brown noise + 40Hz sub-bass + 8kHz shimmer + gentle lowpass
  space: pink noise + 60Hz drone + subtle stereo width
  nature: brown noise + higher frequency filtered ambience
"""
import sys
import subprocess

def generate_ambient(output_path: str, duration: int = 65, theme: str = "ocean"):
    if theme == "ocean":
        filter_complex = (
            "[0]volume=0.9[n];"
            "[1]volume=0.06[sub];"
            "[2]volume=0.015[shimmer];"
            "[n][sub][shimmer]amix=inputs=3:duration=first,"
            "equalizer=f=180:t=o:w=80:g=4,"
            "equalizer=f=3500:t=o:w=800:g=-8,"
            "aecho=0.8:0.6:1200:0.25,"
            "volume=1.4[out]"
        )
        inputs = [
            "-f", "lavfi", "-i", f"anoisesrc=color=brown:amplitude=0.08:duration={duration}",
            "-f", "lavfi", "-i", f"sine=frequency=40:duration={duration}",
            "-f", "lavfi", "-i", f"sine=frequency=7500:duration={duration}",
        ]
    elif theme == "space":
        filter_complex = (
            "[0]volume=0.5[n];"
            "[1]volume=0.05[sub];"
            "[n][sub]amix=inputs=2:duration=first,"
            "equalizer=f=80:t=o:w=50:g=3,"
            "volume=1.2[out]"
        )
        inputs = [
            "-f", "lavfi", "-i", f"anoisesrc=color=pink:amplitude=0.04:duration={duration}",
            "-f", "lavfi", "-i", f"sine=frequency=60:duration={duration}",
        ]
    else:  # nature / general
        filter_complex = (
            "[0]volume=0.7[n];"
            "[1]volume=0.03[sub];"
            "[n][sub]amix=inputs=2:duration=first,"
            "volume=1.0[out]"
        )
        inputs = [
            "-f", "lavfi", "-i", f"anoisesrc=color=brown:amplitude=0.06:duration={duration}",
            "-f", "lavfi", "-i", f"sine=frequency=120:duration={duration}",
        ]

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    print(f"Ambient audio saved: {output_path}")

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "ambient.mp3"
    dur = int(sys.argv[2]) if len(sys.argv) > 2 else 65
    thm = sys.argv[3] if len(sys.argv) > 3 else "ocean"
    generate_ambient(out, dur, thm)
