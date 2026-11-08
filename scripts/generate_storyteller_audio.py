import asyncio
import edge_tts
from pathlib import Path
import subprocess

audio_dir = Path('projects/rahasyalok-quantum-entanglement/assets/audio')
audio_dir.mkdir(parents=True, exist_ok=True)

sections = [
    {
        'id': 'sec_01',
        'text': 'साल 1935... अल्बर्ट आइंस्टीन एक ऐसे रहस्य से कांप उठे, जिसने विज्ञान की दुनिया हिला दी!'
    },
    {
        'id': 'sec_02',
        'text': 'कल्पना कीजिए... दो कण। अरबों किलोमीटर दूर! लेकिन एक को छूते ही... दूसरा उसी पल बदल जाता है!'
    },
    {
        'id': 'sec_03',
        'text': 'बिना किसी तार या सिग्नल के — प्रकाश से भी तेज़! आइंस्टीन ने इसे कहा — स्पूकी एक्शन... भूतों जैसी हरकत!'
    },
    {
        'id': 'sec_04',
        'text': 'आज आधुनिक विज्ञान ने साबित किया कि यह क्वांटम उलझन सच है... और इसी पर भविष्य के सुपर कंप्यूटर बन रहे हैं!'
    },
    {
        'id': 'sec_05',
        'text': 'क्या हमारा ब्रह्मांड एक अनदेखा मायाजाल है? कमेंट में बताइए, और ऐसे ही रहस्यों के लिए सब्सक्राइब करें रहस्यलोक को!'
    }
]

async def generate():
    total_dur = 0.0
    for sec in sections:
        # Natural +5% rate and -1Hz pitch for deep broadcast storytelling resonance
        comm = edge_tts.Communicate(sec['text'], 'hi-IN-MadhurNeural', rate='+5%', pitch='-1Hz')
        out_file = audio_dir / f"{sec['id']}.mp3"
        await comm.save(str(out_file))
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(out_file)]
        dur = float(subprocess.check_output(cmd, text=True).strip())
        total_dur += dur
        print(f"Generated {sec['id']}.mp3: duration = {dur:.2f}s")
    print(f"Total voiceover duration = {total_dur:.2f}s")

if __name__ == '__main__':
    asyncio.run(generate())
