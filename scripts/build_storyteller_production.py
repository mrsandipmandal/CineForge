import sys
from pathlib import Path
import json
import subprocess
import shutil

project_id = 'rahasyalok-quantum-entanglement'
project_dir = Path('projects') / project_id
assets_dir = project_dir / 'assets'
audio_dir = assets_dir / 'audio'
renders_dir = project_dir / 'renders'
renders_dir.mkdir(parents=True, exist_ok=True)
images_dir = assets_dir / 'images'

print("=== Step 1: Building Concatenated Storyteller Voiceover ===")
sec_files = [audio_dir / f"sec_{i:02d}.mp3" for i in range(1, 6)]
silence_025 = audio_dir / "silence_025.mp3"
subprocess.run([
    'ffmpeg', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=24000:cl=mono', '-t', '0.25',
    '-c:a', 'libmp3lame', '-b:a', '128k', str(silence_025)
], check=True, capture_output=True)

# Build concat list for voiceover
concat_list_file = audio_dir / "concat_vo.txt"
with open(concat_list_file, 'w', encoding='utf-8') as f:
    for i, sec in enumerate(sec_files):
        f.write(f"file '{sec.resolve().as_posix()}'\n")
        if i < len(sec_files) - 1:
            f.write(f"file '{silence_025.resolve().as_posix()}'\n")

vo_master = audio_dir / "voiceover_storyteller.mp3"
subprocess.run([
    'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(concat_list_file),
    '-c:a', 'libmp3lame', '-b:a', '160k', str(vo_master)
], check=True, capture_output=True)

vo_dur = float(subprocess.check_output([
    'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
    '-of', 'default=noprint_wrappers=1:nokey=1', str(vo_master)
], text=True).strip())
print(f"Master voiceover duration: {vo_dur:.2f}s")

print("=== Step 2: Mixing with Atmospheric Suspense BGM ===")
bgm_in = assets_dir / 'music' / 'bgm.mp3'
final_mix = audio_dir / 'final_mix.mp3'
# Voice at 1.0, BGM ducked at 0.13, fade out at end of video
subprocess.run([
    'ffmpeg', '-y',
    '-i', str(vo_master),
    '-i', str(bgm_in),
    '-filter_complex',
    f"[1:a]volume=0.13,afade=t=out:st={vo_dur-2.0}:d=2.0[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[out]",
    '-map', '[out]',
    '-c:a', 'libmp3lame', '-b:a', '192k',
    str(final_mix)
], check=True, capture_output=True)
print("Final audio mix created successfully!")

print("=== Step 3: Generating Storyteller Subtitles (ASS) ===")
# Exact timestamps based on section lengths:
# sec_01: 0.00 -> 9.07s
# pause 0.25 -> 9.32s
# sec_02: 9.32 -> 20.86s
# pause 0.25 -> 21.11s
# sec_03: 21.11 -> 31.05s
# pause 0.25 -> 31.30s
# sec_04: 31.30 -> 41.52s
# pause 0.25 -> 41.77s
# sec_05: 41.77 -> 51.71s

