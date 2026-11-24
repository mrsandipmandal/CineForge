#!/usr/bin/env python3
"""Generate Ramayana Episode 7 content: Manthara's Midnight Plot.

Sets up:
- projects/ramayana-manthara-chakranta/project.json
- projects/ramayana-manthara-chakranta/artifacts/script.json (7 scenes, total duration 58.5s)
- projects/ramayana-manthara-chakranta/artifacts/timestamps.json (30 fps)
- projects/ramayana-manthara-chakranta/artifacts/youtube_metadata.txt
"""

import json
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ID = "ramayana-manthara-chakranta"
PROJECT_DIR = REPO_ROOT / "projects" / PROJECT_ID
ARTIFACTS_DIR = PROJECT_DIR / "artifacts"


def build_ep7_data():
    """Build canonical data structures for Ramayana Episode 7."""
    project_metadata = {
        "project_id": PROJECT_ID,
        "id": PROJECT_ID,
        "title": "রামাযণ পর্ব ৭ — মন্থরার কুটিল চক্রান্ত ও দশরথের কালরাত্রি",
        "name": "Ramayana Ep 7: Manthara's Midnight Plot",
        "pipeline_type": "mythological_shorts",
        "type": "mythological_shorts",
        "created_at": "2026-11-19T00:40:00+05:30",
        "aspect_ratio": "9:16",
        "language": "bn-IN",
        "target_duration": 58.5,
        "status": "ready"
    }

    scenes_spec = [
        {
            "id": 1,
            "start_time": 0.0,
            "end_time": 8.5,
            "duration": 8.5,
            "title": "Scene 1: অযোধ্যায় আনন্দের জোয়ার ও আসন্ন অভিষেক",
            "narration_bn": "অযোধ্যায় আনন্দের মহোৎসব! প্রভাত হলেই রঘুকুলতিলক শ্রীরামের রাজ্যাভিষেক। চারদিকে জয়ধ্বনি আর আলোকমালা, কিন্তু রাজপ্রাসাদের গভীর অন্ধকারে ঘনাচ্ছে এক মারাত্মক চক্রান্ত।",
            "subtitle_bn": "প্রভাত হলেই শ্রীরামের রাজ্যাভিষেক... কিন্তু প্রাসাদের অন্ধকারে ঘনাচ্ছে অমঙ্গল!",
            "visual_prompt": "Masterpiece oil painting in the style of Raja Ravi Varma and divine cinematic Indian epic art, ancient Vedic Ayodhya palace illuminated with thousands of golden clay diyas, festive decorations, joyful citizens celebrating in royal courtyards, while dark ominous midnight shadows creep along ornate marble corridors, 8K resolution, volumetric golden lighting, cinematic vertical composition 9:16.",
            "mood": "festive_yet_ominous"
        },
        {
            "id": 2,
            "start_time": 8.5,
            "end_time": 16.5,
            "duration": 8.0,
            "title": "Scene 2: কুটিল মন্থরার বিষাক্ত চক্রান্ত",
            "narration_bn": "কুটিলদাসী মন্থরা ছুটে গেল রানী কৈকেয়ীর মহলে। বিষাক্ত ফিসফিসানিতে সে উস্কে দিল হিংসার আগুন—'শ্রীরাম রাজা হলে তোমার পুত্র ভরত হবে চিরদাস, ধ্বংস হবে তোমার রাজমহিষীর মর্যাদা!'",
            "subtitle_bn": "কুটিলদাসী মন্থরা রানী কৈকেয়ীর কানে ঢালল বিষাক্ত সন্দেহের বিষ!",
            "visual_prompt": "Masterpiece oil painting in the style of Raja Ravi Varma, sinister hunchbacked maidservant Manthara whispering malice into Queen Kaikeyi's ear in the royal chamber, flickering oil lamp casting sinister distorted shadows on the ancient stone wall, Kaikeyi dressed in regal Vedic silk saree looking conflicted, 8K resolution, dramatic chiaroscuro lighting, emotional tension, vertical 9:16.",
            "mood": "conspiratorial_dark"
        },
        {
            "id": 3,
            "start_time": 16.5,
            "end_time": 25.0,
            "duration": 8.5,
            "title": "Scene 3: কৈকেয়ীর ক্রোধ ও অন্ধকার কোপভবন",
            "narration_bn": "মন্থরার কুটিল চক্রান্তে অন্ধ হয়ে রানী কৈকেয়ী ছিঁড়ে ফেললেন রাজকীয় রত্নহার। রাজবেশ ত্যাগ করে তিনি প্রবেশ করলেন অন্ধকার কোপভবনে—ধূলিশয্যায় জ্বলতে লাগল প্রলয়ঙ্করী প্রতিহিংসা।",
            "subtitle_bn": "মন্থরার বিষে উন্মাদ কৈকেয়ী প্রবেশ করলেন অন্ধকার কোপভবনে!",
            "visual_prompt": "Masterpiece oil painting in the style of Raja Ravi Varma, Queen Kaikeyi furiously discarding her precious Navaratna pearl necklace and royal golden ornaments onto the floor of the Kopabhavan anger chamber, untied dark hair, disheveled dark crimson attire, lying on bare cold stone floor, dim ominous torchlight, cinematic Indian mythology, vertical 9:16.",
            "mood": "furious_vengeful"
        },
        {
            "id": 4,
            "start_time": 25.0,
            "end_time": 34.0,
            "duration": 9.0,
            "title": "Scene 4: মহারাজা দশরথের নিশীথ আগমন",
            "narration_bn": "গভীর রাতে আনন্দচিত্তে কোপভবনে এলেন বৃদ্ধ মহারাজা দশরথ। কিন্তু প্রিয়তমা রানীকে মাটিতে ধূসর বেশে ক্রন্দনরত দেখে শিউরে উঠলেন মহারাজ—'দেবী, কীসের এই নিদারুণ শোক? কী চাও তুমি?'",
            "subtitle_bn": "আনন্দে বিহ্বল বৃদ্ধ রাজা দশরথ কোপভবনে প্রবেশ করলেন...",
            "visual_prompt": "Masterpiece oil painting in the style of Raja Ravi Varma, elderly Emperor Dasharatha wearing royal golden mukut crown, pleated silk dhoti with intricate zari border and regal angavastram across shoulders, entering dark Kopabhavan chamber holding ornate golden lamp, reaching out with tears in his eyes towards weeping Kaikeyi, 8K resolution, dramatic emotional lighting, vertical 9:16.",
            "mood": "heartbreaking_agony"
        },
        {
            "id": 5,
            "start_time": 34.0,
            "end_time": 42.5,
            "duration": 8.5,
            "title": "Scene 5: কৈকেয়ীর নিষ্ঠুর দুই বর",
            "narration_bn": "কুটিল হাস্যে কৈকেয়ী চাইলেন সেই প্রতিশ্রুত দুই বর—'প্রথম বরে আমার পুত্র ভরতের হোক অযোধ্যার রাজ্যাভিষেক, আর দ্বিতীয় বরে শ্রীরামের জন্য চোদ্দ বছরের কঠোর বনবাস!'",
            "subtitle_bn": "'ভরতের রাজ্যাভিষেক, আর শ্রীরামের চোদ্দ বছরের কঠোর বনবাস!'",
            "visual_prompt": "Masterpiece oil painting in the style of Raja Ravi Varma, Queen Kaikeyi rising like a vengeful empress in dim royal chamber, pointing two fingers demanding two fatal boons from broken King Dasharatha, stone-cold stern expression, ancient Vedic architecture, ominous shadows, high drama, vertical 9:16.",
            "mood": "cruel_demand"
        },
        {
            "id": 6,
            "start_time": 42.5,
            "end_time": 51.0,
            "duration": 8.5,
            "title": "Scene 6: মহারাজা দশরথের মর্মান্তিক পতন",
            "narration_bn": "বজ্রাঘাতের মতো স্তব্ধ হলো মহারাজা দশরথের বক্ষ! ধূলিতলে লুটিয়ে পড়ে হাহাকার করে উঠলেন মহারাজ—'কৈকেয়ী, আমার সর্বস্ব নাও, আমার প্রাণ নাও, কিন্তু আমার নয়নের মণি শ্রীরামকে কেড়ে নিও না!'",
            "subtitle_bn": "'কৈকেয়ী, আমার প্রাণ নাও, কিন্তু আমার রামকে বনবাস দিও না!'",
            "visual_prompt": "Masterpiece oil painting in the style of Raja Ravi Varma, Emperor Dasharatha collapsing onto palace marble floor in unbearable grief, golden mukut slipping, hands clasped pleading in agony, heart-wrenching tragedy, royal Vedic palace interior, dramatic volumetric spotlight on fallen monarch, 8K resolution, vertical 9:16.",
            "mood": "tragic_collapse"
        },
        {
            "id": 7,
            "start_time": 51.0,
            "end_time": 58.5,
            "duration": 7.5,
            "title": "Scene 7: অযোধ্যার কালরাত্রি ও ভাগ্যনির্ধারণ",
            "narration_bn": "নিষ্ঠুর কৈকেয়ী রইলেন অনড়, সংজ্ঞাহীন দশরথের বুক চিরে নামল কালরাত্রি! সূর্যবংশের ভবিতব্যে কী করবেন শ্রীরাম? কমেন্টে লিখুন 'জয় শ্রীরাম', সাবস্ক্রাইব করুন পরের পর্বের জন্য!",
            "subtitle_bn": "নিষ্ঠুর কৈকেয়ী, অচেতন দশরথ... এরপর কী করবেন শ্রীরাম?",
            "visual_prompt": "Masterpiece oil painting in the style of Raja Ravi Varma, dark silent midnight over ancient Ayodhya palace under a blood-red moon, Emperor Dasharatha lying unconscious attended by grieving shadows while Queen Kaikeyi stands unyielding like stone, cinematic cliffhanger, epic mythological Sanskrit aura, vertical 9:16.",
            "mood": "epic_cliffhanger"
        }
    ]

    # Populate fallback keys for maximum compatibility
    for s in scenes_spec:
        s["narration"] = s["narration_bn"]
        s["subtitle"] = s["subtitle_bn"]

    total_duration = round(sum(s["duration"] for s in scenes_spec), 2)

    script_data = {
        "version": "1.0",
        "project_id": PROJECT_ID,
        "title": "রামাযণ পর্ব ৭ — মন্থরার কুটিল চক্রান্ত ও দশরথের কালরাত্রি",
        "total_duration": total_duration,
        "total_duration_seconds": total_duration,
        "scenes": scenes_spec,
        "sections": [
            {
                "id": f"s{s['id']}",
                "label": s["title"],
                "text": s["narration_bn"],
                "start_seconds": s["start_time"],
                "end_seconds": s["end_time"]
            }
            for s in scenes_spec
        ]
    }

    fps = 30
    timestamps_data = {
        "project_id": PROJECT_ID,
        "fps": fps,
        "total_duration": total_duration,
        "total_frames": int(round(total_duration * fps)),
        "scenes": [
            {
                "id": s["id"],
                "title": s["title"],
                "narration": s["narration_bn"],
                "narration_bn": s["narration_bn"],
                "subtitle": s["subtitle_bn"],
                "subtitle_bn": s["subtitle_bn"],
                "start_time": s["start_time"],
                "end_time": s["end_time"],
                "duration": s["duration"],
                "start_frame": int(round(s["start_time"] * fps)),
                "end_frame": int(round(s["end_time"] * fps)),
                "duration_frames": int(round(s["duration"] * fps)),
                "file": f"scene_{s['id']}.mp3"
            }
            for s in scenes_spec
        ]
    }

    youtube_metadata_text = """================================================================================
🏹 রামায়ণ পর্ব ৭ — মন্থরার কুটিল চক্রান্ত ও মহারাজা দশরথের কালরাত্রি (Manthara's Midnight Plot)
================================================================================

🎯 YOUTUBE VIRAL TITLES (HIGH CTR):
1. মন্থরার কুটিল চক্রান্তে ধ্বংস হলো অযোধ্যার আনন্দ! রানী কৈকেয়ীর দুটি সর্বনাশা বর 😱🚩 | রামায়ণ পর্ব ৭ #shorts
2. রামের বনবাস চাইলেন কৈকেয়ী! রাজা দশরথের বুকফাটা আর্তনাদ 😭💔 | Ramayana Episode 7 #shorts #ramayan
3. এক রাতের ষড়যন্ত্রে বদলে গেল রামায়ণের ইতিহাস! মন্থরা ও কৈকেয়ীর কালরাত্রি 🔥✨ #viralshorts #shriram

--------------------------------------------------------------------------------
📝 DESCRIPTION & STORYTELLING:
অযোধ্যায় তখন আনন্দের মহোৎসব—প্রভাত হলেই রঘুকুলতিলক শ্রীরামের রাজ্যাভিষেক!
কিন্তু রাজপ্রাসাদের গভীর অন্ধকারে কুটিলদাসী মন্থরা রানী কৈকেয়ীর কানে ঢালল বিষাক্ত সন্দেহের বিষ।
কৈকেয়ী দাবি করলেন সেই প্রতিশ্রুত দুই বর—ভরতের রাজ্যাভিষেক এবং শ্রীরামের জন্য চোদ্দ বছরের কঠোর বনবাস!
মহারাজা দশরথ ধূলিশয্যায় লুটিয়ে কেঁদে উঠলেন: "কৈকেয়ী, আমার প্রাণ নাও, কিন্তু আমার রামকে বনবাস দিও না!"
সূর্যবংশের আকাশে নেমে এল এক অভিশপ্ত কালরাত্রি... দেখুন এই রোমহর্ষক ও মর্মস্পর্শী পর্ব!

🚩 কমেন্টে ভক্তিভরে লিখুন: 'জয় শ্রীরাম' 🙏
🔔 রামায়ণের প্রতিটি পর্বের জন্য চ্যানেলটি সাবস্ক্রাইব করে বেল আইকন প্রেস করুন!

--------------------------------------------------------------------------------
🏷️ HASHTAGS & TAGS:
#Ramayan #Manthara #Kaikeyi #Dasharatha #ShriRam #Ayodhya #RamVanvas #SanatanDharma #HinduMythology #LordRama #RamanandSagar #Shorts #YouTubeShorts #Reels #ViralShorts #MythologyShorts #BengaliRamayan

Tags: Ramayan Episode 7, Manthara Chakranta, Kaikeyi Boons, Dasharatha Agony, Ram Vanvas, Ayodhya Kaalratri, Bengali Ramayan Shorts, Sandip Voice Ramayan, 9x16 Ramayan Shorts, Sanatan Shorts

--------------------------------------------------------------------------------
📌 PINNED COMMENT:
"মহারাজা দশরথের এই বুকফাটা হাহাকার দেখে আপনার চোখেও কি জল এসে গেল? কমেন্টে শ্রদ্ধায় লিখুন 'জয় শ্রীরাম' 🚩🙏 এবং প্রভু শ্রীরামের পরবর্তী সিদ্ধান্তের জন্য চ্যানেলটি এখনই সাবস্ক্রাইব করুন!"
"""

    return project_metadata, script_data, timestamps_data, youtube_metadata_text


