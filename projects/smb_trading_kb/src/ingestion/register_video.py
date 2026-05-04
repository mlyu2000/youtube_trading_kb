#!/usr/bin/env python3
"""Video registration module with LLM-based category and school prediction."""

import os
from pathlib import Path
from typing import Optional
import subprocess

from config.settings import settings
from storage.sqlite_store import SQLiteStore
from storage.file_store import FileStore
from models.qwen_client import QwenClient


class VideoRegistrar:
    """Register and register videos for processing."""
    
    # Category definitions
    CATEGORIES = {
        "technical_analysis": "Technical Analysis - Chart patterns, indicators, price action",
        "fundamental_analysis": "Fundamental Analysis - Financial metrics, economic data, company analysis",
        "trading_pychoology": "Trading Psychology - Mindset, emotions, discipline, mental models",
        "macro_markets": "Macro Markets - Central banks, interest rates, global economy",
        "risk_management": "Risk Management - Position sizing, stop losses, portfolio allocation",
        "algorithmic_trading": "Algorithmic/Quant - Coding, backtesting, automated systems",
        "options_trading": "Options Trading - Strategies, Greeks, volatility, expiration",
        "forex_trading": "Forex Trading - Currency pairs, interest rate differentials"
    }
    
    # School of thought definitions
    SCHOOLS = {
        "technical": "Technical Analysis school - charts, patterns, indicators",
        "fundamental": "Fundamental Analysis school - financials, economics, value",
        "price_action": "Price Action school - raw price movement analysis",
        "erokee trading": "Dark_pool/Smart Money Concepts - institutional flow analysis",
        "supply_demand": "Supply and Demand school - market structure, order blocks",
        "market_profile": "Market Profile - time-based volume analysis",
        "elder_ray": "Elder-Ray - 3 momentum systems",
        "ichimoku": "Ichimoku Kinko Hyo - comprehensive trend system"
    }
    
    def __init__(self, sqlite_store: SQLiteStore = None, file_store: FileStore = None,
                 qwen_client: QwenClient = None):
        self.sqlite = sqlite_store or SQLiteStore()
        self.files = file_store or FileStore()
        self.qwen = qwen_client or QwenClient(
            api_base=settings.qwen_api_base,
            api_key=settings.qwen_api_key,
            model=settings.qwen_model
        )
    
    def register_video(self, video_path: str, title: Optional[str] = None, 
                      video_id: Optional[str] = None) -> str:
        """Register a video for processing.
        
        Args:
            video_path: Path to the video file
            title: Optional title for the video
            video_id: Optional custom ID (generated from filename if not provided)
        
        Returns:
            The video ID
        """
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        # Generate video ID from filename if not provided
        if video_id is None:
            video_id = video_path.stem
        
        # Get video duration using ffprobe
        duration = self._get_video_duration(video_path)
        
        # Register in SQLite
        self.sqlite.register_video(
            video_id=video_id,
            title=title or video_path.stem,
            file_path=str(video_path),
            duration_seconds=duration
        )
        
        # Create extracted directory using FileStore helper
        video_dir = self.files.get_frames_dir(video_id).parent
        video_dir.mkdir(parents=True, exist_ok=True)
        
        return video_id
    
    def register_and_predict(self, video_path: str, title: Optional[str] = None,
                            video_id: Optional[str] = None) -> dict:
        """Register video and predict category/school using LLM.
        
        Args:
            video_path: Path to the video file
            title: Optional title for the video
            video_id: Optional custom ID
        
        Returns:
            Dict with video_id, category, school, and confidence
        """
        # Register video
        vid = self.register_video(video_path, title, video_id)
        
        # Return result dict (will be updated after segments are built)
        return {
            "video_id": vid,
            "category": None,
            "school": None,
            "confidence": None
        }
    
    def predict_category_and_school(self, video_id: str, segment_limit: int = 3) -> dict:
        """Use LLM to predict video category and school of thought from content.
        
        Args:
            video_id: The registered video ID
            segment_limit: Number of segments to analyze for prediction
        
        Returns:
            Dict with 'category', 'school', and 'confidence' fields
        """
        # Get segments for analysis
        segments = self.files.load_segments(video_id)
        if not segments:
            return {"category": "general", "school": "default", "confidence": 0.0}
        
        # Build content sample from first N segments
        content_samples = []
        for seg in segments[:segment_limit]:
            transcript = seg.get("transcript", "")
            ocr_text = seg.get("ocr_text", "")
            visual = seg.get("visual_summary", "")
            
            if transcript:
                content_samples.append(f"Transcript: {transcript[:500]}")
            if ocr_text:
                content_samples.append(f"OCR: {ocr_text[:200]}")
            if visual:
                content_samples.append(f"Visual: {visual[:200]}")
        
        content_text = "\n\n".join(content_samples)
        
        # Build prediction prompt
        prompt = f"""You are classifying a trading education video. Analyze this content and 
determine the most likely CATEGORY and SCHOOL OF THOUGHT.

CONTENT SAMPLE:
{content_text[:1500]}

CATEGORY OPTIONS:
{chr(10).join(f"- {cat}: {desc}" for cat, desc in self.CATEGORIES.items())}

SCHOOL OPTIONS:
{chr(10).join(f"- {school}: {desc}" for school, desc in self.SCHOOLS.items())}

INSTRUCTIONS:
1. Read the content carefully
2. Select the BEST matching category (only one)
3. Select the BEST matching school (only one)
4. Provide confidence score (0.0-1.0)
5. Explain your reasoning briefly

Return your answer as JSON:
{{
    "category": "category_name",
    "school": "school_name",
    "confidence": 0.0-1.0,
    "explanation": "brief reasoning"
}}
"""
        
        try:
            # Call Qwen for classification
            result = self.qwen.generate_json(
                prompt,
                system_prompt="You are an expert video classification assistant for trading content.",
                temperature=0.3
            )
            
            # Validate and return
            category = result.get("category", "general")
            school = result.get("school", "default")
            confidence = result.get("confidence", 0.0)
            
            # Store prediction in SQLite
            self.sqlite.update_video_metadata(
                video_id=video_id,
                metadata={
                    "predicted_category": category,
                    "predicted_school": school,
                    "prediction_confidence": confidence,
                    "prediction_explanation": result.get("explanation", "")
                }
            )
            
            return {
                "category": category,
                "school": school,
                "confidence": confidence,
                "explanation": result.get("explanation", "")
            }
            
        except Exception as e:
            print(f"Warning: Category prediction failed: {e}")
            return {"category": "general", "school": "default", "confidence": 0.0}
    
    def _get_video_duration(self, video_path: Path) -> float:
        """Get video duration in seconds using ffprobe."""
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(video_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return float(result.stdout.strip())
        except Exception as e:
            print(f"Warning: Could not get duration for {video_path}: {e}")
            return 0.0
    
    def is_registered(self, video_id: str) -> bool:
        """Check if a video is registered."""
        return self.sqlite.get_video(video_id) is not None
    
    def get_registration(self, video_id: str) -> Optional[dict]:
        """Get registration info for a video."""
        return self.sqlite.get_video(video_id)


def register_video(video_path: str, title: Optional[str] = None,
                  video_id: Optional[str] = None) -> str:
    """Convenience function to register a video."""
    registrar = VideoRegistrar()
    return registrar.register_video(video_path, title, video_id)
