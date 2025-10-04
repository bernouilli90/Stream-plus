#!/usr/bin/env python3
"""Clean old fields from stream stats."""

import sys
sys.path.insert(0, 'api')

from dispatcharr_client import DispatcharrClient

def main():
    print("\n" + "="*70)
    print("CLEANING OLD FIELDS FROM STREAM 531")
    print("="*70)
    
    # Initialize client
    client = DispatcharrClient(
        base_url='http://192.168.10.10:9192',
        username='jose',
        password='rotring1010'
    )
    
    stream_id = 531
    
    print(f"\n1. Getting stream {stream_id}...")
    stream = client.get_stream(stream_id)
    old_stats = stream.get('stream_stats', {})
    print(f"   Current fields: {len(old_stats)}")
    
    # Only keep the 10 Dispatcharr original fields
    new_stats = {
        'resolution': old_stats.get('resolution'),
        'source_fps': old_stats.get('source_fps'),
        'video_codec': old_stats.get('video_codec'),
        'pixel_format': old_stats.get('pixel_format'),
        'audio_codec': old_stats.get('audio_codec'),
        'sample_rate': old_stats.get('sample_rate'),
        'audio_bitrate': old_stats.get('audio_bitrate'),
        'audio_channels': old_stats.get('audio_channels'),
        'stream_type': old_stats.get('stream_type'),
        'ffmpeg_output_bitrate': old_stats.get('ffmpeg_output_bitrate'),
    }
    
    print(f"\n2. Keeping only 10 Dispatcharr fields...")
    print(f"   resolution: {new_stats.get('resolution')}")
    print(f"   source_fps: {new_stats.get('source_fps')} (type: {type(new_stats.get('source_fps')).__name__})")
    print(f"   ffmpeg_output_bitrate: {new_stats.get('ffmpeg_output_bitrate')} kbps")
    
    print(f"\n3. Updating stream in Dispatcharr...")
    stream['stream_stats'] = new_stats
    result = client.update_stream(stream_id, stream)
    
    if result:
        print(f"   ✓ Stream updated successfully")
        
        print(f"\n4. Verifying...")
        stream = client.get_stream(stream_id)
        saved_stats = stream.get('stream_stats', {})
        print(f"   Saved fields: {len(saved_stats)}")
        
        # Check for old fields
        old_fields = ['bitrate_kbps', 'bit_rate', 'width', 'height', 'analyzed_at', 
                     'test_duration', 'pix_fmt', 'channels']
        has_old_fields = [f for f in old_fields if f in saved_stats]
        if has_old_fields:
            print(f"   ⚠️  Still has old fields: {has_old_fields}")
        else:
            print(f"   ✓ Only new format fields")
    else:
        print(f"   ✗ Update failed")
    
    print("\n" + "="*70 + "\n")

if __name__ == '__main__':
    main()
