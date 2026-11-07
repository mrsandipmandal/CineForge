import sys
import shutil
import subprocess
import requests
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.video.stock_sources.wikimedia import WikimediaSource
from tools.video.stock_sources.nasa import NasaSource
from tools.video.stock_sources.base import SearchFilters

project_dir = Path("projects/rahasyalok-quantum-entanglement")
img_dir = project_dir / "assets" / "images"
img_dir.mkdir(parents=True, exist_ok=True)

# Copy subagent scenes 1, 2, 3
brain_dir = Path(r"C:\Users\mr_sa\.gemini\antigravity\brain\2587e69a-7d04-4052-8bde-361e82536ae7")
s1_src = brain_dir / "scene_01_1794068158337.jpg"
s2_src = brain_dir / "scene_02_1794068172819.jpg"
s3_src = brain_dir / "scene_03_1794068221589.jpg"

if s1_src.exists():
    shutil.copy(s1_src, img_dir / "scene_01.png")
    print("Copied scene_01.png")
if s2_src.exists():
    shutil.copy(s2_src, img_dir / "scene_02.png")
    print("Copied scene_02.png")
if s3_src.exists():
    shutil.copy(s3_src, img_dir / "scene_03.png")
    print("Copied scene_03.png")

w = WikimediaSource()
n = NasaSource()

headers = {'User-Agent': 'CineForge-Bot/1.0 (educational research)'}

def download_and_crop(url: str, out_path: Path):
    temp_raw = out_path.with_suffix('.raw.jpg')
    print(f"Downloading from {url[:80]}...")
    resp = requests.get(url, headers=headers, timeout=25)
    resp.raise_for_status()
    with open(temp_raw, 'wb') as f:
        f.write(resp.content)
    
    # Crop and scale to 1080x1920 using FFmpeg
    # scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920
    crop_cmd = [
        "ffmpeg", "-y",
        "-i", str(temp_raw),
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=contrast=1.1:brightness=-0.02:saturation=1.15",
        str(out_path)
    ]
    subprocess.run(crop_cmd, check=True)
    temp_raw.unlink(missing_ok=True)
    print(f"Formatted and saved {out_path.name} (1080x1920)")

# Scene 4: Nobel Prize medal in Physics
print("Searching Scene 4: Nobel prize medal...")
res4 = w.search("Nobel prize medal Sweden", SearchFilters(kind='image', per_page=5))
for cand in res4:
    try:
        download_and_crop(cand.download_url, img_dir / "scene_04.png")
        break
    except Exception as e:
        print("Scene 4 error on cand:", e)

# Scene 5: Quantum computer chandelier
print("Searching Scene 5: Quantum computer...")
res5 = w.search("Quantum computer IBM cryostat dilution", SearchFilters(kind='image', per_page=5))
if not res5:
    res5 = w.search("Quantum computer", SearchFilters(kind='image', per_page=5))

for cand in res5:
    try:
        download_and_crop(cand.download_url, img_dir / "scene_05.png")
        break
    except Exception as e:
        print("Scene 5 error on cand:", e)

# Scene 6: Cosmic galaxies / Hubble deep field
print("Searching Scene 6: Galaxy collision / Hubble...")
res6 = n.search("Hubble galaxy collision", SearchFilters(kind='image', per_page=5))
if not res6:
    res6 = n.search("deep field galaxy", SearchFilters(kind='image', per_page=5))

for cand in res6:
    try:
        download_and_crop(cand.download_url, img_dir / "scene_06.png")
        break
    except Exception as e:
        print("Scene 6 error on cand:", e)

# Scene 7: Cosmic vortex / nebula space
print("Searching Scene 7: Cosmic nebula vortex...")
res7 = n.search("Helix nebula eye space", SearchFilters(kind='image', per_page=5))
if not res7:
    res7 = n.search("Carina nebula cosmic", SearchFilters(kind='image', per_page=5))

for cand in res7:
    try:
        download_and_crop(cand.download_url, img_dir / "scene_07.png")
        break
    except Exception as e:
        print("Scene 7 error on cand:", e)

print("All 7 scene images ready in:", img_dir)
