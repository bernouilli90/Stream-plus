#!/usr/bin/env python3
"""Show original saved bitrates (before re-analysis)."""

import sys
sys.path.insert(0, 'api')

from dispatcharr_client import DispatcharrClient

def main():
    print("\n" + "="*70)
    print("ORIGINAL SAVED BITRATES")
    print("="*70)
    
    # Initialize client
    client = DispatcharrClient(
        base_url='http://192.168.10.10:9192',
        username='jose',
        password='rotring1010'
    )
    
    stream_ids = [531, 720, 776]
    
    print("\nThese are the bitrates saved BEFORE the last test:")
    print("-" * 70)
    
    for stream_id in stream_ids:
        stream = client.get_stream(stream_id)
        stats = stream.get('stream_stats', {})
        
        print(f"\nStream {stream_id}: {stream.get('name')}")
        print(f"  ffmpeg_output_bitrate: {stats.get('ffmpeg_output_bitrate')} kbps")
        print(f"  Meets >=5000 kbps? {stats.get('ffmpeg_output_bitrate', 0) >= 5000}")
        
        # Calculate expected score
        score = 0
        if stats.get('resolution') == '1920x1080':
            score += 50
            print(f"  + 50 points (resolution 1920x1080)")
        if stats.get('video_codec') == 'h264':
            score += 20
            print(f"  + 20 points (codec h264)")
        if stats.get('ffmpeg_output_bitrate', 0) >= 5000:
            score += 30
            print(f"  + 30 points (bitrate >= 5000 kbps)")
        
        print(f"  → Expected Total: {score} points")
    
    print("\n" + "="*70 + "\n")

if __name__ == '__main__':
    main()
