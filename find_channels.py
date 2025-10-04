#!/usr/bin/env python3
"""Find available channels with stream 776"""

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

print("Finding channels with stream 776...")
channels = client.get_channels()

found_channels = []
for ch in channels:
    if 776 in ch.get('streams', []):
        found_channels.append(ch)
        print(f"\nChannel ID: {ch['id']}")
        print(f"  Name: {ch.get('name', 'N/A')}")
        print(f"  Channel Number: {ch.get('channel_number', 'N/A')}")
        print(f"  Streams: {ch.get('streams', [])}")
        print(f"  Enabled: {ch.get('enabled', False)}")

if not found_channels:
    print("\nNo channels found with stream 776")
    print("\nLet's check the first 5 channels:")
    for ch in channels[:5]:
        print(f"\nChannel ID: {ch['id']}")
        print(f"  Name: {ch.get('name', 'N/A')}")
        print(f"  Streams: {ch.get('streams', [])}")
        print(f"  Enabled: {ch.get('enabled', False)}")
