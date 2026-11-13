"""End-to-End demonstration test for Mars Cinematic Production.

Exercises the full lifecycle:
1. Production Wizard progressive intake and AI Decision
2. Proposal Packet generation and validation
3. Cinematic Scene Spec generation and ThreeJSWorld validation
4. Initial Composed Render and Visual QA
5. Video Quality Enhancer (cinematic profile)
6. AI Human Enhancer (verified not_applicable on Mars landscape)
7. Before/After Comparison and Final Stream QA
8. Checkpoint persistence across stages
"""

import json
import subprocess
from pathlib import Path
import pytest

from lib.checkpoint import (
    CANONICAL_STAGE_ARTIFACTS,
    init_project,
    write_checkpoint,
    validate_checkpoint,
)
from lib.cinematic_scene_spec import CinematicSceneSpec
from lib.production_wizard import ProductionWizard, SelectionMode, WizardMode
from schemas.artifacts import validate_artifact
from tools.analysis.visual_qa import VisualQA
from tools.enhancement.ai_human_enhancer import AIHumanEnhancer
from tools.enhancement.video_quality_enhancer import VideoQualityEnhancer
from tools.graphics.threejs_world import ThreeJSWorld


def test_mars_cinematic_end_to_end(tmp_path: Path, monkeypatch):
    """Run full Mars cinematic workflow end-to-end."""
    from lib import paths as paths_mod
    monkeypatch.setattr(paths_mod, "PROJECTS_DIR", tmp_path / "projects")

    project_id = "mars-cinematic-demo"
    pipeline_dir = tmp_path / "projects"
    project_dir = init_project(
        project_id,
        title="Mars Canyon Reveal",
        pipeline_type="cinematic",
        pipeline_dir=pipeline_dir,
    )
    assert project_dir.exists()

    # -------------------------------------------------------------
    # 1. Wizard Intake & AI Decision
    # -------------------------------------------------------------
    prompt = "A 10-second cinematic teaser showing the vast red canyon on Mars under the Martian sun"
    wizard = ProductionWizard(mode=WizardMode.GUIDED, prompt=prompt)

    # Prompt explicitly contains duration -> extracted automatically
    assert not wizard.should_ask_duration()
    assert "duration" in wizard.decisions
    assert wizard.decisions["duration"].selection_mode == SelectionMode.USER_SELECTED
    assert "10" in str(wizard.decisions["duration"].selected_value)

    # AI Decision on enhancement strategy
    from lib.production_wizard import DecisionRecord
    wizard.record_decision(
        "video_quality_enhancement",
        DecisionRecord(
            category="enhancement_selection",
            subject="Video Quality Enhancer profile",
            selection_mode=SelectionMode.AI_DECIDED,
            selected_value="cinematic",
            decision_reason="Cinematic mood treatment enhances Martian terrain depth and dynamic range",
            constraints_considered=["user_prompt_intent", "cinematic_pipeline"],
            confidence=0.90,
        ),
    )

    # Human enhancement is not applicable for landscape
    wizard.record_decision(
        "ai_human_enhancement",
        DecisionRecord(
            category="enhancement_selection",
            subject="AI Human Enhancer",
            selection_mode=SelectionMode.NOT_APPLICABLE,
            selected_value="not_applicable",
            decision_reason="Mars canyon landscape contains no human subjects",
            confidence=1.0,
        ),
    )

    # -------------------------------------------------------------
    # 2. Proposal Packet
    # -------------------------------------------------------------
    proposal = {
        "version": "1.0",
        "concept_options": [
            {
                "id": "c1",
                "title": "Valles Marineris Descent",
                "hook": "Descent into the deepest canyon in the solar system.",
                "narrative_structure": "journey",
                "visual_approach": "Dramatic camera flyover revealing reddish ochre canyon walls",
                "target_duration_seconds": 10.0,
                "key_points": ["Ancient geological forces", "Immense scale of Valles Marineris"],
                "why_this_works": "Mars canyon flyovers create immediate visceral cinematic scale",
            },
            {
                "id": "c2",
                "title": "Martian Dawn Horizon",
                "hook": "Witnessing the sun break over Olympus Mons.",
                "narrative_structure": "comparison",
                "visual_approach": "Atmospheric dust glow",
                "target_duration_seconds": 10.0,
                "key_points": ["Thin atmosphere optics", "Towering volcanoes"],
                "why_this_works": "High aesthetic contrast",
            },
            {
                "id": "c3",
                "title": "Curiosity Footsteps",
                "hook": "Traces in the red sands that will outlast civilizations.",
                "narrative_structure": "analogy",
                "visual_approach": "Rover wheel tracks leading to infinity",
                "target_duration_seconds": 10.0,
                "key_points": ["Permanence of tracks in no-wind depressions", "Exploration history"],
                "why_this_works": "Evocative human connection",
            },
        ],
        "selected_concept": {
            "concept_id": "c1",
            "rationale": "Strongest narrative alignment with prompt intent",
        },
        "production_plan": {
            "pipeline": "cinematic",
            "stages": [
                {
                    "stage": "compose",
                    "tools": [{"tool_name": "video_compose", "role": "composition", "available": True}],
                    "approach": "Compose procedural landscape terrain with ambient sound",
                },
                {
                    "stage": "enhancement",
                    "tools": [{"tool_name": "video_quality_enhancer", "role": "video enhancement", "available": True}],
                    "approach": "Apply cinematic contrast and edge definition",
                },
            ],
            "delivery_promise": {
                "promise_type": "motion_led",
                "motion_required": True,
                "tone_mode": "cinematic",
                "quality_floor": "broadcast",
                "approved_fallback": None,
            },
            "renderer_family": "cinematic-trailer",
            "render_runtime": "ffmpeg",
            "composition_mode": "atelier",
        },
        "cost_estimate": {
            "total_estimated_usd": 0.0,
            "line_items": [
                {"tool": "video_quality_enhancer", "operation": "cinematic_finish", "estimated_usd": 0.0}
            ],
            "budget_verdict": "within_budget",
        },
        "approval": {
            "status": "approved",
            "user_notes": "Approved for 10s preview render",
        },
    }
    validate_artifact("proposal_packet", proposal)

    # -------------------------------------------------------------
    # 3. 3D Scene Specification & Three.js Validation
    # -------------------------------------------------------------
    scene_data = {
        "id": "mars_canyon_hero",
        "type": "generated",
        "narrative_role": "Valles Marineris flythrough",
        "description": "Camera flies through deep Mars canyon under dramatic lighting",
        "start_seconds": 0.0,
        "end_seconds": 10.0,
    }
    scene_spec = CinematicSceneSpec.from_scene_plan_scene(scene_data)
    assert scene_spec.theme == "mars_desert"
    assert scene_spec.terrain_type in ["dune", "canyon", "plain"]

    threejs_spec = scene_spec.to_threejs_world_spec()
    val_res = ThreeJSWorld().execute({
        "operation": "validate",
        "world_spec": threejs_spec,
        "duration_seconds": 10.0,
    })
    assert val_res.success is True
    assert val_res.data["report"]["valid"] is True

    # -------------------------------------------------------------
    # 4. Initial Composed Render (10s video)
    # -------------------------------------------------------------
    renders_dir = project_dir / "renders"
    composed_path = renders_dir / "mars_composed.mp4"

    # Generate 10-second 640x360 synthetic cinematic video with ambient tone
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "mptestsrc=rate=30:duration=10",
        "-f", "lavfi", "-i", "sine=frequency=110:duration=10",
        "-vf", "scale=640:360,format=yuv420p",
        "-c:v", "libx264", "-crf", "22",
        "-c:a", "aac",
        str(composed_path),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    assert composed_path.exists()
    assert composed_path.stat().st_size > 0

    # -------------------------------------------------------------
    # 5. Initial QA
    # -------------------------------------------------------------
    vqa = VisualQA()
    qa_probe = vqa.execute({"operation": "probe", "input_path": str(composed_path)})
    assert qa_probe.success is True
    assert qa_probe.data["width"] == 640
    assert qa_probe.data["height"] == 360
    assert abs(qa_probe.data["duration"] - 10.0) < 0.5

    # -------------------------------------------------------------
    # 6. Video Quality Enhancer (Cinematic Profile)
    # -------------------------------------------------------------
    vqe = VideoQualityEnhancer()
    enhanced_path = renders_dir / "mars_enhanced.mp4"

    vqe_res = vqe.execute({
        "input_path": str(composed_path),
        "output_path": str(enhanced_path),
        "profile": "cinematic",
        "selection_mode": "ai_decided",
        "decision_reason": "Cinematic contrast for Mars landscape",
    })
    assert vqe_res.success is True, vqe_res.error
    assert enhanced_path.exists()
    assert composed_path.exists()  # Original strictly preserved!

    vq_report = vqe_res.data["report"]
    assert vq_report["status"] == "completed"
    assert vq_report["qa_results"]["output_decodable"] is True
    assert vq_report["qa_results"]["audio_preserved"] is True
    validate_artifact("enhancement_report", vq_report)

    # -------------------------------------------------------------
    # 7. AI Human Enhancer (Verifies Not Applicable on Landscape)
    # -------------------------------------------------------------
    human_enhancer = AIHumanEnhancer()
    final_output_path = renders_dir / "mars_final.mp4"

    human_res = human_enhancer.execute({
        "input_path": str(enhanced_path),
        "output_path": str(final_output_path),
        "profile": "natural",
    })
    assert human_res.success is True, human_res.error
    human_report = human_res.data["report"]
    # Verified: not applicable, no faces detected, untouched video preserved
    assert human_report["status"] == "skipped"
    assert human_report["enhancers"]["ai_human"]["selection_mode"] == "not_applicable"
    assert human_report["enhancers"]["ai_human"]["human_subjects_detected"] is False
    validate_artifact("enhancement_report", human_report)

    # -------------------------------------------------------------
    # 8. Before / After Comparison & Final Probe Verification
    # -------------------------------------------------------------
    comp_probe = vqa.execute({"operation": "probe", "input_path": str(composed_path)})
    enh_probe = vqa.execute({"operation": "probe", "input_path": str(enhanced_path)})

    assert comp_probe.success and enh_probe.success
    assert comp_probe.data["duration"] == pytest.approx(enh_probe.data["duration"], abs=0.5)
    assert comp_probe.data["has_audio"] == enh_probe.data["has_audio"]
    assert composed_path.stat().st_size > 0
    assert enhanced_path.stat().st_size > 0

    # -------------------------------------------------------------
    # 9. Checkpoint Validation across Pipeline
    # -------------------------------------------------------------
    from tests.contracts.test_phase0_contracts import sample_artifact
    project_id = "mars-cinematic-demo"
    pipeline_dir = tmp_path / "projects"

    # Write predecessor checkpoints to satisfy stage gating & prerequisites
    preceding_stages = [
        ("research", False),
        ("proposal", True),
        ("script", True),
        ("scene_plan", True),
        ("assets", True),
        ("edit", True),
        ("compose", True),
    ]

    for stage_name, req_approval in preceding_stages:
        art_name = CANONICAL_STAGE_ARTIFACTS[stage_name]
        art_data = proposal if stage_name == "proposal" else sample_artifact(art_name)
        write_checkpoint(
            project_id=project_id,
            stage=stage_name,
            status="completed",
            artifacts={art_name: art_data},
            pipeline_type="cinematic",
            pipeline_dir=pipeline_dir,
            human_approved=req_approval,
        )

    # Write enhancement checkpoint
    write_checkpoint(
        project_id=project_id,
        stage="enhancement",
        status="completed",
        artifacts={"enhancement_report": vq_report},
        pipeline_type="cinematic",
        pipeline_dir=pipeline_dir,
    )

    # Verify project files exist
    assert (project_dir / "checkpoint_proposal.json").exists()
    assert (project_dir / "checkpoint_enhancement.json").exists()
