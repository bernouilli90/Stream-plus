#!/usr/bin/env python3
"""Check Dispatcharr original stream_stats format"""

import os
import sys

os.environ['DISPATCHARR_API_URL'] = 'http://192.168.10.10:9192'
os.environ['DISPATCHARR_API_USER'] = 'jose'
os.environ['DISPATCHARR_API_PASSWORD'] = 'rotring1010'

sys.path.insert(0, '.')

from api.dispatcharr_client import DispatcharrClient
import json

client = DispatcharrClient(
    base_url=os.getenv('DISPATCHARR_API_URL'),
    username=os.getenv('DISPATCHARR_API_USER'),
    password=os.getenv('DISPATCHARR_API_PASSWORD')
)

# Find streams with stats from before our testing (Sept 2025)
streams = client.get_streams()
old_stats_streams = [s for s in streams if s.get('stream_stats') and s.get('stream_stats_updated_at') and s.get('stream_stats_updated_at', '').startswith('2025-09')]

if old_stats_streams:
    stream = old_stats_streams[0]
    print(f"Stream {stream['id']} - Original Dispatcharr format:")
    print(f"Updated at: {stream.get('stream_stats_updated_at')}")
    print("\nFields:")
    print(json.dumps(stream.get('stream_stats', {}), indent=2))
else:
    print("No streams found with original Dispatcharr stats")
    print("\nLet's check what fields we're currently saving:")
    if streams:
        recent = [s for s in streams if s.get('stream_stats')]
        if recent:
            print(f"\nStream {recent[0]['id']} (recent):")
            print(json.dumps(recent[0].get('stream_stats', {}), indent=2))
