#!/usr/bin/env python
"""
Test to verify the corrected stream testing logic
"""
import sys
import os
from datetime import datetime, timedelta, timezone

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import StreamMatcher

def test_needs_stream_testing():
    """Test the _needs_stream_testing function with timestamps"""

    print("Testing _needs_stream_testing function...")

    # Test 1: No stats at all -> should need testing
    result1 = StreamMatcher._needs_stream_testing(None, None, False, 7)
    print(f"No stats: {result1} (expected: True)")
    assert result1 == True, "Should need testing when no stats"

    # Test 2: Empty stats -> should need testing
    result2 = StreamMatcher._needs_stream_testing({}, None, False, 7)
    print(f"Empty stats: {result2} (expected: True)")
    assert result2 == True, "Should need testing when empty stats"

    # Test 3: Force retest -> should need testing
    result3 = StreamMatcher._needs_stream_testing({'resolution': '1080p'}, None, True, 7)
    print(f"Force retest: {result3} (expected: True)")
    assert result3 == True, "Should need testing when force_retest=True"

    # Test 4: Recent stats (now) -> should NOT need testing
    now = datetime.now(timezone.utc).isoformat()
    result4 = StreamMatcher._needs_stream_testing({'resolution': '1080p'}, now, False, 7)
    print(f"Recent stats (now): {result4} (expected: False)")
    assert result4 == False, "Should NOT need testing when stats are recent"

    # Test 5: Old stats (10 days ago) -> should need testing
    old_time = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    result5 = StreamMatcher._needs_stream_testing({'resolution': '1080p'}, old_time, False, 7)
    print(f"Old stats (10 days ago): {result5} (expected: True)")
    assert result5 == True, "Should need testing when stats are older than threshold"

    # Test 6: Stats at threshold (7 days ago) -> should need testing (conservative approach)
    threshold_time = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    result6 = StreamMatcher._needs_stream_testing({'resolution': '1080p'}, threshold_time, False, 7)
    print(f"Stats at threshold (7 days ago): {result6} (expected: True - conservative)")
    assert result6 == True, "Should need testing when stats are at threshold (conservative approach)"

    print("✅ All tests passed!")
    return True

if __name__ == "__main__":
    success = test_needs_stream_testing()
    sys.exit(0 if success else 1)