#!/usr/bin/env python3
"""
Test script to demonstrate the improved stream testing logging
"""

import sys
import os
sys.path.insert(0, 'api')

from dispatcharr_client import DispatcharrClient

def test_logging_demo():
    """Demo the improved logging for stream testing"""

    # Initialize client (this will fail but shows the logging structure)
    client = DispatcharrClient("http://localhost:8080")

    # This will fail because there's no server, but it will show the logging structure
    try:
        result = client.test_stream(123, test_duration=5)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Expected error (no server running): {e}")

if __name__ == '__main__':
    print("=== Stream Testing Logging Demo ===")
    print("This will show the improved logging structure (will fail due to no server)")
    print()
    test_logging_demo()