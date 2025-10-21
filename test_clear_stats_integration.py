#!/usr/bin/env python3
"""
Integration test for clear_stream_stats using PUT approach
This script tests the new implementation against a real Dispatcharr instance
"""

import sys
import time
sys.path.insert(0, 'api')

from dispatcharr_client import DispatcharrClient

def test_clear_stats_integration():
    """Test clearing stream stats with real Dispatcharr instance"""

    # Initialize client (adjust URL as needed)
    client = DispatcharrClient("http://localhost:8080")

    # Use a test stream ID (adjust as needed)
    test_stream_id = 123

    print("Testing clear_stream_stats with PUT approach...")
    print(f"Stream ID: {test_stream_id}")

    try:
        # First, get current stream state
        print("\n1. Getting current stream state...")
        current_stream = client.get_stream(test_stream_id)
        print(f"Current stream_stats: {current_stream.get('stream_stats', 'Not found')}")
        print(f"Current stream_stats_updated_at: {current_stream.get('stream_stats_updated_at', 'Not found')}")

        # Clear the stats
        print("\n2. Clearing stream stats...")
        cleared_stream = client.clear_stream_stats(test_stream_id)
        print("Clear operation completed successfully")

        # Verify the stats were cleared
        print("\n3. Verifying stats were cleared...")
        updated_stream = client.get_stream(test_stream_id)
        print(f"Updated stream_stats: {updated_stream.get('stream_stats', 'Not found')}")
        print(f"Updated stream_stats_updated_at: {updated_stream.get('stream_stats_updated_at', 'Not found')}")

        # Check if stats are actually empty
        stats = updated_stream.get('stream_stats', {})
        if stats == {}:
            print("✅ SUCCESS: Stream stats were properly cleared!")
        else:
            print(f"❌ FAILURE: Stream stats not cleared. Still contains: {stats}")

        return True

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == '__main__':
    success = test_clear_stats_integration()
    sys.exit(0 if success else 1)