def generate_ep7_content(base_dir=None):
    """Generate all files for Ramayana Episode 7."""
    target_project_dir = Path(base_dir) / PROJECT_ID if base_dir else PROJECT_DIR
    target_artifacts_dir = target_project_dir / "artifacts"

    target_artifacts_dir.mkdir(parents=True, exist_ok=True)

    project_metadata, script_data, timestamps_data, youtube_metadata = build_ep7_data()

    # 1. project.json
    project_file = target_project_dir / "project.json"
    with open(project_file, "w", encoding="utf-8") as f:
        json.dump(project_metadata, f, indent=2, ensure_ascii=False)
    print(f"Generated: {project_file}")

    # 2. script.json
    script_file = target_artifacts_dir / "script.json"
    with open(script_file, "w", encoding="utf-8") as f:
        json.dump(script_data, f, indent=2, ensure_ascii=False)
    print(f"Generated: {script_file}")

    # 3. timestamps.json
    timestamps_file = target_artifacts_dir / "timestamps.json"
    with open(timestamps_file, "w", encoding="utf-8") as f:
        json.dump(timestamps_data, f, indent=2, ensure_ascii=False)
    print(f"Generated: {timestamps_file}")

    # 4. youtube_metadata.txt
    yt_file = target_artifacts_dir / "youtube_metadata.txt"
    with open(yt_file, "w", encoding="utf-8") as f:
        f.write(youtube_metadata)
    print(f"Generated: {yt_file}")

    return {
        "project_dir": str(target_project_dir),
        "total_duration": script_data["total_duration"],
        "scene_count": len(script_data["scenes"]),
    }


if __name__ == "__main__":
    res = generate_ep7_content()
    print(f"Successfully generated Ramayana Ep7 content: {res}")
