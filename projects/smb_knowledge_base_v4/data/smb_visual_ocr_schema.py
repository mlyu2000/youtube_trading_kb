#!/usr/bin/env python3
"""
Visual Chart/Diagram OCR Schema Documentation

SMB Knowledge Base v3.0 - Enriched OCR Output Format
"""

import json
from pathlib import Path

# Example visual OCR output schema
EXAMPLE_OCR_OUTPUT = {
    "video_id": "45eaVU5NVi8",
    "device": "cuda",
    "whisper_model": "openai/whisper-large-v3-turbo",
    "timestamp": "2026-05-03T06:00:00.000000",
    
    "transcription": {
        "language": "en",
        "segments": 150,
        "duration": 623.5,
        "segments": [
            {
                "start": 0.0,
                "end": 3.2,
                "text": "Welcome back to the channel"
            }
        ]
    },
    
    "visual": {
        "frame_count": 125,
        "frames_dir": "/home/ml/smb_processor/frames/45eaVU5NVi8",
        "frame_info": [
            {
                "frame_id": "frame_000000",
                "timestamp": 0.0,
                "width": 1920,
                "height": 1080,
                "aspect_ratio": 1.78,
                "visual_type": "landscape",
                "description": "Chart/diagram/price action",
                "confidence": 0.85
            },
            {
                "frame_id": "frame_000001",
                "timestamp": 5.0,
                "width": 1920,
                "height": 1080,
                "aspect_ratio": 1.78,
                "visual_type": "landscape",
                "description": "Chart/diagram/price action",
                "confidence": 0.85
            },
            {
                "frame_id": "frame_000010",
                "timestamp": 50.0,
                "width": 1080,
                "height": 1920,
                "aspect_ratio": 0.56,
                "visual_type": "portrait",
                "description": "Host explanation/talking head",
                "confidence": 0.75
            }
        ],
        "frame_types": {
            "landscape": 110,
            "portrait": 10,
            "square": 5
        }
    },
    
    "ocr": {
        "result_count": 125,
        "schema_version": "3.0",
        "results": {
            "frame_000000": {
                "timestamp": 0.0,
                "visual_type": "landscape",
                "description": "Chart/diagram/price action",
                "confidence": 0.85,
                "ocr_results": [
                    {
                        "text": "SPY $450.25",
                        "confidence": 0.92,
                        "bounding_box": [[100, 50], [200, 50], [200, 70], [100, 70]]
                    },
                    {
                        "text": "Volume: 5.2M",
                        "confidence": 0.89,
                        "bounding_box": [[100, 600], [250, 600], [250, 620], [100, 600]]
                    }
                ],
                "ocr_confidence_avg": 0.905,
                "detected_chart_type": "price_chart",
                "text_count": 2
            },
            "frame_000001": {
                "timestamp": 5.0,
                "visual_type": "landscape",
                "description": "Chart/diagram/price action",
                "confidence": 0.85,
                "ocr_results": [
                    {
                        "text": "Support at $448.50",
                        "confidence": 0.94,
                        "bounding_box": [[80, 200], [280, 200], [280, 220], [80, 200]]
                    },
                    {
                        "text": "RSI: 62",
                        "confidence": 0.96,
                        "bounding_box": [[500, 100], [580, 100], [580, 120], [500, 100]]
                    }
                ],
                "ocr_confidence_avg": 0.95,
                "detected_chart_type": "technical_chart",
                "text_count": 2
            }
        },
        "visual_insights": {
            "visual_timestamps": [
                {
                    "timestamp": 0.0,
                    "frame_id": "frame_000000",
                    "visual_type": "landscape",
                    "description": "Chart/diagram/price action",
                    "detected_chart_type": "price_chart",
                    "text_samples": [
                        {"text": "SPY $450.25", "confidence": 0.92}
                    ],
                    "confidence": 0.85
                },
                {
                    "timestamp": 5.0,
                    "frame_id": "frame_000001",
                    "visual_type": "landscape",
                    "description": "Chart/diagram/price action",
                    "detected_chart_type": "technical_chart",
                    "text_samples": [
                        {"text": "Support at $448.50", "confidence": 0.94},
                        {"text": "RSI: 62", "confidence": 0.96}
                    ],
                    "confidence": 0.85
                }
            ],
            "chart_summary": {
                "price_chart": {
                    "count": 45,
                    "timestamps": [0.0, 10.0, 20.0, 30.0],
                    "ocr_samples": [
                        {"text": "SPY $450.25", "confidence": 0.92},
                        {"text": "QQQ $380.50", "confidence": 0.91}
                    ]
                },
                "technical_chart": {
                    "count": 30,
                    "timestamps": [5.0, 15.0, 25.0],
                    "ocr_samples": [
                        {"text": "Support at $448.50", "confidence": 0.94},
                        {"text": "RSI: 62", "confidence": 0.96},
                        {"text": "MACD: -1.2", "confidence": 0.93}
                    ]
                }
            },
            "total_visual_entries": 75
        }
    }
}


