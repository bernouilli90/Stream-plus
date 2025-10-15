print("Starting test script...")

import sys
sys.path.append('.')
print("Added to path")

from app import app
print("App imported")

from dispatcharr_client import DispatcharrClient
print("Client imported")

from stream_sorter_models import StreamSorter
print("Sorter imported")

# Test the preview functionality
print("Entering app context...")
with app.app_context():
    print("In app context")
    client = DispatcharrClient()
    print("Client created")

    sorter = StreamSorter(client)
    print("Sorter created")

    # Get all rules first
    rules = sorter.get_sorting_rules()
    print(f'Available rules: {[r.name for r in rules]}')

    # Get a sample rule that has m3u_source conditions
    group_rule = next((r for r in rules if r.name == 'Group'), None)

    if group_rule:
        print(f'Testing rule: {group_rule.name}')
        print(f'Rule conditions: {[c.condition_type for c in group_rule.conditions]}')

        # Get streams with M3U enrichment
        streams = client.get_streams()
        print(f'Total streams: {len(streams)}')

        m3u_accounts = client.get_m3u_accounts()
        print(f'M3U accounts: {len(m3u_accounts)}')
        m3u_account_map = {acc['id']: acc for acc in m3u_accounts}

        # Enrich streams
        enriched_count = 0
        for stream in streams:
            if 'm3u_account' in stream and stream['m3u_account'] in m3u_account_map:
                stream['m3u_account_name'] = m3u_account_map[stream['m3u_account']]['name']
                enriched_count += 1

        print(f'Enriched streams: {enriched_count}')

        # Test preview
        preview = sorter.preview_sorting(group_rule, streams[:5])  # Test with first 5 streams
        print(f'Preview results for first 5 streams:')
        for result in preview:
            print(f'  Stream {result.stream_id}: {result.total_points} points')
    else:
        print('No Group rule found')

print("Test script completed")