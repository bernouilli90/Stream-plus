#!/usr/bin/env python3
"""Debug sorting - check exact values being evaluated."""

import sys
sys.path.insert(0, 'api')

from dispatcharr_client import DispatcharrClient
from stream_sorter_models import StreamSorter, SortingRule, SortingCondition

def main():
    print("\n" + "="*70)
    print("DEBUG: SORTING EVALUATION")
    print("="*70)
    
    # Initialize client
    client = DispatcharrClient(
        base_url='http://192.168.10.10:9192',
        username='jose',
        password='rotring1010'
    )
    
    # Get streams
    stream_ids = [531, 720, 776]
    
    print("\n1. Checking stream stats...")
    print("-" * 70)
    for stream_id in stream_ids:
        stream = client.get_stream(stream_id)
        stats = stream.get('stream_stats', {})
        bitrate = stats.get('ffmpeg_output_bitrate')
        resolution = stats.get('resolution')
        codec = stats.get('video_codec')
        
        print(f"\nStream {stream_id}:")
        print(f"  resolution: {resolution}")
        print(f"  video_codec: {codec}")
        print(f"  ffmpeg_output_bitrate: {bitrate} kbps")
        print(f"  bitrate >= 5000? {bitrate >= 5000 if bitrate else 'N/A'}")
    
    # Create test rule
    print("\n" + "="*70)
    print("2. Creating test rule...")
    print("-" * 70)
    
    rule = SortingRule(
        id=999,
        name="Debug Rule",
        description="Debug bitrate scoring",
        channels=[614],
        groups=[],
        conditions=[
            SortingCondition(
                id=1,
                rule_id=999,
                condition_type='video_resolution',
                operator='==',
                value='1920x1080',
                points=50
            ),
            SortingCondition(
                id=2,
                rule_id=999,
                condition_type='video_bitrate',
                operator='>=',
                value='5000',
                points=30
            ),
            SortingCondition(
                id=3,
                rule_id=999,
                condition_type='video_codec',
                operator='==',
                value='h264',
                points=20
            ),
        ]
    )
    
    print("\n3. Scoring each stream...")
    print("-" * 70)
    
    sorter = StreamSorter(client)
    
    for stream_id in stream_ids:
        stream = client.get_stream(stream_id)
        stats = stream.get('stream_stats', {})
        
        print(f"\nStream {stream_id}: {stream.get('name')}")
        print(f"  Stats present: {bool(stats)}")
        print(f"  Stats fields: {len(stats)}")
        print(f"  ffmpeg_output_bitrate in stats: {'ffmpeg_output_bitrate' in stats}")
        print(f"  ffmpeg_output_bitrate value: {stats.get('ffmpeg_output_bitrate')}")
        
        # Score the stream
        score = sorter.score_stream(stream, rule)
        print(f"  → Total Score: {score} points")
        
        # Debug each condition
        for condition in rule.conditions:
            result = sorter._evaluate_condition(stats, condition)
            print(f"    - {condition.condition_type} {condition.operator} {condition.value}: {result} points")
    
    print("\n" + "="*70 + "\n")

if __name__ == '__main__':
    main()
