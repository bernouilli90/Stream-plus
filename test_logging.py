#!/usr/bin/env python3
"""
Script to test the enhanced logging in test_stream method.
This will help debug Docker environment issues.
"""

from api.dispatcharr_client import DispatcharrClient

def test_stream_with_logging():
    # Create client
    client = DispatcharrClient(
        base_url='http://192.168.10.10:9192',
        username='jose',
        password='rotring1010'
    )

    # Test a stream that we know exists
    stream_id = 2396  # From our check

    print("=" * 80)
    print(f"Testing stream {stream_id} with enhanced logging")
    print("=" * 80)

    result = client.test_stream(stream_id, test_duration=5)

    print("=" * 80)
    print("Test completed")
    print(f"Success: {result.get('success')}")
    print(f"Message: {result.get('message')}")
    if result.get('save_error'):
        print(f"Save Error: {result.get('save_error')}")
    print("=" * 80)

if __name__ == "__main__":
    test_stream_with_logging()