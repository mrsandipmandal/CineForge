import yt_dlp

ydl = yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True})
queries = [
    'Shrimad Ramayan Episode 37 Sony SAB',
    'Shrimad Ramayan Episode 38 Sony SAB',
    'Shrimad Ramayan Episode 39 Sony SAB',
    'Shrimad Ramayan Episode 40 Sony SAB',
    'Shrimad Ramayan Episode 41 Sony SAB'
]

for q in queries:
    res = ydl.extract_info(f"ytsearch3:{q}", download=False)
    for e in res.get('entries', []):
        if 'Sony SAB' in e.get('title', '') or 'Sony' in str(e):
            print(f"{e['id']} | {e['title']}")
