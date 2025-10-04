#!/usr/bin/env python3
"""Find enabled channels for testing"""

import os
import sys

os.environ['DISPATCHARR_API_URL'] = 'http://192.168.10.10:9192'
os.environ['DISPATCHARR_API_USER'] = 'jose'
os.environ['DISPATCHARR_API_PASSWORD'] = 'rotring1010'

sys.path.insert(0, '.')

from api.dispatcharr_client import DispatcharrClient

client = DispatcharrClient(
    base_url=os.getenv('DISPATCHARR_API_URL'),
    username=os.getenv('DISPATCHARR_API_USER'),
    password=os.getenv('DISPATCHARR_API_PASSWORD')
)

print("Finding enabled channels...")
channels = client.get_channels()

enabled_channels = [ch for ch in channels if ch.get('enabled', False)]

print(f"\nFound {len(enabled_channels)} enabled channels out of {len(channels)} total")

if enabled_channels:
    print("\nFirst 10 enabled channels:")
    for i, ch in enumerate(enabled_channels[:10], 1):
        print(f"\n{i}. Channel ID: {ch['id']}")
        print(f"   Name: {ch.get('name', 'N/A')}")
        print(f"   Channel Number: {ch.get('channel_number', 'N/A')}")
        print(f"   Streams: {ch.get('streams', [])}")
        
        if ch.get('streams'):
            print(f"   First stream ID: {ch['streams'][0]}")
else:
    print("\n[WARNING] No enabled channels found!")
    print("\nShowing all channels (first 10):")
    for i, ch in enumerate(channels[:10], 1):
        print(f"\n{i}. Channel ID: {ch['id']}")
        print(f"   Name: {ch.get('name', 'N/A')}")
        print(f"   Enabled: {ch.get('enabled', False)}")
        print(f"   Streams: {ch.get('streams', [])}")