def print_schema():
    """Print the visual OCR schema documentation."""
    print("=" * 70)
    print("SMB Knowledge Base v3.0 - Visual Chart/Diagram OCR Schema")
    print("=" * 70)
    print()
    
    print("1. FRAME CLASSIFICATION (Aspect Ratio)")
    print("-" * 40)
    print("  Landscape (width/height > 1.5): Chart/diagram/price action")
    print("    Confidence: 0.85")
    print("    OCR Purpose: Extract chart labels, numbers, indicators")
    print()
    print("  Portrait (width/height < 1.0): Host explanation/talking head")
    print("    Confidence: 0.75")
    print("    OCR Purpose: Extract name, title, on-screen text")
    print()
    print("  Square (1.0 >= width/height >= 1.5): Preview/infographic")
    print("    Confidence: 0.70")
    print("    OCR Purpose: Extract summary text, overlay text")
    print()
    
    print("2. OCR RESULTS SCHEMA (Per Frame)")
    print("-" * 40)
    print("  frame_XXXXXX: {")
    print("    timestamp: float          # Video timestamp (seconds)")
    print("    visual_type: str          # 'landscape', 'portrait', 'square'")
    print("    description: str          # Content description")
    print("    confidence: float         # 0.70-0.85")
    print("    ocr_results: [")
    print("      {")
    print("        text: str             # Extracted text")
    print("        confidence: float     # 0.0-1.0")
    print("        bounding_box: [[x,y],...]  # Polygon corners")
    print("      }")
    print("    ]")
    print("    ocr_confidence_avg: float  # Average OCR confidence")
    print("    detected_chart_type: str   # 'price_chart', 'technical_chart', etc.")
    print("    text_count: int           # Number of OCR results")
    print("  }")
    print()
    
    print("3. VISUAL INSIGHTS SUMMARY")
    print("-" * 40)
    print("  visual_insights: {")
    print("    visual_timestamps: [")
    print("      {")
    print("        timestamp: float")
    print("        frame_id: str")
    print("        visual_type: str")
    print("        detected_chart_type: str")
    print("        text_samples: [{text, confidence}]  # Top 3")
    print("        confidence: float")
    print("      }")
    print("    ]")
    print("    chart_summary: {")
    print("      'price_chart': {")
    print("        count: int")
    print("        timestamps: [float, ...]")
    print("        ocr_samples: [{text, confidence}]")
    print("      }")
    print("    }")
    print("    total_visual_entries: int")
    print("  }")
    print()
    
    print("4. EXAMPLE DETECTED CHART TYPES")
    print("-" * 40)
    for chart_type in EXAMPLE_OCR_OUTPUT["ocr"]["visual_insights"]["chart_summary"].keys():
        print(f"  - {chart_type}: {EXAMPLE_OCR_OUTPUT['ocr']['visual_insights']['chart_summary'][chart_type]['count']} occurrences")
    print()
    
    print("5. OUTPUT FILE")
    print("-" * 40)
    print("  Location: /home/ml/smb_processor/output/{video_id}_final_result.json")
    print("  Size: ~80-100KB per video (with visual OCR)")
    print("  Format: JSON with nested structure")
    print()
    
    print("=" * 70)


if __name__ == "__main__":
    print_schema()
