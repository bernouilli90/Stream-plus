#!/usr/bin/env python3
"""Check stats for all test streams."""

import sys
sys.path.insert(0, 'api')

from dispatcharr_client import DispatcharrClient
import json

def main():
    print("\n" + "="*70)
    print("CHECKING STATS FOR ALL TEST STREAMS")
    print("="*70)
    
    # Initialize client
    client = DispatcharrClient(
        base_url='http://192.168.10.10:9192',
        username='jose',
        password='rotring1010'
    )
    
    # Test streams
    stream_ids = [776, 531, 720]
    
    for stream_id in stream_ids:
        try:
            stream = client.get_stream(stream_id)
            stats = stream.get('stream_stats', {})
            
            print(f"\nStream {stream_id}: {stream.get('name')}")
            print("-" * 70)
            
            if not stats:
                print("  NO STATS")
                continue
            
            print(f"  Number of fields: {len(stats)}")
            
            # Key fields
            print(f"\n  Video:")
            print(f"    resolution: {stats.get('resolution')}")
            print(f"    video_codec: {stats.get('video_codec')}")
            print(f"    pixel_format: {stats.get('pixel_format')}")
            print(f"    source_fps: {stats.get('source_fps')}")
            
            print(f"\n  Audio:")
            print(f"    audio_codec: {stats.get('audio_codec')}")
            print(f"    sample_rate: {stats.get('sample_rate')}")
            print(f"    audio_bitrate: {stats.get('audio_bitrate')}")
            print(f"    audio_channels: {stats.get('audio_channels')}")
            
            print(f"\n  Other:")
            print(f"    stream_type: {stats.get('stream_type')}")
            print(f"    ffmpeg_output_bitrate: {stats.get('ffmpeg_output_bitrate')} kbps")
            
            # Check for old fields
            old_fields = ['bitrate_kbps', 'bit_rate', 'width', 'height', 'analyzed_at', 
                         'test_duration', 'pix_fmt', 'channels']
            has_old_fields = [f for f in old_fields if f in stats]
            if has_old_fields:
                print(f"\n  ⚠️  OLD FIELDS PRESENT: {has_old_fields}")
            else:
                print(f"\n  ✓ Only new format fields")
            
        except Exception as e:
            print(f"\nStream {stream_id}: ERROR - {e}")
    
    print("\n" + "="*70)
    print("CHECK COMPLETED")
    print("="*70 + "\n")

if __name__ == '__main__':
    main()
