#!/usr/bin/env python3
"""Audio transcription module using faster-whisper with multi-language support."""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

from config.settings import settings
from storage.sqlite_store import SQLiteStore
from storage.file_store import FileStore

# Language-specific Whisper models (use HF Hub names for automatic CTranslate2 conversion)
WHISPER_MODELS = {
    "zh": "ylpeter/faster-whisper-large-v3-turbo-cantonese-16",
    "zh-HK": "ylpeter/faster-whisper-large-v3-turbo-cantonese-16",
    "zh-TW": "ylpeter/faster-whisper-large-v3-turbo-cantonese-16",
    "default": "ylpeter/faster-whisper-large-v3-turbo-cantonese-16",
}


class AudioTranscriber:
    """Transcribe audio to text using Whisper with language-aware model selection."""
    
    def __init__(self, model_name: str = None, device: str = None,
                 sqlite_store: SQLiteStore = None, file_store: FileStore = None):
        self.model_name = model_name or settings.whisper_model
        self.device = device or settings.device
        self.sqlite = sqlite_store or SQLiteStore()
        self.files = file_store or FileStore()
    
    def _get_model_for_language(self, language: str) -> str:
        """Get the appropriate Whisper model for a given language."""
        if language and language.lower() in ['zh', 'zh-hant', 'zh-hk', 'zh-tw', 'zh-cn', 'yue', 'cantonese']:
            return WHISPER_MODELS.get("zh", WHISPER_MODELS["default"])
        return WHISPER_MODELS.get("default")
    
    def _load_model(self, model_name: str) -> WhisperModel:
        """Load Whisper model with GPU support."""
        if not WHISPER_AVAILABLE:
            return None
        
        # Use GPU acceleration if available
        device = self.device
        if self.device == "auto":
            device = "cuda" if self._is_cuda_available() else "cpu"
        
        compute_type = "int8_float16" if device == "cuda" else "int8"
        
        # Check if model dir exists and has safetensors format
        model_path = Path(model_name)
        if model_path.exists() and (model_path / "model.safetensors").exists():
            model_type = "safetensors"
        elif model_path.exists() and (model_path / "pytorch_model.bin").exists():
            model_type = "pytorch"
        else:
            model_type = "auto"  # Let faster-whisper detect
        
        return WhisperModel(
            model_name,
            device=device,
            compute_type=compute_type,
            local_files_only=False,
            use_auth_token=False
        )
    
    def _is_cuda_available(self) -> bool:
        """Check if CUDA is available for GPU acceleration."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def transcribe(self, video_id: str, audio_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
        """Transcribe video audio with language detection and model selection.
        
        Args:
            video_id: ID of the video
            audio_path: Optional path to audio file (extracted if not provided)
        
        Returns:
            Transcription with segments
        """
        if not WHISPER_AVAILABLE:
            print("faster-whisper not available. Cannot transcribe.")
            return None
        
        if audio_path is None:
            audio_path = self.files.get_audio_path(video_id)
        
        if not audio_path.exists():
            print(f"Audio file not found: {audio_path}")
            return None
        
        try:
            # First pass: detect language with base model
            print("Detecting language...")
            base_model = WhisperModel("base", device="cpu", compute_type="int8")
            segments_gen, info = base_model.transcribe(
                str(audio_path),
                word_timestamps=False,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            base_model = None  # Free memory
            
            detected_language = info.language
            print(f"Detected language: {detected_language}")
            
            # Select appropriate model based on language
            model_name = self._get_model_for_language(detected_language)
            print(f"Using model: {model_name}")
            
            # Load language-specific model with GPU acceleration
            model = self._load_model(model_name)
            if model is None:
                print(f"Failed to load model {model_name}")
                return None
            
            # Second pass: transcribe with selected model
            print("Transcribing with selected model...")
            segments, info = model.transcribe(
                str(audio_path),
                word_timestamps=True,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
                language=detected_language if detected_language not in ['zh', 'zh-TW', 'zh-HK'] else None
            )
            
            # Build segments list
            transcription_segments = []
            for segment in segments:
                transcription_segments.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "words": [
                        {"word": w.word, "start": w.start, "end": w.end}
                        for w in segment.words
                    ] if segment.words else []
                })
            
            # Build result
            result = {
                "video_id": video_id,
                "language": detected_language,
                "language_probability": info.language_probability,
                "duration": info.duration,
                "segments": transcription_segments,
                "extracted_at": __import__('datetime').datetime.utcnow().isoformat()
            }
            
            # Save to file
            transcript_path = self.files.get_transcript_path(video_id)
            with open(transcript_path, 'w') as f:
                json.dump(result, f, indent=2)
            
            # Store segment metadata in SQLite
            for seg in transcription_segments:
                segment_id = f"{video_id}_seg_{int(seg['start'])}_{int(seg['end'])}"
                self.sqlite.create_segment(
                    segment_id=segment_id,
                    video_id=video_id,
                    start_time=seg['start'],
                    end_time=seg['end'],
                    transcript=seg['text'],
                    keyframes_json=json.dumps([])
                )
            
            # Update processing job
            job_id = f"{video_id}_transcribe"
            self.sqlite.create_processing_job(
                job_id=job_id,
                video_id=video_id,
                job_type="transcription",
                status="completed",
                error_message=None
            )
            
            return result
            
        except Exception as e:
            print(f"Error transcribing {video_id}: {e}")
            self.sqlite.create_processing_job(
                job_id=f"{video_id}_transcribe",
                video_id=video_id,
                job_type="transcription",
                status="failed",
                error_message=str(e)
            )
            return None
    
    def transcribe_audio_file(self, audio_path: str) -> Dict[str, Any]:
        """Transcribe a standalone audio file.
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            Transcription with segments
        """
        if not WHISPER_AVAILABLE:
            return {"error": "faster-whisper not installed"}
        
        audio_path = Path(audio_path)
        
        # Detect language first
        base_model = WhisperModel("base", device="cpu", compute_type="int8")
        segments_gen, info = base_model.transcribe(
            str(audio_path),
            word_timestamps=False,
            vad_filter=True
        )
        base_model = None
        
        detected_language = info.language
        print(f"Detected language: {detected_language}")
        
        # Select and load model
        model_name = self._get_model_for_language(detected_language)
        model = self._load_model(model_name)
        if model is None:
            return {"error": f"Failed to load model {model_name}"}
        
        # Transcribe
        segments, info = model.transcribe(
            str(audio_path),
            word_timestamps=True,
            vad_filter=True
        )
        
        transcription_segments = []
        for segment in segments:
            transcription_segments.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text
            })
        
        return {
            "audio_file": str(audio_path),
            "language": detected_language,
            "model_used": model_name,
            "duration": info.duration,
            "segments": transcription_segments
        }


def transcribe_audio(video_id: str) -> Optional[Dict[str, Any]]:
    """Convenience function to transcribe a video."""
    transcriber = AudioTranscriber()
    return transcriber.transcribe(video_id)
