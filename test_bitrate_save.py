#!/usr/bin/env python
"""Test script to verify bitrate is saved correctly in stream stats"""
import os
import json
from api.dispatcharr_client import DispatcharrClient

# Create client
client = DispatcharrClient(
    os.getenv('DISPATCHARR_API_URL', 'http://127.0.0.1:9191'),
    os.getenv('DISPATCHARR_USERNAME', 'user'),
    os.getenv('DISPATCHARR_PASSWORD', 'password')
)

# Get stream
stream_id = 520
print(f"Getting stream {stream_id}...")
stream = client.get_stream(stream_id)
print(f"Stream: {stream['name']}")
print(f"URL: {stream['url']}\n")

# Test stream
print("Testing stream (10 second FFmpeg analysis)...")
result = client.test_stream(stream['url'])

print("\n" + "="*60)
print("STATS RETURNED FROM test_stream():")
print("="*60)
print(json.dumps(result, indent=2))

# Update stream stats in Dispatcharr
print("\n" + "="*60)
print("UPDATING STREAM STATS IN DISPATCHARR...")
print("="*60)
update_result = client.update_stream_stats(stream_id, result)
print(json.dumps(update_result, indent=2))

# Get stream again to verify
print("\n" + "="*60)
print("GETTING STREAM AGAIN TO VERIFY SAVED STATS...")
print("="*60)
stream_updated = client.get_stream(stream_id)
saved_stats = stream_updated.get('stream_stats', {})
print(json.dumps(saved_stats, indent=2))

# Check for bitrate fields
print("\n" + "="*60)
print("BITRATE FIELD CHECK:")
print("="*60)
if 'output_bitrate' in saved_stats:
    print(f"✓ output_bitrate: {saved_stats['output_bitrate']} kbps")
else:
    print("✗ output_bitrate: NOT FOUND")

if 'ffmpeg_output_bitrate' in saved_stats:
    print(f"✓ ffmpeg_output_bitrate: {saved_stats['ffmpeg_output_bitrate']} kbps")
else:
    print("✗ ffmpeg_output_bitrate: NOT FOUND")

if 'video_bitrate' in saved_stats:
    print(f"✓ video_bitrate: {saved_stats['video_bitrate']} kbps")
else:
    print("✗ video_bitrate: NOT FOUND")
