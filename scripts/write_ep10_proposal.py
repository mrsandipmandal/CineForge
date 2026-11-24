import json
from pathlib import Path
from datetime import datetime, timezone

project_dir = Path("f:/CineForge/projects/ramayana-ep10-bharat-kaikeyi-dhikkar")
now = datetime.now(timezone.utc).isoformat()

# 1. Research Checkpoint
research_data = {
    "version": "1.0",
    "project_id": "ramayana-ep10-bharat-kaikeyi-dhikkar",
    "pipeline_type": "mythological_shorts",
    "stage": "research",
    "status": "completed",
    "timestamp": now,
    "checkpoint_policy": "guided",
    "human_approval_required": False,
    "human_approved": True,
    "artifacts": {
        "research_brief": {
            "version": "1.0",
            "title": "भरत का अयोध्या आगमन, कैकेयी को धिक्कार एवं भ्रातृ-प्रेम का संकल्प",
            "scriptures": ["Valmiki Ramayana (Ayodhya Kand, Sarga 70-75)", "Ramcharitmanas (Ayodhya Kand, Doha 155-175)"],
            "core_conflict": "Bharata returns from Kekaya to find Ayodhya plunged in mourning, discovers his father Dasharatha has died of grief, and that Kaikeyi exiled Rama for his sake. In fury and pure devotion, he denounces Kaikeyi, rejects the throne, and vows to restore Rama.",
            "characters": ["Prince Bharata", "Shatrughna", "Rani Kaikeyi", "Mata Kausalya", "Maharshi Vasishtha"]
        }
    }
}
with open(project_dir / "checkpoint_research.json", "w", encoding="utf-8") as f:
    json.dump(research_data, f, indent=2, ensure_ascii=False)

# 2. Proposal Checkpoint
proposal_data = {
    "version": "1.0",
    "project_id": "ramayana-ep10-bharat-kaikeyi-dhikkar",
    "pipeline_type": "mythological_shorts",
    "stage": "proposal",
    "status": "completed",
    "timestamp": now,
    "checkpoint_policy": "guided",
    "human_approval_required": True,
    "human_approved": False,
    "artifacts": {
        "proposal_packet": {
            "version": "1.0",
            "title": "रामायण • भाग १० : भरत का अयोध्या आगमन, कैकेयी को धिक्कार एवं भ्रातृ-प्रेम का संकल्प",
            "target_duration_seconds": 90,
            "aspect_ratio": "9:16",
            "resolution": "1080x1920",
            "fps": 30,
            "audio_strategy": "Fish Audio s2-pro (Sanjay Deep Storyteller) + Sombre Tragic Tanpura & Veena Drone",
            "visual_strategy": "Genuine Shrimad Ramayan (2024) TV clips (Ep 37-40), Smart 9:16 vertical crop with zero watermarks",
            "scenes": [
                {
                    "scene_number": 1,
                    "title": "अशुभ स्वप्न और दूतों का आगमन",
                    "situation": "ननिहाल कैकेय देश में भरत का व्याकुल होना, दूतों द्वारा अयोध्या लौटने का संदेश देना।"
                },
                {
                    "scene_number": 2,
                    "title": "उजाड़ व शोकमग्न अयोध्या में प्रवेश",
                    "situation": "अयोध्या के सूने मार्ग, बंद द्वार और प्रजा के आंसुओं को देखकर भरत का आशंकित होना।"
                },
                {
                    "scene_number": 3,
                    "title": "कैकेयी के राजप्रासाद में आगमन",
                    "situation": "हर्षोल्लास से भरी कैकेयी द्वारा भरत की आरती उतारना और पिता के बारे में पूछना।"
                },
                {
                    "scene_number": 4,
                    "title": "दशरथ मरण का वज्रपात",
                    "situation": "कैकेयी का निर्लज्जता से कहना— 'महाराज दशरथ स्वर्ग सिधार गए, पुत्र!'"
                },
                {
                    "scene_number": 5,
                    "title": "श्री राम का वनवास रहस्योद्घाटन",
                    "situation": "भरत के पूछने पर कैकेयी का कहना— 'तेरे लिए निष्कंटक राज्य पाने को मैंने राम को १४ वर्ष वनवास भेजा!'"
                },
                {
                    "scene_number": 6,
                    "title": "भरत का महाक्रोध एवं कैकेयी को धिक्कार",
                    "situation": "भरत का कांपते हुए मुकुট फेंकना और गर्जना— 'तू मेरी माता नहीं, रघुकुल की कालरात्रि है!'"
                },
                {
                    "scene_number": 7,
                    "title": "राजसिंहासन का तिरस्कार",
                    "situation": "'जिस राज्य के लिए मेरे भ्राता राम वन गए, उस सिंहासन पर बैठना मेरे लिए विष के समान है!'"
                },
                {
                    "scene_number": 8,
                    "title": "माता कौशल्या के चरणों में विलाप",
                    "situation": "शोकग्रस्त माता कौशल्या के चरणों में गिरकर भरत का अश्रुपूरित निर्दोषता का प्रमाण देना।"
                },
                {
                    "scene_number": 9,
                    "title": "माता कौशल्या का वात्सल्यपूर्ण आलिंगन",
                    "situation": "कौशल्या का भरत के निष्कलंक प्रेम को पहचान कर उन्हें हृदय से लगाना और सांत्वना देना।"
                },
                {
                    "scene_number": 10,
                    "title": "चित्रकूट गमन व पादुका का महासंकल्प",
                    "situation": "भरत का संपूर्ण अयोध्यावासियों के समक्ष दृढ़ संकल्प— 'मैं वन जाकर प्रभु राम को वापस लाऊंगा!'"
                }
            ]
        }
    }
}
with open(project_dir / "checkpoint_proposal.json", "w", encoding="utf-8") as f:
    json.dump(proposal_data, f, indent=2, ensure_ascii=False)

print("Research and Proposal checkpoints written successfully for Ep 10!")
