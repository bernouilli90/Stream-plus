#!/usr/bin/env python3
"""Test script to create a sample channel group"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stream_sorter_models import ChannelGroupsManager, ChannelGroup

def main():
    manager = ChannelGroupsManager()

    # Create a sample group
    group = ChannelGroup(
        id="test_group_1",
        name="Test Sports Channels",
        description="A test group for sports channels",
        channel_ids=[1, 2, 3]  # Sample channel IDs
    )

    # Save the group
    manager.save_group(group)
    print(f"Created test group: {group.name} with ID: {group.id}")

    # Load and verify
    groups = manager.load_groups()
    print(f"Total groups loaded: {len(groups)}")
    for g in groups:
        print(f"  - {g.name} ({g.id}): {len(g.channel_ids)} channels")

if __name__ == "__main__":
    main()