# SMB CAPITAL YOUTUBE KNOWLEDGE BASE

## Overview
| Metric | Value |
|--------|-------|
| Total Videos | 15 |
| Total Transcript Segments | 9,500+ |
| Total Visual Timestamps | 943 |

## Files
- **smb_knowledge_base.json** - Original transcripts (YouTube captions)
- **smb_knowledge_base_enriched.json** - Transcripts + visual timestamps (Whisper local)
- **smb_knowledge_base_final.json** - **FINAL VERSION** with local Whisper + visual frames
- **double_diagonal_strategy.md** - Extracted trading strategy

## Processing Methodology
1. Downloaded videos with yt-dlp
2. Extracted audio with ffmpeg
3. Transcribed audio with Whisper (local, base model)
4. Captured video frames at 10s intervals
5. Analyzed frames for visual content (chart/diagram, summary, host explanation)
6. Mapped visual content to transcript timestamps

## Sample Visual Content
