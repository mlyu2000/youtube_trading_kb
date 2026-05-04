#!/usr/bin/env python3
"""
GPU-Aware SMB Capital YouTube Video Transcription with Visual Chart/Diagram OCR

Auto-detects CUDA availability and uses appropriate compute device:
- CUDA available: GPU acceleration for Whisper and PaddleOCR
- CUDA unavailable: CPU fallback with reduced precision

Visual Content Detection:
- Portrait frames → Host explanation (75% confidence)
- Landscape frames → Chart/diagram (85% confidence)
- Square frames → Preview/infographic (70% confidence)

OCR Output Schema:
- frame_id: frame identifier
- timestamp: video timestamp (seconds)
- visual_type: portrait/landscape/square
- ocr_results: {text, confidence, bounding_box}
- classification: detected_chart_type (if applicable)

Usage:
    python gpu_transcribe.py --video-id=YLC1234
    python gpu_transcribe.py --video-id=YLC1234 --device=cuda
    python gpu_transcribe.py --video-id=YLC1234 --device=cpu
    python gpu_transcribe.py --video-id=YLC1234 --visual-ocr
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

try:
    import torch
except ImportError:
    torch = None

try:
    import whisper
except ImportError:
    whisper = None

try:
    import cv2
except ImportError:
    cv2 = None


# Configuration
OUTPUT_DIR = Path("/home/ml/smb_processor/output")
FRAMES_DIR = Path("/home/ml/smb_processor/frames")
WHISPER_MODELS = {
    "gpu": "openai/whisper-large-v3-turbo",
    "cpu": "openai/whisper-base"
}

# Visual classification thresholds
ASPECT_RATIO_THRESHOLD = 1.5  # > 1.5 = landscape, < 1 = portrait


def get_device() -> str:
    """Auto-detect available compute device."""
    if torch and torch.cuda.is_available():
        return "cuda"
    return "cpu"


def get_compute_type(device: str) -> str:
    """Select compute type based on device."""
    if device == "cuda":
        return "int8_float16"  # Faster with GPU
    return "int8"


def classify_frame_aspect_ratio(width: int, height: int) -> dict:
    """Classify frame type based on aspect ratio."""
    aspect_ratio = width / height if height > 0 else 0
    
    classification = {
        "aspect_ratio": aspect_ratio,
        "width": width,
        "height": height
    }
    
    if aspect_ratio > ASPECT_RATIO_THRESHOLD:
        classification["visual_type"] = "landscape"
        classification["description"] = "Chart/diagram/price action"
        classification["confidence"] = 0.85
        classification["ocr_purpose"] = "extract_chart_labels_numbers"
    elif aspect_ratio < 1.0:
        classification["visual_type"] = "portrait"
        classification["description"] = "Host explanation/talking head"
        classification["confidence"] = 0.75
        classification["ocr_purpose"] = "extract_name_title"
    else:
        classification["visual_type"] = "square"
        classification["description"] = "Preview/infographic/overlay"
        classification["confidence"] = 0.70
        classification["ocr_purpose"] = "extract_summary_text"
    
    return classification


def extract_audio(video_path: Path, audio_path: Path) -> bool:
    """Extract audio from video using ffmpeg."""
    try:
        command = [
            "ffmpeg", "-i", str(video_path),
            "-vn", "-acodec", "pcm_s16le",
            "-ar", "16000", "-ac", "1",
            str(audio_path), "-y"
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Audio extraction failed: {e}")
        return False


def transcribe_audio(audio_path: Path, device: str, model_name: str) -> dict:
    """Transcribe audio using Whisper with GPU acceleration."""
    if not whisper:
        raise ImportError("whisper package not installed")
    
    print(f"Loading Whisper model: {model_name} on {device}...")
    model = whisper.load_model(model_name)
    
    # Run transcription
    result = model.transcribe(
        str(audio_path),
        device=device,
        language="en",
        fp16=(device == "cuda"),
       低温=False,
        temperature=0.0,
        compression_ratio_threshold=2.4,
        logprob_threshold=-1.0,
        no_speech_threshold=0.6,
        condition_on_previous_text=True,
        initial_prompt=None,
        verbose=False
    )
    
    return result


def extract_frames(video_path: Path, frames_dir: Path, interval: int = 5) -> tuple:
    """Extract frames from video at specified interval with aspect ratio info."""
    if not cv2:
        raise ImportError("opencv-python package not installed")
    
    frames_dir.mkdir(parents=True, exist_ok=True)
    
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps * interval)
    frame_count = 0
    saved_count = 0
    
    frame_info = []
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % frame_interval == 0:
            frame_path = frames_dir / f"frame_{saved_count:06d}.jpg"
            cv2.imwrite(str(frame_path), frame)
            
            # Get frame dimensions and classify
            height, width = frame.shape[:2]
            aspect_info = classify_frame_aspect_ratio(width, height)
            
            frame_info.append({
                "frame_id": f"frame_{saved_count:06d}",
                "timestamp": round(frame_count / fps, 2),
                "width": width,
                "height": height,
                **aspect_info
            })
            
            saved_count += 1
        
        frame_count += 1
    
    cap.release()
    return saved_count, frame_info


def run_visual_ocr(frames_dir: Path, frame_info: list, use_gpu: bool = True) -> dict:
    """Run PaddleOCR on frames with visual type classification.
    
    OCR Schema:
    - frame_id: frame identifier
    - timestamp: video timestamp (seconds)
    - visual_type: portrait/landscape/square
    - description: what this frame type contains
    - ocr_results: [{text, confidence, bounding_box}]
    - detected_chart_type: if applicable (price_chart, bar_chart, line_chart, etc.)
    """
    
    try:
        from paddleocr import PaddleOCR
        
        print("Loading PaddleOCR with GPU:", use_gpu)
        ocr = PaddleOCR(
            use_angle_cls=True,
            use_gpu=use_gpu,
            max_text_length=50,
            lang="en"
        )
        
        results = {}
        
        for frame in frame_info:
            frame_id = frame["frame_id"]
            timestamp = frame["timestamp"]
            frame_path = frames_dir / f"{frame_id}.jpg"
            
            if not frame_path.exists():
                continue
            
            # Run OCR
            ocr_result = ocr.ocr(str(frame_path), cls=True)
            
            # Parse results
            ocr_outputs = []
            detected_chart_keywords = []
            
            if ocr_result and ocr_result[0]:
                for line in ocr_result[0]:
                    text = line[1][0]
                    confidence = line[1][1]
                    bbox = line[0]  # Bounding box: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                    
                    ocr_outputs.append({
                        "text": text,
                        "confidence": round(confidence, 3),
                        "bounding_box": [[float(p[0]), float(p[1])] for p in bbox]
                    })
                    
                    # Keyword detection for chart type
                    text_lower = text.lower()
                    if any(kw in text_lower for kw in ["chart", "diagram", "graph", "plot"]):
                        detected_chart_keywords.append("generic_chart")
                    if any(kw in text_lower for kw in ["price", "stock", "equity", "share"]):
                        detected_chart_keywords.append("price_chart")
                    if any(kw in text_lower for kw in ["volume", "bar", "histogram"]):
                        detected_chart_keywords.append("bar_chart")
                    if any(kw in text_lower for kw in ["support", "resistance", "trend"]):
                        detected_chart_keywords.append("technical_chart")
            
            # Determine chart type based on frame classification + OCR
            visual_type = frame["visual_type"]
            chart_type = None
            
            if visual_type == "landscape":
                # Landscape frames are likely charts
                if detected_chart_keywords:
                    chart_type = detected_chart_keywords[0]
                else:
                    chart_type = "generic_chart"
            
            results[frame_id] = {
                "timestamp": timestamp,
                "visual_type": visual_type,
                "description": frame["description"],
                "confidence": frame["confidence"],
                "ocr_results": ocr_outputs,
                "ocr_confidence_avg": round(sum(r["confidence"] for r in ocr_outputs) / len(ocr_outputs), 3) if ocr_outputs else 0,
                "detected_chart_type": chart_type,
                "text_count": len(ocr_outputs)
            }
        
        return results
        
    except ImportError as e:
        print(f"PaddleOCR not available: {e}")
        return {}


def extract_visual_insights(ocr_results: dict, whisper_segments: list) -> dict:
    """Extract visual insights by aligning OCR timestamps with transcription.
    
    Returns:
    - visual_timestamps: list of visual events with timestamps
    - chart_summary: summary of detected charts
    - text_mapping: mapping of frame text to transcription segments
    """
    
    visual_timestamps = []
    
    for frame_id, data in ocr_results.items():
        if data.get("text_count", 0) > 0:
            visual_timestamps.append({
                "timestamp": data["timestamp"],
                "frame_id": frame_id,
                "visual_type": data["visual_type"],
                "description": data["description"],
                "detected_chart_type": data.get("detected_chart_type"),
                "text_samples": data["ocr_results"][:3],  # Top 3 text samples
                "confidence": data["confidence"]
            })
    
    # Summarize charts
    chart_summary = {}
    for data in ocr_results.values():
        chart_type = data.get("detected_chart_type")
        if chart_type:
            if chart_type not in chart_summary:
                chart_summary[chart_type] = {
                    "count": 0,
                    "timestamps": [],
                    "ocr_samples": []
                }
            chart_summary[chart_type]["count"] += 1
            chart_summary[chart_type]["timestamps"].append(data["timestamp"])
            chart_summary[chart_type]["ocr_samples"].extend(data["ocr_results"])
    
    return {
        "visual_timestamps": visual_timestamps,
        "chart_summary": chart_summary,
        "total_visual_entries": len(visual_timestamps)
    }


def enrich_with_notebooklm(data: dict, notebooklm_results: dict) -> dict:
    """Merge NotebookLM natural language content with Whisper transcriptions."""
    # This would integrate with the NotebookLM export data
    # For now, placeholder for future integration
    return data


def process_video(video_id: str, device: str, output_dir: Path, visual_ocr: bool = True) -> dict:
    """Process single video with GPU-aware pipeline and visual chart/diagram OCR.
    
    Pipeline:
    1. Download video (yt-dlp)
    2. Extract audio (ffmpeg)
    3. Transcribe audio (Whisper with GPU)
    4. Extract frames (OpenCV, 5s interval)
    5. Classify frames by aspect ratio (portrait/landscape/square)
    6. Run PaddleOCR on frames (GPU if CUDA available)
    7. Extract visual insights and chart summaries
    8. Enrich with NotebookLM if available
    """
    print(f"Processing video: {video_id} on {device}")
    
    # Paths
    video_path = output_dir / "videos" / f"{video_id}.mp4"
    audio_path = output_dir / "audio" / f"{video_id}.wav"
    frames_dir = FRAMES_DIR / video_id
    result_path = output_dir / f"{video_id}_result.json"
    
    # Ensure directories exist
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Download video (using yt-dlp)
    print("Downloading video...")
    download_cmd = [
        "yt-dlp", "-f", "best",
        f"https://www.youtube.com/watch?v={video_id}",
        "-o", str(video_path)
    ]
    
    try:
        result = subprocess.run(download_cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            print(f"Download failed: {result.stderr}")
            return {"video_id": video_id, "status": "download_failed"}
    except subprocess.TimeoutExpired:
        return {"video_id": video_id, "status": "download_timeout"}
    
    # Extract audio
    print("Extracting audio...")
    if not extract_audio(video_path, audio_path):
        return {"video_id": video_id, "status": "audio_extraction_failed"}
    
    # Transcribe with Whisper
    print("Transcribing audio...")
    whisper_model = WHISPER_MODELS.get(device, "openai/whisper-base")
    whisper_result = transcribe_audio(audio_path, device, whisper_model)
    
    # Extract frames for OCR
    print("Extracting and classifying frames...")
    frame_count, frame_info = extract_frames(video_path, frames_dir)
    print(f"Extracted {frame_count} frames")
    
    # Classify frame types
    frame_types = {}
    for f in frame_info:
        ft = f["visual_type"]
        frame_types[ft] = frame_types.get(ft, 0) + 1
    print(f"Frame types: {frame_types}")
    
    # Run visual OCR (GPU-aware)
    ocr_results = {}
    visual_insights = {}
    if visual_ocr:
        print("Running PaddleOCR on frames...")
        ocr_results = run_visual_ocr(frames_dir, frame_info, use_gpu=(device == "cuda"))
        
        if ocr_results:
            visual_insights = extract_visual_insights(ocr_results, whisper_result["segments"])
            print(f"Visual insights: {visual_insights['total_visual_entries']} entries")
    
    # Build final result with enriched schema
    final_result = {
        "video_id": video_id,
        "device": device,
        "whisper_model": whisper_model,
        "timestamp": datetime.utcnow().isoformat(),
        
        "transcription": {
            "language": "en",
            "segments": len(whisper_result["segments"]),
            "duration": whisper_result["segments"][-1]["end"] if whisper_result["segments"] else 0,
            "segments": [
                {
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"].strip()
                }
                for seg in whisper_result["segments"]
            ]
        },
        
        "visual": {
            "frame_count": frame_count,
            "frames_dir": str(frames_dir),
            "frame_info": frame_info,
            "frame_types": frame_types
        },
        
        "ocr": {
            "result_count": len(ocr_results),
            "results": ocr_results,
            "schema_version": "2.0",
            "visual_insights": visual_insights
        }
    }
    
    # Save results
    with open(result_path, "w") as f:
        json.dump(final_result, f, indent=2)
    
    print(f"Results saved to: {result_path}")
    return final_result


def main():
    parser = argparse.ArgumentParser(description="GPU-aware SMB Capital video transcription with visual OCR")
    parser.add_argument("--video-id", required=True, help="YouTube video ID")
    parser.add_argument("--device", choices=["auto", "cuda", "cpu"], default="auto",
                       help="Compute device (auto-detects CUDA if available)")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR,
                       help="Output directory for results")
    parser.add_argument("--no-visual-ocr", action="store_true",
                       help="Skip visual chart/diagram OCR processing")
    
    args = parser.parse_args()
    
    # Auto-detect device if requested
    if args.device == "auto":
        device = get_device()
        print(f"Auto-detected device: {device}")
        if device == "cuda":
            print(f"GPU: {torch.cuda.get_device_name(0)}")
            print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    else:
        device = args.device
    
    # Process video
    result = process_video(args.video_id, device, args.output_dir, visual_ocr=not args.no_visual_ocr)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Processing Complete!")
    print("=" * 60)
    print(f"Video ID: {result['video_id']}")
    print(f"Device: {result['device']}")
    print(f"Segments: {result['transcription']['segments']}")
    print(f"Duration: {result['transcription']['duration']:.1f} seconds")
    print(f"Frames extracted: {result['visual']['frame_count']}")
    print(f"Frame types: {result['visual']['frame_types']}")
    
    if result['ocr'].get('result_count', 0) > 0:
        print(f"OCR frames processed: {result['ocr']['result_count']}")
        visual_insights = result['ocr'].get('visual_insights', {})
        print(f"Visual insights: {visual_insights.get('total_visual_entries', 0)} entries")
        
        chart_summary = visual_insights.get('chart_summary', {})
        if chart_summary:
            print("Detected chart types:")
            for chart_type, data in chart_summary.items():
                print(f"  - {chart_type}: {data['count']} occurrences")
    
    # Save final result
    output_file = args.output_dir / f"{args.video_id}_final_result.json"
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"\nFinal results saved to: {output_file}")
    print(f"GPU acceleration: {'enabled' if device == 'cuda' else 'disabled'}")
    print(f"Visual OCR: {'enabled' if not args.no_visual_ocr else 'disabled'}")


if __name__ == "__main__":
    main()
