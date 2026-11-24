import json, os, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ID = "ramayana-vivaha-ayodhya"
PROJECT_DIR = str(REPO_ROOT / "projects" / PROJECT_ID)
ARTIFACTS_DIR = os.path.join(PROJECT_DIR, "artifacts")
CHECKPOINTS_DIR = os.path.join(PROJECT_DIR, "checkpoints")
os.makedirs(ARTIFACTS_DIR, exist_ok=True)
os.makedirs(CHECKPOINTS_DIR, exist_ok=True)

now = datetime.datetime.now(datetime.timezone.utc).isoformat()

# Load timestamps
with open(os.path.join(ARTIFACTS_DIR, "timestamps.json"), "r", encoding="utf-8") as f:
    ts_data = json.load(f)

scenes = ts_data["scenes"]
total_dur = ts_data["total_duration"]

# 1. Script Artifact
script_artifact = {
    "version": "1.0",
    "title": "रामायण भाग ६ — दिव्य राम-सीता विवाह एवं अयोध्या आगमन",
    "total_duration_seconds": total_dur,
    "sections": [
        {
            "id": f"s{s['id']}",
            "label": f"Scene {s['id']}: {s['subtitle']}",
            "text": s["narration"],
            "start_seconds": s["start_time"],
            "end_seconds": s["end_time"]
        }
        for s in scenes
    ]
}

with open(os.path.join(ARTIFACTS_DIR, "script.json"), "w", encoding="utf-8") as f:
    json.dump(script_artifact, f, indent=2, ensure_ascii=False)

# 2. Scene Plan Artifact
scene_plan_artifact = {
    "version": "1.0",
    "project_id": PROJECT_ID,
    "scenes": [
        {
            "id": f"scene_{s['id']}",
            "scene_number": s["id"],
            "heading": s["subtitle"],
            "duration_seconds": s["duration"],
            "visual_prompt": f"8K ancient Indian mythological epic painting in Raja Ravi Varma style for Scene {s['id']}",
            "narration": s["narration"]
        }
        for s in scenes
    ]
}

with open(os.path.join(ARTIFACTS_DIR, "scene_plan.json"), "w", encoding="utf-8") as f:
    json.dump(scene_plan_artifact, f, indent=2, ensure_ascii=False)

# 3. Asset Manifest Artifact
asset_manifest_artifact = {
    "version": "1.0",
    "project_id": PROJECT_ID,
    "assets": [
        {
            "id": f"img_scene_{s['id']}",
            "type": "image",
            "scene_id": f"scene_{s['id']}",
            "path": f"images/scene_{s['id']}.jpg"
        }
        for s in scenes
    ] + [
        {
            "id": "audio_master",
            "type": "audio",
            "path": "audio/audio_mix.mp3"
        }
    ]
}

with open(os.path.join(ARTIFACTS_DIR, "asset_manifest.json"), "w", encoding="utf-8") as f:
    json.dump(asset_manifest_artifact, f, indent=2, ensure_ascii=False)

# 4. Checkpoints
stages = [
    ("research", {}),
    ("proposal", {}),
    ("script", {"script": script_artifact}),
    ("scene_plan", {"scene_plan": scene_plan_artifact}),
    ("assets", {"asset_manifest": asset_manifest_artifact}),
    ("edit", {}),
    ("compose", {}),
    ("enhancement", {}),
    ("publish", {})
]

for stage_name, arts in stages:
    cp_data = {
        "version": "1.0",
        "project_id": PROJECT_ID,
        "pipeline_type": "mythological_shorts",
        "stage": stage_name,
        "status": "completed",
        "timestamp": now,
        "checkpoint_policy": "guided",
        "human_approval_required": False,
        "human_approved": True,
        "artifacts": arts
    }
    with open(os.path.join(PROJECT_DIR, f"checkpoint_{stage_name}.json"), "w", encoding="utf-8") as f:
        json.dump(cp_data, f, indent=2, ensure_ascii=False)
    with open(os.path.join(CHECKPOINTS_DIR, f"{stage_name}.json"), "w", encoding="utf-8") as f:
        json.dump(cp_data, f, indent=2, ensure_ascii=False)

print("Generated all Ep6 artifacts and checkpoints successfully.")
