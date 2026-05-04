import json
import subprocess
from pathlib import Path
import time
from PIL import Image
import whisper

# Load missing videos
with open('/home/ml/smb_videos_to_process.txt', 'r') as f:
    missing = [line.strip() for line in f if line.strip()]

print(f'Found {len(missing)} videos to process')
print(f'Loading Whisper...')
model = whisper.load_model('base')
print('Whisper loaded')

output_dir = Path('/home/ml/smb_processor')
raw_dir = output_dir / 'videos' / 'raw'
frames_dir = output_dir / 'frames'
processed_dir = output_dir / 'output'

for d in [raw_dir, frames_dir, processed_dir]:
    d.mkdir(parents=True, exist_ok=True)

def download(vid):
    output = raw_dir / f'{vid}.mp4'
    if output.exists():
        return output
    url = f'https://www.youtube.com/watch?v={vid}'
    r = subprocess.run(['yt-dlp', '-f', 'best[ext=mp4]', '-o', str(output), url],
                      capture_output=True, text=True, timeout=300)
    return output if r.returncode == 0 else None

def transcribe(video_path):
    audio = raw_dir / f'{video_path.stem}.mp3'
    if not audio.exists():
        r = subprocess.run(['ffmpeg', '-i', str(video_path), '-vn', '-acodec', 'libmp3lame',
                          '-ar', '16000', '-ac', '1', str(audio)],
                         capture_output=True, text=True)
    r = model.transcribe(str(audio), language='en')
    return [{'start': s['start'], 'end': s['end'], 'text': s['text']} for s in r['segments']]

def capture_frames(video_path, interval=10):
    r = subprocess.run(['ffmpeg', '-i', str(video_path), '-vf', f'fps=1/{interval}',
                      '-start_number', '0',
                      str(frames_dir / f'{video_path.stem}_%04d.jpg')],
                     capture_output=True, text=True)
    if r.returncode != 0:
        return []
    frames = sorted(frames_dir.glob(f'{video_path.stem}_*.jpg'))
    return [{'timestamp': i*interval, 'path': str(f)} for i, f in enumerate(frames)]

def analyze_frame(path, timestamp):
    frame = {'timestamp': timestamp, 'visual_type': 'unknown', 'confidence': 0.0, 'description': ''}
    try:
        img = Image.open(path)
        w, h = img.size
        if w > h * 1.5:
            frame['visual_type'] = 'chart_or_diagram'
            frame['description'] = 'Wide-format chart or diagram'
            frame['confidence'] = 0.7
        elif w == h:
            frame['visual_type'] = 'square_preview'
            frame['description'] = 'Square mobile preview'
            frame['confidence'] = 0.8
        else:
            frame['visual_type'] = 'host_explanation'
            frame['description'] = 'Portrait host explanation'
            frame['confidence'] = 0.6
    except Exception as e:
        frame['error'] = str(e)
    return frame

# Process each video
for i, vid in enumerate(missing, 1):
    print(f'\n[{i}/{len(missing)}] Processing: {vid}')
    
    video = download(vid)
    if not video:
        print(f'  Download failed')
        continue
    
    print(f'  Transcribing...')
    transcript = transcribe(video)
    
    print(f'  Capturing frames...')
    frames = capture_frames(video, interval=10)
    
    result = {'video_id': vid, 'segments': transcript, 'visual_entries': []}
    
    for frame in frames:
        analysis = analyze_frame(frame['path'], frame['timestamp'])
        relevant = [t['text'][:200] for t in transcript 
                   if t['start'] <= frame['timestamp'] <= t['end']]
        m, s = int(frame['timestamp']//60), int(frame['timestamp']%60)
        entry = {
            'timestamp': frame['timestamp'],
            'timecode': f'{m:02d}:{s:02d}',
            'visual_type': analysis['visual_type'],
            'description': analysis['description'],
            'confidence': analysis.get('confidence', 0),
            'transcript_context': relevant[0] if relevant else None
        }
        result['visual_entries'].append(entry)
    
    # Save
    out_path = processed_dir / f'{vid}_processed.json'
    with open(out_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f'  Saved: {len(frames)} frames, {len(transcript)} segments')
    
    time.sleep(2)

print('\nDone!')
