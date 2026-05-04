#!/bin/bash
# SMB Knowledge Base v3.0 - Visual OCR Pipeline Runner
# Usage: ./run_smb_pipeline_v3.sh [video_id] [device]

set -e

echo "========================================"
echo "SMB Knowledge Base v3.0 Pipeline Runner"
echo "========================================"
echo ""

# Default values
VIDEO_ID="${1:-45eaVU5NVi8}"
DEVICE="${2:-auto}"
OUTPUT_DIR="/home/ml/smb_processor"

echo "Video ID: $VIDEO_ID"
echo "Device: $DEVICE"
echo "Output: $OUTPUT_DIR"
echo ""

# Step 1: Process video with GPU-aware transcription + visual OCR
echo "[1/2] Processing video with visual OCR..."
python /home/ml/smb_gpu_transcribe.py \
    --video-id="$VIDEO_ID" \
    --device="$DEVICE" \
    --output-dir="$OUTPUT_DIR"

# Step 2: Run KB merge
echo ""
echo "[2/2] Running KB merge with visual OCR enrichment..."
python /home/ml/smb_merge_kb_v3.py

echo ""
echo "========================================"
echo "Pipeline Complete!"
echo "========================================"
echo ""
echo "Output files:"
ls -lh "$OUTPUT_DIR/output/${VIDEO_ID}_final_result.json" 2>/dev/null || echo "  (video not found or not processed)"
ls -lh /home/ml/smb_notebooklm_pilot/smb_final_kb_v3.json

echo ""
echo "To run on all videos in your list:"
echo "  while read -r vid; do $0 \$vid cuda; done < /home/ml/smb_all_video_ids.txt"
