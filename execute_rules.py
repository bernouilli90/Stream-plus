#!/usr/bin/env python
"""
Stream Plus - Rule Execution CLI
Execute auto-assignment and sorting rules from command line
"""
import argparse
import sys
import os
from datetime import datetime
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import RulesManager, StreamMatcher, AutoAssignmentRule
from stream_sorter_models import SortingRulesManager, StreamSorter, SortingRule
from api.dispatcharr_client import DispatcharrClient


class RuleExecutor:
    """Executes auto-assignment and sorting rules"""
    
    def __init__(self):
        """Initialize rule executor"""
        self.assignment_manager = RulesManager()
        self.sorting_manager = SortingRulesManager()
        self.dispatcharr_client = DispatcharrClient(
            base_url=os.getenv('DISPATCHARR_API_URL', 'http://localhost:8080'),
            username=os.getenv('DISPATCHARR_API_USER'),
            password=os.getenv('DISPATCHARR_API_PASSWORD')
        )
        
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
                if rule.test_streams_before_sorting:
                    if verbose:
                        print(f"    Testing streams to get stats...")
                    
                    # Filter streams by basic conditions first
                    basic_matches = [
                        s for s in streams 
                        if StreamMatcher._stream_matches_basic_conditions(rule, s)
                    ]
                    
                    if verbose:
                        print(f"    {len(basic_matches)} stream(s) passed basic filtering")
                    
                    # Test streams
                    tested = 0
                    failed = 0
                    skipped = 0
                    
                    for stream in basic_matches:
                        stream_stats = stream.get('stream_stats')
                        
                        # Check if we need to test
                        needs_test = StreamMatcher._needs_stream_testing(
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
                                if verbose:
                                    print(f"        ❌ Test failed")
                        else:
                            skipped += 1
                    
                    if verbose or tested > 0 or failed > 0:
                        print(f"    Stream testing: {tested} tested, {failed} failed, {skipped} skipped")
                    
                    # Reload streams with updated stats
                    streams = self.dispatcharr_client.get_streams()
                
                # Find matching streams
                matches = StreamMatcher.evaluate_rule(rule, streams)
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
                if rule.channel_ids:
                    channel_ids = rule.channel_ids
                    print(f"    Target channels: {len(channel_ids)} specific channel(s)")
                else:
                    # Apply to all channels
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
                    
                    # Score and sort streams
                    sorted_streams = StreamSorter.sort_streams(rule, channel_streams)
                    
                    # Update order in Dispatcharr
                    channel = self.dispatcharr_client.get_channel(channel_id)
                    if channel:
                        channel['streams'] = [s['id'] for s in sorted_streams]
                        success = self.dispatcharr_client.update_channel(channel_id, channel)
                    else:
                        success = False
                    
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
                
                # Score and sort streams
                sorted_streams = StreamSorter.sort_streams(rule, channel_streams)
                
                # Update order in Dispatcharr
                channel = self.dispatcharr_client.get_channel(channel_id)
                if channel:
                    channel['streams'] = [s['id'] for s in sorted_streams]
                    success = self.dispatcharr_client.update_channel(channel_id, channel)
                else:
                    success = False
                
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
