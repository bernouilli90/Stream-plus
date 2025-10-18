#!/usr/bin/env python
"""
Stream Plus - Rule Execution CLI
Execute auto-assignment and sorting rules from command line
"""
import argparse
import sys
import os
import json
from datetime import datetime, timezone
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import RulesManager, StreamMatcher, AutoAssignmentRule
from stream_sorter_models import SortingRulesManager, StreamSorter, SortingRule
from api.dispatcharr_client import DispatcharrClient

# M3U refresh state file
M3U_REFRESH_STATE_FILE = 'm3u_refresh_state.json'

def load_m3u_refresh_state():
    """Load M3U refresh state from file"""
    if os.path.exists(M3U_REFRESH_STATE_FILE):
        try:
            with open(M3U_REFRESH_STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"last_refresh": None}

def save_m3u_refresh_state(state):
    """Save M3U refresh state to file"""
    try:
        with open(M3U_REFRESH_STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"Error saving M3U refresh state: {e}")

def update_m3u_refresh_time():
    """Update the last M3U refresh timestamp"""
    state = load_m3u_refresh_state()
    # Always save in UTC
    utc_now = datetime.now(timezone.utc)
    state["last_refresh"] = utc_now.isoformat().replace('+00:00', 'Z')
    save_m3u_refresh_state(state)


