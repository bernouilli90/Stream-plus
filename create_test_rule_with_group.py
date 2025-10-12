#!/usr/bin/env python3
"""Test script to create a sample sorting rule with channel groups"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stream_sorter_models import SortingRulesManager, SortingRule, SortingCondition

def main():
    manager = SortingRulesManager()

    # Create a test condition
    condition = SortingCondition(
        condition_type='video_bitrate',
        operator='>',
        value=1000,
        points=10
    )

    # Create a rule that uses the channel group
    rule = SortingRule(
        id=0,  # Will be assigned by manager
        name='Test Group Rule',
        description='A test rule that applies to a channel group',
        enabled=True,
        channel_ids=[],  # No individual channels
        channel_group_ids=['1'],  # Use the group we created
        conditions=[condition],
        test_streams_before_sorting=False,
        force_retest_old_streams=False,
        retest_days_threshold=7
    )

    # Save the rule
    created_rule = manager.create_rule(rule)
    print(f"Created test rule: {created_rule.name} with ID: {created_rule.id}")
    print(f"Rule applies to channel groups: {created_rule.channel_group_ids}")

    # Test the expansion functionality
    from stream_sorter_models import ChannelGroupsManager
    channel_groups_manager = ChannelGroupsManager()
    expanded_channels = channel_groups_manager.expand_group_ids(['1'])
    print(f"Group '1' expands to channels: {expanded_channels}")

    # Verify the rule was created correctly
    rules = manager.load_rules()
    group_rule = next((r for r in rules if r.name == 'Test Group Rule'), None)
    if group_rule:
        print(f"Rule verification: Found rule with {len(group_rule.channel_group_ids)} channel groups")
    else:
        print("Rule verification: Rule not found!")

if __name__ == "__main__":
    main()