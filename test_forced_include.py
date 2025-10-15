#!/usr/bin/env python3
"""
Test script to verify forced include functionality
"""
import os
import sys
sys.path.append('.')

from models import RulesManager, StreamMatcher
from api.dispatcharr_client import DispatcharrClient

def test_forced_include():
    # Load rules
    rules_manager = RulesManager()
    rules = rules_manager.load_rules()

    # Find rule with forced includes
    rule_with_include = None
    for rule in rules:
        if rule.force_include_stream_ids:
            rule_with_include = rule
            break

    if not rule_with_include:
        print("No rule with forced includes found")
        return

    print(f"Testing rule: {rule_with_include.name} (ID: {rule_with_include.id})")
    print(f"Forced include streams: {rule_with_include.force_include_stream_ids}")

    # Get streams
    dispatcharr_client = DispatcharrClient(
        base_url=os.getenv('DISPATCHARR_API_URL', 'http://localhost:8080'),
        username=os.getenv('DISPATCHARR_API_USER'),
        password=os.getenv('DISPATCHARR_API_PASSWORD')
    )

    streams = dispatcharr_client.get_streams()
    print(f"Total streams available: {len(streams)}")

    # Test the filtering logic (same as in execute_auto_assignment_in_background)
    pre_filtered_streams = []
    excluded_count = 0
    included_count = 0
    regex_matches = 0

    for stream in streams:
        stream_id = stream.get('id')

        # Skip streams that are explicitly excluded
        if stream_id in rule_with_include.force_exclude_stream_ids:
            excluded_count += 1
            continue

        # Include streams that are explicitly included
        if stream_id in rule_with_include.force_include_stream_ids:
            pre_filtered_streams.append(stream)
            included_count += 1
            continue

        # For remaining streams, check basic conditions
        if StreamMatcher._stream_matches_basic_conditions(rule_with_include, stream):
            pre_filtered_streams.append(stream)
            regex_matches += 1

    print(f"Filtering results:")
    print(f"  Excluded: {excluded_count}")
    print(f"  Forced included: {included_count}")
    print(f"  Regex matches: {regex_matches}")
    print(f"  Total pre-filtered: {len(pre_filtered_streams)}")

    # Check if forced include streams are in the result
    forced_streams_found = []
    for stream in pre_filtered_streams:
        if stream.get('id') in rule_with_include.force_include_stream_ids:
            forced_streams_found.append(stream.get('id'))

    print(f"Forced include streams found in results: {forced_streams_found}")

    if len(forced_streams_found) == len(rule_with_include.force_include_stream_ids):
        print("✅ SUCCESS: All forced include streams are present in filtered results!")
    else:
        print("❌ FAILURE: Some forced include streams are missing!")

if __name__ == "__main__":
    test_forced_include()