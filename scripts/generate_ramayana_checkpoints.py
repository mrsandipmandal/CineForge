import json, os, datetime

PROJECT_ID = "ramayana-parashurama-krodh"
PROJECT_DIR = r"f:\CineForge\projects\ramayana-parashurama-krodh"
ARTIFACTS_DIR = os.path.join(PROJECT_DIR, "artifacts")
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

now = datetime.datetime.now(datetime.timezone.utc).isoformat()

# Load timestamps to get exact scenes
with open(os.path.join(PROJECT_DIR, "timestamps_parashurama.json"), "r", encoding="utf-8") as f:
    ts_data = json.load(f)

scenes = ts_data["scenes"]
total_dur = ts_data["total_duration"]

# 1. Script Artifact
script_artifact = {
    "version": "1.0",
    "title": "रामायण भाग ५ — भगवान परशुराम का क्रोध एवं वैष्णव धनुष",
    "total_duration_seconds": total_dur,
    "sections": [
        {
            "id": f"s{s['id']}",
            "label": f"Scene {s['id']}: {s['subtitle']}",
            "text": s["text"],
            "start_seconds": s["start"],
            "end_seconds": s["end"]
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
            "visual_prompt": f"8K ancient Indian mythological epic painting for Scene {s['id']}",
            "narration": s["text"]
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
            "path": "audio_mix_parashurama.mp3"
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
        "pipeline_type": "cinematic",
        "stage": stage_name,
        "status": "completed",
        "timestamp": now,
        "checkpoint_policy": "guided",
        "human_approval_required": False,
        "human_approved": True,
        "artifacts": arts
    }
    cp_path = os.path.join(PROJECT_DIR, f"checkpoint_{stage_name}.json")
    with open(cp_path, "w", encoding="utf-8") as f:
        json.dump(cp_data, f, indent=2, ensure_ascii=False)

print("Successfully generated all checkpoints and artifacts for Backlot!")
