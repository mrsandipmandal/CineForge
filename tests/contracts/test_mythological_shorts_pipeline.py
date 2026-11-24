import pytest
from lib.pipeline_loader import load_pipeline, get_stage_order, get_stage_human_approval_default

def test_mythological_shorts_pipeline_load():
    manifest = load_pipeline("mythological_shorts")
    assert manifest["name"] == "mythological_shorts"
    assert manifest["category"] == "cinematic"
    assert manifest["stability"] == "production"

def test_stage_order():
    manifest = load_pipeline("mythological_shorts")
    order = get_stage_order(manifest)
    assert order == ["research", "proposal", "script", "scene_plan", "assets", "edit", "compose", "publish"]

def test_required_skills():
    manifest = load_pipeline("mythological_shorts")
    assert "mythological-video-production" in manifest["required_skills"]

def test_authenticity_contract():
    manifest = load_pipeline("mythological_shorts")
    contract = manifest["metadata"]["authenticity_contract"]
    
    # Wardrobe
    wardrobe = contract["wardrobe"]["male_royal_attire"]
    assert "Gowns, sarees, Victorian capes, Greek tunics, or unisex dresses on male monarchs" in wardrobe["strictly_forbidden"]
    assert "Pristine pleated silk Dhoti (धोती) or Pancha with intricate Zari golden brocade border (कशीदाकारी)" in wardrobe["mandatory_specifications"]["lower_body"]
    
    # Weaponry
    weaponry = contract["weaponry_and_mantras"]
    assert "Sacred Devanagari Sanskrit mantras 'ॐ ॐ नमः शिवाय ॐ', Trishul, and Damru engravings" in weaponry["mandatory_specifications"]["shiva_astras"]
    
    # Narration
    audio = contract["audio_narration"]
    assert "Sanjay Deep Authoritative Storyteller baritone" in audio["voice_archetype"]
    assert audio["mastering_chain"]["integrated_loudness_target_lufs"] == -14.0

def test_human_approval_gates():
    manifest = load_pipeline("mythological_shorts")
    assert get_stage_human_approval_default(manifest, "proposal") is True
    assert get_stage_human_approval_default(manifest, "assets") is True
    assert get_stage_human_approval_default(manifest, "research") is False
