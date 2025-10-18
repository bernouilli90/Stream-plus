#!/usr/bin/env python
"""
Test script to verify the stream assignment bug fix
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import AutoAssignmentRule, StreamMatcher

def test_failed_stream_exclusion():
    """Test that streams that failed testing are excluded when rule requires stats"""

    # Create a rule that requires resolution
    rule = AutoAssignmentRule(
        id=1,
        name="Test Rule",
        channel_id=1,
        enabled=True,
        video_resolution=["1080p"]  # Requires stats
    )

    # Create test streams
    streams = [
        {
            'id': 1,
            'name': 'Stream 1',
            'stream_stats': {'resolution': '1920x1080'}  # Has stats, matches
        },
        {
            'id': 2,
            'name': 'Stream 2',
            'stream_stats': {'resolution': '1280x720'}   # Has stats, doesn't match
        },
        {
            'id': 3,
            'name': 'Stream 3'  # No stats (simulates failed test)
        }
    ]

    # Test without failed streams
    matches_no_failed = StreamMatcher.evaluate_rule(rule, streams)
    print(f"Without failed streams: {len(matches_no_failed)} matches")
    for stream in matches_no_failed:
        print(f"  - {stream['name']} (ID: {stream['id']})")

    # Test with stream 3 marked as failed
    failed_test_stream_ids = {3}
    matches_with_failed = StreamMatcher.evaluate_rule(rule, streams, failed_test_stream_ids)
    print(f"\nWith stream 3 failed: {len(matches_with_failed)} matches")
    for stream in matches_with_failed:
        print(f"  - {stream['name']} (ID: {stream['id']})")

    # Verify that stream 3 is excluded
    stream_3_included = any(s['id'] == 3 for s in matches_with_failed)
    if stream_3_included:
        print("❌ FAIL: Stream 3 (failed test) was incorrectly included")
        return False
    else:
        print("✅ PASS: Stream 3 (failed test) was correctly excluded")
        return True

if __name__ == "__main__":
    success = test_failed_stream_exclusion()
    sys.exit(0 if success else 1)