import subprocess
from pathlib import Path

project_dir = Path("projects/rahasyalok-quantum-entanglement")
audio_dir = project_dir / "assets" / "audio"
music_dir = project_dir / "assets" / "music"
audio_dir.mkdir(parents=True, exist_ok=True)
music_dir.mkdir(parents=True, exist_ok=True)

sections = [
    {
        "id": "sec_01",
        "text": "कल्पना कीजिए... दो कण। एक यहाँ, एक अरबों प्रकाश-वर्ष दूर। और फिर भी... एक पल में एक-दूसरे से जुड़े।",
        "rate": "+55%"
    },
    {
        "id": "sec_02",
        "text": "यह विज्ञान की सबसे बड़ी पहेली है — क्वांटम एंटैंगलमेंट। जब दो कण आपस में उलझ जाते हैं, तो वे हमेशा के लिए एक हो जाते हैं। दोनों के बीच चाहे जितनी भी दूरी हो।",
        "rate": "+58%"
    },
    {
        "id": "sec_03",
        "text": "यहाँ तक कि खुद आइंस्टीन इस बात को मानने से डरते थे। उन्होंने इसे कहा — Spooky Action at a Distance! मतलब — दूर से होने वाली डरावनी हरकत। उन्हें लगा, यह impossible है।",
        "rate": "+58%"
    },
    {
        "id": "sec_04",
        "text": "लेकिन 2022 में तीन वैज्ञानिकों ने यह साबित कर दिया — यह सच है! और उन्हें मिला Physics का Nobel Prize। आइंस्टीन गलत थे।",
        "rate": "+58%"
    },
    {
        "id": "sec_05",
        "text": "और आज? इसी तकनीक से बन रहे हैं Quantum Computers — जो साधारण कंप्यूटर से लाखों गुना तेज़ होंगे। और Quantum Cryptography — जिसे कोई भी hack नहीं कर सकता।",
        "rate": "+58%"
    },
    {
        "id": "sec_06",
        "text": "तो सोचिए — दो कण, अरबों किलोमीटर दूर, एक पल में एक-दूसरे को महसूस करते हैं। यह Physics है... या जादू?",
        "rate": "+55%"
    },
    {
        "id": "sec_07",
        "text": "आपको क्या लगता है — क्या Quantum Entanglement से कभी Time Travel possible होगा? Comment में बताइए!",
        "rate": "+58%"
    }
]

print("Synthesizing voiceover sections at exact 52-54s target rate...")
voice = "hi-IN-MadhurNeural"
sec_files = []
durations = []

for sec in sections:
    out_file = audio_dir / f"{sec['id']}.mp3"
    sec_files.append(out_file)
    cmd = [
        "edge-tts",
        "--voice", voice,
        "--rate", sec["rate"],
        "--text", sec["text"],
        "--write-media", str(out_file)
    ]
    subprocess.run(cmd, check=True)
    
    probe_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(out_file)
    ]
    res = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
    dur = float(res.stdout.strip())
    durations.append(dur)
    print(f"Generated {sec['id']}: {dur:.2f}s")

concat_list = audio_dir / "concat_list.txt"
with open(concat_list, "w", encoding="utf-8") as f:
    for sf in sec_files:
        f.write(f"file '{sf.name}'\n")

voiceover_master = audio_dir / "voiceover.mp3"
concat_cmd = [
    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
    "-i", str(concat_list),
    "-c", "copy",
    str(voiceover_master)
]
subprocess.run(concat_cmd, check=True)

probe_cmd = [
    "ffprobe", "-v", "error",
    "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1",
    str(voiceover_master)
]
res = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
total_voice_dur = float(res.stdout.strip())
print(f"Perfect YouTube Shorts voiceover generated: {total_voice_dur:.2f}s")

bgm_file = music_dir / "bgm.mp3"
bgm_cmd = [
    "ffmpeg", "-y",
    "-f", "lavfi", "-i", "sine=frequency=55:sample_rate=44100",
    "-f", "lavfi", "-i", "sine=frequency=110:sample_rate=44100",
    "-f", "lavfi", "-i", "anoisesrc=sample_rate=44100:amplitude=0.012:color=brown",
    "-filter_complex",
    f"[0:a]volume=0.35[s1];[1:a]volume=0.18[s2];[2:a]lowpass=f=400,volume=0.25[n];[s1][s2][n]amix=inputs=3:duration=first[mix];[mix]afade=t=in:ss=0:d=1.5,afade=t=out:st={total_voice_dur}:d=1.5[out]",
    "-map", "[out]",
    "-t", f"{total_voice_dur + 1.2:.2f}",
    "-b:a", "192k",
    str(bgm_file)
]
subprocess.run(bgm_cmd, check=True)

final_mix = audio_dir / "final_mix.mp3"
mix_cmd = [
    "ffmpeg", "-y",
    "-i", str(voiceover_master),
    "-i", str(bgm_file),
    "-filter_complex",
    "[1:a]volume=0.14[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[out]",
    "-map", "[out]",
    "-b:a", "192k",
    str(final_mix)
]
subprocess.run(mix_cmd, check=True)
print("Final mix ready at:", final_mix)
