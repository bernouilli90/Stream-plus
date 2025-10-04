#!/usr/bin/env python3
"""Check what fields are in stream_stats"""

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

stream = client.get_stream(776)
print("Stream 776 stats:")
print(json.dumps(stream.get('stream_stats', {}), indent=2))
