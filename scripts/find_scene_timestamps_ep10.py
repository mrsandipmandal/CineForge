import subprocess
import os

sample_dir = r"f:\CineForge\projects\ramayana-ep10-bharat-kaikeyi-dhikkar\tv_clips\ep_samples"
os.makedirs(sample_dir, exist_ok=True)

checks = [
    # Ep 39: Bharat arrives in Ayodhya, meets Kaikeyi
    ("VB1qUiypwZQ", "02:00", "02:02", "ep39_02m"),
    ("VB1qUiypwZQ", "05:00", "05:02", "ep39_05m"),
    ("VB1qUiypwZQ", "08:00", "08:02", "ep39_08m"),
    ("VB1qUiypwZQ", "12:00", "12:02", "ep39_12m"),
    ("VB1qUiypwZQ", "16:00", "16:02", "ep39_16m"),
    ("VB1qUiypwZQ", "19:00", "19:02", "ep39_19m"),

    # Ep 40: Bharat angry at Kaikeyi, meeting Kausalya
    ("2sCCUAu9dRA", "02:00", "02:02", "ep40_02m"),
    ("2sCCUAu9dRA", "05:00", "05:02", "ep40_05m"),
    ("2sCCUAu9dRA", "08:00", "08:02", "ep40_08m"),
    ("2sCCUAu9dRA", "12:00", "12:02", "ep40_12m"),
    ("2sCCUAu9dRA", "16:00", "16:02", "ep40_16m"),
    ("2sCCUAu9dRA", "19:00", "19:02", "ep40_19m"),

    # Ep 41: Bharat's pledge, departure for Chitrakoot
    ("jjZBp8NbbP8", "02:00", "02:02", "ep41_02m"),
    ("jjZBp8NbbP8", "05:00", "05:02", "ep41_05m"),
    ("jjZBp8NbbP8", "08:00", "08:02", "ep41_08m")
]

for video_id, t_start, t_end, tag in checks:
    out_mp4 = os.path.join(sample_dir, f"{tag}.mp4")
    out_jpg = os.path.join(sample_dir, f"{tag}.jpg")
    if os.path.exists(out_jpg):
        continue
    cmd = [
        "yt-dlp",
        "--download-sections", f"*{t_start}-{t_end}",
        "-f", "136/bestvideo[height<=720]",
        "-o", out_mp4,
        f"https://www.youtube.com/watch?v={video_id}"
    ]
    print(f"Downloading {tag}...")
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    cmd_f = ["ffmpeg", "-y", "-i", out_mp4, "-vframes", "1", out_jpg]
    subprocess.run(cmd_f, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("Ep samples complete!")
