#!/usr/bin/env python3
"""Test direct stream URL access"""

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

# Get stream 776 directly
print("Getting stream 776 details...")
stream = client.get_stream(776)

print(f"\nStream ID: {stream['id']}")
print(f"Name: {stream.get('name', 'N/A')}")
print(f"URL: {stream.get('url', 'N/A')}")
print(f"Type: {stream.get('type', 'N/A')}")
print(f"\nFull stream object:")
import json
print(json.dumps(stream, indent=2))