class RuleExecutor:
    """Executes auto-assignment and sorting rules"""
    
    def __init__(self):
        """Initialize rule executor"""
        self.dispatcharr_client = DispatcharrClient(
            base_url=os.getenv('DISPATCHARR_API_URL', 'http://localhost:8080'),
            username=os.getenv('DISPATCHARR_API_USER'),
            password=os.getenv('DISPATCHARR_API_PASSWORD')
        )
        self.assignment_manager = RulesManager()
        self.sorting_manager = SortingRulesManager(dispatcharr_client=self.dispatcharr_client)
        
    def execute_assignment_rules(self, rule_ids: Optional[List[int]] = None, verbose: bool = False) -> dict:
        """
        Execute auto-assignment rules
        
        Args:
            rule_ids: List of specific rule IDs to execute (None = all enabled rules)
            verbose: Print detailed progress information
            
        Returns:
            Dictionary with execution statistics
        """
        print("\n" + "="*80)
        print("EXECUTING AUTO-ASSIGNMENT RULES")
        print("="*80 + "\n")
        
        # Refresh M3U sources before executing rules
        print("🔄 Refreshing M3U sources...")
        try:
            refresh_result = self.dispatcharr_client.refresh_m3u_sources()
            # Update the refresh timestamp
            update_m3u_refresh_time()
            print("✅ M3U sources refreshed successfully")
            if verbose:
                print(f"   Refresh result: {refresh_result}")
        except Exception as e:
            print(f"⚠️  Warning: Failed to refresh M3U sources: {e}")
            print("   Continuing with rule execution...")
        
        print()  # Add blank line
        
        # Load rules
        all_rules = self.assignment_manager.load_rules()
        
        # Filter rules
        if rule_ids:
            rules_to_execute = [r for r in all_rules if r.id in rule_ids]
        else:
            rules_to_execute = [r for r in all_rules if r.enabled]
        
        if not rules_to_execute:
            print("⚠️  No rules to execute")
            return {'total_rules': 0, 'successful': 0, 'failed': 0, 'total_streams_added': 0, 'total_matches': 0}
        
        print(f"📋 Found {len(rules_to_execute)} rule(s) to execute\n")
        
        total_streams_added = 0
        total_matches = 0
        successful_rules = 0
        failed_rules = 0
        
        for idx, rule in enumerate(rules_to_execute, 1):
            print(f"[{idx}/{len(rules_to_execute)}] Executing rule: {rule.name} (ID: {rule.id})")
            print(f"    Channel ID: {rule.channel_id}")
            
            try:
                # Get channel info
                channel = self.dispatcharr_client.get_channel(rule.channel_id)
                if not channel:
                    print(f"    ❌ Error: Channel {rule.channel_id} not found")
                    failed_rules += 1
                    continue
                
                print(f"    Target channel: {channel.get('name', 'Unknown')}")
                
                # Load all streams
                if verbose:
                    print(f"    Loading streams...")
                streams = self.dispatcharr_client.get_streams()
                
                if verbose:
                    print(f"    Found {len(streams)} total streams")
                
                # Test streams if required
                failed_test_stream_ids = set()  # Track streams that failed testing
                if rule.test_streams_before_sorting:
                    if verbose:
                        print(f"    Testing streams to get stats...")
                    
                    # Filter streams by basic conditions first, but also consider forced inclusions/exclusions
                    basic_matches = []
                    for stream in streams:
                        stream_id = stream.get('id')
                        
                        # Skip streams that are explicitly excluded (don't test them)
                        if stream_id in rule.force_exclude_stream_ids:
                            continue
                        
                        # Include streams that are explicitly included (test them even if they don't match basic conditions)
                        if stream_id in rule.force_include_stream_ids:
                            basic_matches.append(stream)
                            continue
                        
                        # For remaining streams, check basic conditions
                        if StreamMatcher._stream_matches_basic_conditions(rule, stream):
                            basic_matches.append(stream)
                    
                    if verbose:
                        print(f"    {len(basic_matches)} stream(s) passed basic filtering (including forced includes, excluding forced excludes)")
                    
                    # Test streams
                    tested = 0
                    failed = 0
                    skipped = 0
                    
                    for stream in basic_matches:
                        stream_stats = stream.get('stream_stats')
                        
                        # Check if we need to test
                        needs_test = StreamMatcher._needs_stream_testing(
                            stream_stats,
                            stream.get('stream_stats_updated_at'),
                            rule.force_retest_old_streams,
                            rule.retest_days_threshold
                        )
                        
                        if needs_test:
                            if verbose:
                                print(f"      Testing: {stream.get('name', 'unknown')} (ID: {stream.get('id')})")
                            
                            test_result = self.dispatcharr_client.test_stream(stream['id'])
                            if test_result and test_result.get('success'):
                                tested += 1
                            else:
                                failed += 1
                                failed_test_stream_ids.add(stream['id'])  # Track failed streams
                                # Clear stream stats for failed streams
                                try:
                                    self.dispatcharr_client.clear_stream_stats(stream['id'])
                                    if verbose:
                                        print(f"        Cleared stats for failed stream")
                                except Exception as e:
                                    if verbose:
                                        print(f"        Warning: Failed to clear stats: {e}")
                                if verbose:
                                    print(f"        ❌ Test failed")
                        else:
                            skipped += 1
                    
                    if verbose or tested > 0 or failed > 0:
                        print(f"    Stream testing: {tested} tested, {failed} failed, {skipped} skipped")
                    
                    # Reload streams with updated stats
                    streams = self.dispatcharr_client.get_streams()
                
                # Find matching streams
                matches = StreamMatcher.evaluate_rule(rule, streams, failed_test_stream_ids)
                print(f"    ✓ Found {len(matches)} matching stream(s)")
                
                if len(matches) > 0:
                    # Assign streams to channel
                    if rule.replace_existing_streams:
                        # Clear existing streams
                        if verbose:
                            print(f"    Removing existing streams from channel...")
                        channel_streams = self.dispatcharr_client.get_channel_streams(rule.channel_id)
                        for stream in channel_streams:
                            self.dispatcharr_client.remove_stream_from_channel(rule.channel_id, stream['id'])
                    
                    # Add matching streams
                    added = 0
                    for stream in matches:
                        if verbose:
                            print(f"      Adding: {stream.get('name', 'unknown')}")
                        
                        success = self.dispatcharr_client.add_stream_to_channel(
                            rule.channel_id, 
                            stream['id']
                        )
                        if success:
                            added += 1
                    
                    print(f"    ✅ Added {added} stream(s) to channel")
                    total_streams_added += added
                    total_matches += len(matches)
                    successful_rules += 1
                else:
                    print(f"    ℹ️  No streams to add")
                    successful_rules += 1
                
            except Exception as e:
                print(f"    ❌ Error: {str(e)}")
                failed_rules += 1
            
            print()  # Blank line between rules
        
        # Summary
        print("="*80)
        print("AUTO-ASSIGNMENT SUMMARY")
        print("="*80)
        print(f"Total rules executed: {len(rules_to_execute)}")
        print(f"Successful: {successful_rules}")
        print(f"Failed: {failed_rules}")
        print(f"Total matches found: {total_matches}")
        print(f"Total streams added: {total_streams_added}")
        print("="*80 + "\n")
        
        return {
            'total_rules': len(rules_to_execute),
            'successful': successful_rules,
            'failed': failed_rules,
            'total_matches': total_matches,
            'total_streams_added': total_streams_added
        }
    
    def execute_sorting_rules(self, rule_ids: Optional[List[int]] = None, verbose: bool = False) -> dict:
        """
        Execute sorting rules
        
        Args:
            rule_ids: List of specific rule IDs to execute (None = all enabled rules)
            verbose: Print detailed progress information
            
        Returns:
            Dictionary with execution statistics
        """
        print("\n" + "="*80)
        print("EXECUTING SORTING RULES")
        print("="*80 + "\n")
        
        # Refresh M3U sources before executing rules
        print("🔄 Refreshing M3U sources...")
        try:
            self.dispatcharr_client.refresh_m3u_sources()
            # Update the refresh timestamp
            update_m3u_refresh_time()
            print("✅ M3U sources refreshed successfully\n")
        except Exception as e:
            print(f"⚠️  Failed to refresh M3U sources: {e}\n")
        
        # Load rules
        all_rules = self.sorting_manager.load_rules()
        
        # Filter rules
        if rule_ids:
            rules_to_execute = [r for r in all_rules if r.id in rule_ids]
        else:
            rules_to_execute = [r for r in all_rules if r.enabled]
        
        if not rules_to_execute:
            print("⚠️  No rules to execute")
            return {'total_rules': 0, 'successful': 0, 'failed': 0, 'total_channels_sorted': 0}
        
        print(f"📋 Found {len(rules_to_execute)} rule(s) to execute\n")
        
        total_channels_sorted = 0
        successful_rules = 0
        failed_rules = 0
        
        for idx, rule in enumerate(rules_to_execute, 1):
            print(f"[{idx}/{len(rules_to_execute)}] Executing rule: {rule.name} (ID: {rule.id})")
            
            try:
                # Determine target channels
                if rule.all_channels:
                    # Apply to all channels
                    all_channels = self.dispatcharr_client.get_channels()
                    channel_ids = [ch['id'] for ch in all_channels]
                    print(f"    Target channels: All ({len(channel_ids)} channel(s))")
                elif rule.channel_ids:
                    # Apply to specific channels
                    channel_ids = rule.channel_ids
                    print(f"    Target channels: {len(channel_ids)} specific channel(s)")
                elif rule.channel_group_ids:
                    # Apply to channels in specified groups
                    channel_ids = []
                    for group_id in rule.channel_group_ids:
                        if group_id in self.sorting_manager.groups_manager.groups:
                            group = self.sorting_manager.groups_manager.groups[group_id]
                            channel_ids.extend(group.channel_ids)
                            print(f"    Target group '{group.name}' (ID: {group_id}): {len(group.channel_ids)} channel(s)")
                        else:
                            print(f"    ⚠️  Group {group_id} not found or has no channels")
                    
                    if channel_ids:
                        print(f"    Target channels: {len(channel_ids)} channel(s) from {len(rule.channel_group_ids)} group(s)")
                    else:
                        print(f"    ⚠️  No channels found in specified groups, skipping rule")
                        continue
                else:
                    # Default: apply to all channels
                    all_channels = self.dispatcharr_client.get_channels()
                    channel_ids = [ch['id'] for ch in all_channels]
                    print(f"    Target channels: All ({len(channel_ids)} channel(s))")
                
                # Test streams if required
                if rule.test_streams_before_sorting:
                    if verbose:
                        print(f"    Testing streams to get stats...")
                    
                    # Get all streams
                    streams = self.dispatcharr_client.get_streams()
                    
                    # Get streams that belong to target channels
                    channel_stream_ids = set()
                    for channel_id in channel_ids:
                        channel_streams = self.dispatcharr_client.get_channel_streams(channel_id)
                        channel_stream_ids.update(s['id'] for s in channel_streams)
                    
                    # Filter to only test channel streams
                    streams_to_test = [s for s in streams if s['id'] in channel_stream_ids]
                    
                    if verbose:
                        print(f"    {len(streams_to_test)} stream(s) in target channels")
                    
                    tested = 0
                    failed = 0
                    skipped = 0
                    
                    for stream in streams_to_test:
                        stream_stats = stream.get('stream_stats')
                        
                        # Check if we need to test
                        needs_test = StreamSorter._needs_stream_testing(
                            stream_stats,
                            rule.force_retest_old_streams,
                            rule.retest_days_threshold
                        )
                        
                        if needs_test:
                            if verbose:
                                print(f"      Testing: {stream.get('name', 'unknown')}")
                            
                            success = self.dispatcharr_client.test_stream(stream['id'])
                            if success:
                                tested += 1
                            else:
                                failed += 1
                        else:
                            skipped += 1
                    
                    if verbose or tested > 0 or failed > 0:
                        print(f"    Stream testing: {tested} tested, {failed} failed, {skipped} skipped")
                
                # Get M3U accounts for stream enrichment
                m3u_accounts = self.dispatcharr_client.get_m3u_accounts()
                m3u_accounts_dict = {account['id']: account for account in m3u_accounts}
                
                # Sort each channel
                sorted_count = 0
                for channel_id in channel_ids:
                    if verbose:
                        print(f"      Sorting channel {channel_id}...")
                    
                    # Get channel streams
                    channel_streams = self.dispatcharr_client.get_channel_streams(channel_id)
                    
                    if not channel_streams:
                        if verbose:
                            print(f"        (empty channel, skipped)")
                        continue
                    
                    # Enrich streams with M3U account information for sorting conditions
                    for stream in channel_streams:
                        m3u_id = stream.get('m3u_account_id')  # Some APIs use m3u_account_id
                        if m3u_id is None:
                            m3u_id = stream.get('m3u_account')  # Others use m3u_account
                        if m3u_id is not None and m3u_id in m3u_accounts_dict:
                            stream['m3u_account'] = m3u_id
                    
                    # Score and sort streams
                    sorted_streams = StreamSorter.sort_streams(rule, channel_streams)
                    
                    # Update order in Dispatcharr
                    channel = self.dispatcharr_client.get_channel(channel_id)
                    if channel:
                        original_streams = channel.get('streams', [])
                        sorted_stream_ids = [s['id'] for s in sorted_streams]
                        channel['streams'] = sorted_stream_ids
                        
                        if verbose:
                            print(f"        Original streams order: {original_streams}")
                            print(f"        New streams order: {sorted_stream_ids}")
                        
                        try:
                            # Try PATCH first (partial update)
                            result = self.dispatcharr_client.patch_channel(channel_id, {'streams': sorted_stream_ids})
                            if verbose:
                                print(f"        PATCH result: {result}")
                            
                            # Verify the update worked
                            updated_channel = self.dispatcharr_client.get_channel(channel_id)
                            if updated_channel and updated_channel.get('streams') == sorted_stream_ids:
                                success = True
                                if verbose:
                                    print(f"        ✓ Order updated successfully with PATCH")
                            else:
                                # If PATCH didn't work, try PUT with full channel object
                                if verbose:
                                    print(f"        PATCH failed, trying PUT...")
                                result = self.dispatcharr_client.update_channel(channel_id, channel)
                                if verbose:
                                    print(f"        PUT result: {result}")
                                
                                # Verify again
                                updated_channel = self.dispatcharr_client.get_channel(channel_id)
                                if updated_channel and updated_channel.get('streams') == sorted_stream_ids:
                                    success = True
                                    if verbose:
                                        print(f"        ✓ Order updated successfully with PUT")
                                else:
                                    success = False
                                    if verbose:
                                        print(f"        ❌ Order update failed - Dispatcharr automatically reorders streams by ID descending")
                                        print(f"        Note: This is a limitation of the Dispatcharr API, not the sorting logic")
                                        print(f"        Expected: {sorted_stream_ids}")
                                        print(f"        Actual: {updated_channel.get('streams') if updated_channel else 'None'}")
                        except Exception as e:
                            success = False
                            if verbose:
                                print(f"        ❌ Update failed with exception: {str(e)}")
                    else:
                        success = False
                        if verbose:
                            print(f"        ❌ Could not retrieve channel {channel_id}")
                    
                    if success:
                        sorted_count += 1
                        if verbose:
                            print(f"        ✓ Sorted {len(sorted_streams)} stream(s)")
                    else:
                        if verbose:
                            print(f"        ❌ Failed to update order")
                
                print(f"    ✅ Sorted {sorted_count} channel(s)")
                total_channels_sorted += sorted_count
                successful_rules += 1
                
            except Exception as e:
                print(f"    ❌ Error: {str(e)}")
                failed_rules += 1
            
            print()  # Blank line between rules
        
        # Summary
        print("="*80)
        print("SORTING SUMMARY")
        print("="*80)
        print(f"Total rules executed: {len(rules_to_execute)}")
        print(f"Successful: {successful_rules}")
        print(f"Failed: {failed_rules}")
        print(f"Total channels sorted: {total_channels_sorted}")
        print("="*80 + "\n")
        
        return {
            'total_rules': len(rules_to_execute),
            'successful': successful_rules,
            'failed': failed_rules,
            'total_channels_sorted': total_channels_sorted
        }
    
    def execute_single_sorting_rule(self, rule: SortingRule, verbose: bool = False) -> dict:
        """
        Execute a single sorting rule
        
        Args:
            rule: The sorting rule to execute
            verbose: Print detailed progress information
            
        Returns:
            Dictionary with execution statistics for this rule
        """
        # Determine target channels
        if rule.all_channels:
            # Apply to all channels
            all_channels = self.dispatcharr_client.get_channels()
            channel_ids = [ch['id'] for ch in all_channels]
            if verbose:
                print(f"    Target channels: All ({len(channel_ids)} channel(s))")
        elif rule.channel_ids:
            channel_ids = rule.channel_ids
            if verbose:
                print(f"    Target channels: {len(channel_ids)} specific channel(s)")
        else:
            # Expand group assignments
            channel_ids = []
            if rule.channel_group_ids:
                channel_ids = self.sorting_manager.groups_manager.expand_group_ids(rule.channel_group_ids)
                if verbose:
                    print(f"    Target channels: {len(channel_ids)} from group(s)")
        
        # Get M3U accounts for stream enrichment
        m3u_accounts = self.dispatcharr_client.get_m3u_accounts()
        m3u_accounts_dict = {account['id']: account for account in m3u_accounts}
        
        if not channel_ids:
            return {'channels_sorted': 0, 'error': 'No channels to sort'}
        
        # Test streams if required
        if rule.test_streams_before_sorting:
            if verbose:
                print(f"    Testing streams to get stats...")
            
            # Get all streams
            streams = self.dispatcharr_client.get_streams()
            
            # Get streams that belong to target channels
            channel_stream_ids = set()
            for channel_id in channel_ids:
                channel_streams = self.dispatcharr_client.get_channel_streams(channel_id)
                channel_stream_ids.update(s['id'] for s in channel_streams)
            
            # Filter to only test channel streams
            streams_to_test = [s for s in streams if s['id'] in channel_stream_ids]
            
            if verbose:
                print(f"    {len(streams_to_test)} stream(s) in target channels")
            
            tested = 0
            failed = 0
            skipped = 0
            
            for stream in streams_to_test:
                stream_stats = stream.get('stream_stats')
                
                # Check if we need to test
                needs_test = StreamSorter._needs_stream_testing(
                    stream_stats,
                    rule.force_retest_old_streams,
                    rule.retest_days_threshold
                )
                
                if needs_test:
                    # Test the stream
                    try:
                        updated_stream = self.dispatcharr_client.update_stream(stream['id'], stream)
                        if updated_stream and updated_stream.get('stream_stats'):
                            tested += 1
                        else:
                            failed += 1
                    except Exception as e:
                        if verbose:
                            print(f"      ❌ Failed to test stream {stream['id']}: {str(e)}")
                        failed += 1
                else:
                    skipped += 1
            
            if verbose:
                print(f"    Stream testing: {tested} tested, {skipped} skipped, {failed} failed")
        
        # Sort each channel
        sorted_count = 0
        for channel_id in channel_ids:
            if verbose:
                print(f"      Sorting channel {channel_id}...")
            
            try:
                # Get channel streams
                channel_streams = self.dispatcharr_client.get_channel_streams(channel_id)
                
                if not channel_streams:
                    if verbose:
                        print(f"        (empty channel, skipped)")
                    continue
                
                # Enrich streams with M3U account information for sorting conditions
                for stream in channel_streams:
                    m3u_id = stream.get('m3u_account_id')  # Some APIs use m3u_account_id
                    if m3u_id is None:
                        m3u_id = stream.get('m3u_account')  # Others use m3u_account
                    if m3u_id is not None and m3u_id in m3u_accounts_dict:
                        stream['m3u_account'] = m3u_id
                
                # Score and sort streams
                sorted_streams = StreamSorter.sort_streams(rule, channel_streams)
                
                # Update order in Dispatcharr
                channel = self.dispatcharr_client.get_channel(channel_id)
                if channel:
                    original_streams = channel.get('streams', [])
                    sorted_stream_ids = [s['id'] for s in sorted_streams]
                    channel['streams'] = sorted_stream_ids
                    
                    if verbose:
                        print(f"        Original streams order: {original_streams}")
                        print(f"        New streams order: {sorted_stream_ids}")
                    
                    try:
                        # Try PATCH first (partial update)
                        result = self.dispatcharr_client.patch_channel(channel_id, {'streams': sorted_stream_ids})
                        if verbose:
                            print(f"        PATCH result: {result}")
                        
                        # Verify the update worked
                        updated_channel = self.dispatcharr_client.get_channel(channel_id)
                        if updated_channel and updated_channel.get('streams') == sorted_stream_ids:
                            success = True
                            if verbose:
                                print(f"        ✓ Order updated successfully with PATCH")
                        else:
                            # If PATCH didn't work, try PUT with full channel object
                            if verbose:
                                print(f"        PATCH failed, trying PUT...")
                            result = self.dispatcharr_client.update_channel(channel_id, channel)
                            if verbose:
                                print(f"        PUT result: {result}")
                            
                            # Verify again
                            updated_channel = self.dispatcharr_client.get_channel(channel_id)
                            if updated_channel and updated_channel.get('streams') == sorted_stream_ids:
                                success = True
                                if verbose:
                                    print(f"        ✓ Order updated successfully with PUT")
                            else:
                                success = False
                                if verbose:
                                    print(f"        ❌ Order update failed - Dispatcharr automatically reorders streams by ID descending")
                                    print(f"        Note: This is a limitation of the Dispatcharr API, not the sorting logic")
                                    print(f"        Expected: {sorted_stream_ids}")
                                    print(f"        Actual: {updated_channel.get('streams') if updated_channel else 'None'}")
                    except Exception as e:
                        success = False
                        if verbose:
                            print(f"        ❌ Update failed with exception: {str(e)}")
                else:
                    success = False
                    if verbose:
                        print(f"        ❌ Could not retrieve channel {channel_id}")
                
                if success:
                    sorted_count += 1
                    if verbose:
                        print(f"        ✓ Sorted {len(sorted_streams)} stream(s)")
                else:
                    if verbose:
                        print(f"        ❌ Failed to update order")
                        
            except Exception as e:
                if verbose:
                    print(f"        ❌ Error sorting channel {channel_id}: {str(e)}")
        
        return {'channels_sorted': sorted_count}


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Execute Stream Plus auto-assignment and sorting rules',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Execute all enabled auto-assignment rules
  python execute_rules.py --assignment
  
  # Execute all enabled sorting rules
  python execute_rules.py --sorting
  
  # Execute both (assignment first, then sorting)
  python execute_rules.py --all
  
  # Execute with verbose output
  python execute_rules.py --all --verbose
  
  # Execute specific assignment rules by ID
  python execute_rules.py --assignment --rule-ids 1 2 3
  
  # Execute specific sorting rules by ID
  python execute_rules.py --sorting --rule-ids 1 2
        """
    )
    
    # Action group (mutually exclusive)
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument(
        '--assignment', '-a',
        action='store_true',
        help='Execute auto-assignment rules only'
    )
    action_group.add_argument(
        '--sorting', '-s',
        action='store_true',
        help='Execute sorting rules only'
    )
    action_group.add_argument(
        '--all',
        action='store_true',
        help='Execute both assignment and sorting rules (assignment first)'
    )
    
    # Optional arguments
    parser.add_argument(
        '--rule-ids',
        type=int,
        nargs='+',
        help='Specific rule IDs to execute (default: all enabled rules)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Print detailed progress information'
    )
    
    args = parser.parse_args()
    
    # Print header
    print("\n" + "="*80)
    print("STREAM PLUS - RULE EXECUTION CLI")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Create executor
    executor = RuleExecutor()
    
    # Execute rules based on arguments
    try:
        if args.all:
            # Execute assignment rules first
            assignment_stats = executor.execute_assignment_rules(
                rule_ids=args.rule_ids,
                verbose=args.verbose
            )
            
            # Then execute sorting rules
            sorting_stats = executor.execute_sorting_rules(
                rule_ids=args.rule_ids,
                verbose=args.verbose
            )
            
            # Combined summary
            print("="*80)
            print("COMBINED SUMMARY")
            print("="*80)
            print(f"Assignment rules: {assignment_stats['successful']}/{assignment_stats['total_rules']} successful")
            print(f"Streams added: {assignment_stats['total_streams_added']}")
            print(f"Sorting rules: {sorting_stats['successful']}/{sorting_stats['total_rules']} successful")
            print(f"Channels sorted: {sorting_stats['total_channels_sorted']}")
            print("="*80 + "\n")
            
        elif args.assignment:
            executor.execute_assignment_rules(
                rule_ids=args.rule_ids,
                verbose=args.verbose
            )
            
        elif args.sorting:
            executor.execute_sorting_rules(
                rule_ids=args.rule_ids,
                verbose=args.verbose
            )
        
        print(f"✅ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Execution interrupted by user")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
