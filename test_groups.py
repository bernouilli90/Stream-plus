#!/usr/bin/env python3
from stream_sorter_models import ChannelGroupsManager

manager = ChannelGroupsManager()
groups = manager.load_groups()
print(f'Loaded {len(groups)} groups')
for group in groups:
    print(f'  - {group.name} (ID: {group.id})')