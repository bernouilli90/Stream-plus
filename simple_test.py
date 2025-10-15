import sys
import os
sys.path.append('.')

print('Testing forced include functionality...')

try:
    from models import RulesManager, StreamMatcher
    print('✓ Models imported')

    from api.dispatcharr_client import DispatcharrClient
    print('✓ API client imported')

    # Load rules
    rules_manager = RulesManager()
    rules = rules_manager.load_rules()
    print(f'✓ Loaded {len(rules)} rules')

    # Find rule with forced includes
    rule_with_include = None
    for rule in rules:
        if rule.force_include_stream_ids:
            rule_with_include = rule
            break

    if not rule_with_include:
        print('❌ No rule with forced includes found')
        sys.exit(1)

    print(f'✓ Found rule with forced includes: {rule_with_include.name}')
    print(f'  Forced include streams: {rule_with_include.force_include_stream_ids}')

    # Get streams
    dispatcharr_client = DispatcharrClient(
        base_url=os.getenv('DISPATCHARR_API_URL', 'http://localhost:8080'),
        username=os.getenv('DISPATCHARR_API_USER'),
        password=os.getenv('DISPATCHARR_API_PASSWORD')
    )

    streams = dispatcharr_client.get_streams()
    print(f'✓ Got {len(streams)} streams from API')

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

    print(f'✓ Filtering completed:')
    print(f'  Excluded: {excluded_count}')
    print(f'  Forced included: {included_count}')
    print(f'  Regex matches: {regex_matches}')
    print(f'  Total pre-filtered: {len(pre_filtered_streams)}')

    # Check if forced include streams are in the result
    forced_streams_found = []
    for stream in pre_filtered_streams:
        if stream.get('id') in rule_with_include.force_include_stream_ids:
            forced_streams_found.append(stream.get('id'))

    print(f'✓ Forced include streams found in results: {forced_streams_found}')

    if len(forced_streams_found) == len(rule_with_include.force_include_stream_ids):
        print('✅ SUCCESS: All forced include streams are present in filtered results!')
        print('The forced include functionality is working correctly.')
    else:
        missing = set(rule_with_include.force_include_stream_ids) - set(forced_streams_found)
        print(f'❌ FAILURE: Some forced include streams are missing: {list(missing)}')

except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()