ass_header = """[Script Info]
Title: RahasyaLok Quantum Storyteller
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Nirmala UI,62,&H0000D7FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,60,60,340,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

events = [
    "Dialogue: 0,0:00:00.30,0:00:04.50,Default,,0,0,0,,साल 1935... अल्बर्ट आइंस्टीन",
    "Dialogue: 0,0:00:04.50,0:00:09.10,Default,,0,0,0,,एक ऐसे रहस्य से कांप उठे,\\Nजिसने विज्ञान की दुनिया हिला दी!",
    "Dialogue: 0,0:00:09.35,0:00:14.20,Default,,0,0,0,,कल्पना कीजिए... दो कण।\\Nअरबों किलोमीटर दूर!",
    "Dialogue: 0,0:00:14.20,0:00:20.90,Default,,0,0,0,,लेकिन एक को छूते ही...\\Nदूसरा उसी पल बदल जाता है!",
    "Dialogue: 0,0:00:21.15,0:00:25.50,Default,,0,0,0,,बिना किसी तार या सिग्नल के —\\Nप्रकाश से भी तेज़!",
    "Dialogue: 0,0:00:25.50,0:00:31.10,Default,,0,0,0,,आइंस्टीन ने इसे कहा — स्पूकी एक्शन...\\Nयानी भूतों जैसी हरकत!",
    "Dialogue: 0,0:00:31.35,0:00:36.50,Default,,0,0,0,,आज आधुनिक विज्ञान ने साबित किया\\Nकि यह क्वांटम उलझन सच है...",
    "Dialogue: 0,0:00:36.50,0:00:41.55,Default,,0,0,0,,और इसी पर भविष्य के\\Nसुपर कंप्यूटर बन रहे हैं!",
    "Dialogue: 0,0:00:41.80,0:00:46.50,Default,,0,0,0,,क्या हमारा ब्रह्मांड\\Nएक अनदेखा मायाजाल है?",
    "Dialogue: 0,0:00:46.50,0:00:51.80,Default,,0,0,0,,कमेंट में बताइए, और सब्सक्राइब करें\\Nरहस्यों की दुनिया — RahasyaLok को!"
]

ass_path = assets_dir / 'subtitles.ass'
ass_path.write_text(ass_header + '\n'.join(events) + '\n', encoding='utf-8')
print("Subtitles.ass written successfully!")

print("=== Step 4: Generating Dynamic Ken Burns Action Clips ===")
temp_clips_dir = renders_dir / 'clips'
temp_clips_dir.mkdir(parents=True, exist_ok=True)

# 8 Dynamic action cuts across the 52.0s duration
cuts_spec = [
    # 0.00 -> 9.30s: Einstein study (creeping slow zoom-in into face)
    {'img': images_dir / 'scene_03.png', 'dur': 9.35, 'fps': 30, 'zf': "zoom+0.0008", 'max_z': 1.25, 'x': 'iw/2-(iw/zoom/2)', 'y': 'ih/2-(ih/zoom/2)'},
    # 9.35 -> 15.00s: Cosmic web (slow zoom-out)
    {'img': images_dir / 'scene_02.png', 'dur': 5.65, 'fps': 30, 'zf': "zoom-0.0010", 'max_z': 1.25, 'x': 'iw/2-(iw/zoom/2)', 'y': 'ih/2-(ih/zoom/2)'},
    # 15.00 -> 21.15s: Entangled particle vortex (slow push-in)
    {'img': images_dir / 'scene_01.png', 'dur': 6.15, 'fps': 30, 'zf': "zoom+0.0012", 'max_z': 1.25, 'x': 'iw/2-(iw/zoom/2)', 'y': 'ih/2-(ih/zoom/2)'},
    # 21.15 -> 26.00s: Hubble deep space (vertical pan)
    {'img': images_dir / 'scene_06.png', 'dur': 4.85, 'fps': 30, 'zf': "1.15", 'max_z': 1.20, 'x': 'iw/2-(iw/zoom/2)', 'y': 'ih*0.2+(ih*0.6*on/(30*4.85))-(ih/zoom/2)'},
    # 26.00 -> 31.35s: Einstein blackboard equations (slow horizontal pan)
    {'img': images_dir / 'scene_03.png', 'dur': 5.35, 'fps': 30, 'zf': "1.20", 'max_z': 1.25, 'x': 'iw*0.2+(iw*0.4*on/(30*5.35))-(iw/zoom/2)', 'y': 'ih/2-(ih/zoom/2)'},
    # 31.35 -> 36.50s: Cryogenic quantum computer (slow zoom in)
    {'img': images_dir / 'scene_04.png', 'dur': 5.15, 'fps': 30, 'zf': "zoom+0.0012", 'max_z': 1.25, 'x': 'iw/2-(iw/zoom/2)', 'y': 'ih/2-(ih/zoom/2)'},
    # 36.50 -> 41.80s: Supercomputer optical core (slow pan)
    {'img': images_dir / 'scene_05.png', 'dur': 5.30, 'fps': 30, 'zf': "1.15", 'max_z': 1.20, 'x': 'iw/2-(iw/zoom/2)', 'y': 'ih*0.7-(ih*0.4*on/(30*5.30))-(ih/zoom/2)'},
    # 41.80 -> 52.00s: Cosmic Helix nebula vortex (creeping zoom-in into eye of cosmos)
    {'img': images_dir / 'scene_07.png', 'dur': 10.20, 'fps': 30, 'zf': "zoom+0.0007", 'max_z': 1.25, 'x': 'iw/2-(iw/zoom/2)', 'y': 'ih/2-(ih/zoom/2)'}
]

rendered_clips = []
for i, cut in enumerate(cuts_spec):
    clip_path = temp_clips_dir / f"cut_{i:02d}.mp4"
    frames = int(cut['dur'] * cut['fps'])
    vf = f"zoompan=z='min({cut['zf']},{cut['max_z']})':d={frames}:x='{cut['x']}':y='{cut['y']}':s=1080x1920:fps=30"
    cmd = [
        'ffmpeg', '-y',
        '-loop', '1', '-i', str(cut['img']),
        '-vf', vf,
        '-t', str(cut['dur']),
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
        '-pix_fmt', 'yuv420p',
        str(clip_path)
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    rendered_clips.append(clip_path)
    print(f"Rendered dynamic action cut {i+1}/8 ({cut['dur']:.2f}s)")

# Concat video cuts
clips_list_file = temp_clips_dir / 'clips_list.txt'
with open(clips_list_file, 'w', encoding='utf-8') as f:
    for c in rendered_clips:
        f.write(f"file '{c.resolve().as_posix()}'\n")

raw_video = renders_dir / 'raw_action_cuts.mp4'
subprocess.run([
    'ffmpeg', '-y',
    '-f', 'concat', '-safe', '0', '-i', str(clips_list_file),
    '-c', 'copy',
    str(raw_video)
], check=True, capture_output=True)
print("Dynamic action video concatenated successfully!")

print("=== Step 5: Final Mux with Audio & Single-Track ASS Subtitles ===")
final_mp4 = renders_dir / 'final.mp4'
ass_relative = ass_path.relative_to(Path('.')).as_posix()

burn_cmd = [
    'ffmpeg', '-y',
    '-i', str(raw_video),
    '-i', str(final_mix),
    '-map', '0:v:0',
    '-map', '1:a:0',
    '-vf', f"ass={ass_relative}",
    '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
    '-c:a', 'aac', '-b:a', '192k',
    '-shortest',
    str(final_mp4)
]
subprocess.run(burn_cmd, check=True)
print(f"Final video rendered successfully: {final_mp4}")

# Probe result
dur = subprocess.check_output([
    'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
    '-of', 'default=noprint_wrappers=1:nokey=1', str(final_mp4)
], text=True).strip()
print(f"Verified Final Video Duration: {float(dur):.2f}s")
