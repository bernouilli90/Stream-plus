"""
Data models for Stream Plus
"""
import json
import os
import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict

# Import Stream Sorter models
from stream_sorter_models import (
    SortingCondition,
    SortingRule,
    SortingRulesManager,
    StreamSorter
)


@dataclass
class AutoAssignmentRule:
    """
    Automatic stream to channel assignment rule
    
    Attributes:
        id: Unique rule ID
        name: Descriptive rule name
        channel_id: ID of the channel to which streams will be assigned
        enabled: Whether the rule is active
        replace_existing_streams: If True, removes existing streams before assigning
        
        # Filtering conditions (all optional):
        regex_pattern: Regular expression to filter by stream name
        m3u_account_id: M3U account ID (None = all)
        
        # Video stats conditions:
        video_bitrate_operator: Comparison operator (>, >=, <, <=, ==)
        video_bitrate_value: Value in kbps to compare
        video_codec: Required video codec (h264, h265, etc.)
        video_resolution: Required resolution (720p, 1080p, 2160p, SD)
        video_fps: Required exact FPS
        
        # Audio stats conditions:
        audio_codec: Required audio codec (ac3, aac, etc.)
        
        # Stream testing options:
        test_streams_before_sorting: Whether to test streams to obtain stats before applying rule
        force_retest_old_streams: Whether to force retesting all streams (even with recent stats)
        retest_days_threshold: Days threshold for considering stats "old" (default 7)
    """
    id: int
    name: str
    channel_id: int
    enabled: bool = True
    replace_existing_streams: bool = False
    
    # Filtering conditions
    regex_pattern: Optional[str] = None
    m3u_account_id: Optional[int] = None
    
    # Video conditions
    video_bitrate_operator: Optional[str] = None  # >, >=, <, <=, ==
    video_bitrate_value: Optional[float] = None  # kbps
    video_codec: Optional[List[str]] = None  # Can be a list: ["h264", "h265"]
    video_resolution: Optional[List[str]] = None  # Can be a list: ["720p", "1080p", "SD"]
    video_fps: Optional[List[float]] = None  # Can be a list: [25.0, 30.0, 50.0]
    
    # Audio conditions
    audio_codec: Optional[List[str]] = None  # Can be a list: ["aac", "ac3"]
    
    # Stream testing options
    test_streams_before_sorting: bool = False
    force_retest_old_streams: bool = False
    retest_days_threshold: int = 7
    
    def to_dict(self) -> Dict[str, Any]:
        """Converts rule to dictionary"""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'AutoAssignmentRule':
        """Creates a rule from a dictionary, with automatic migration from old format"""
        # Migrate old resolution format to new format
        if 'video_resolution_operator' in data or 'video_resolution_width' in data or 'video_resolution_height' in data:
            # Old format detected - remove old fields and don't set video_resolution
            # (user will need to reconfigure resolution in the new format)
            data.pop('video_resolution_operator', None)
            data.pop('video_resolution_width', None)
            data.pop('video_resolution_height', None)
            if 'video_resolution' not in data:
                data['video_resolution'] = None
        
        # Normalize single values to lists for multi-value fields
        multi_value_fields = ['video_codec', 'video_resolution', 'video_fps', 'audio_codec']
        for field in multi_value_fields:
            if field in data and data[field] is not None:
                # If it's a string or number, convert to list
                if not isinstance(data[field], list):
                    data[field] = [data[field]]
        
        return AutoAssignmentRule(**data)


class RulesManager:
    """Auto-assignment rules manager"""
    
    def __init__(self, rules_file: str = 'auto_assignment_rules.json'):
        self.rules_file = rules_file
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Creates the rules file if it doesn't exist"""
        if not os.path.exists(self.rules_file):
            with open(self.rules_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
    
    def load_rules(self) -> List[AutoAssignmentRule]:
        """Loads all rules from the file"""
        try:
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Support both formats: {"rules": [...]} and [...]
                rules_data = data.get('rules', data) if isinstance(data, dict) else data
                return [AutoAssignmentRule.from_dict(rule_data) for rule_data in rules_data]
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def save_rules(self, rules: List[AutoAssignmentRule]):
        """Saves all rules to the file"""
        with open(self.rules_file, 'w', encoding='utf-8') as f:
            # Save in {"rules": [...]} format for consistency
            json.dump({"rules": [rule.to_dict() for rule in rules]}, f, indent=2, ensure_ascii=False)
    
    def get_rule(self, rule_id: int) -> Optional[AutoAssignmentRule]:
        """Gets a rule by its ID"""
        rules = self.load_rules()
        for rule in rules:
            if rule.id == rule_id:
                return rule
        return None
    
    def create_rule(self, rule: AutoAssignmentRule) -> AutoAssignmentRule:
        """Creates a new rule"""
        rules = self.load_rules()
        
        # Assign new ID
        if rules:
            rule.id = max(r.id for r in rules) + 1
        else:
            rule.id = 1
        
        rules.append(rule)
        self.save_rules(rules)
        return rule
    
    def update_rule(self, rule_id: int, updated_rule: AutoAssignmentRule) -> Optional[AutoAssignmentRule]:
        """Updates an existing rule"""
        rules = self.load_rules()
        
        for i, rule in enumerate(rules):
            if rule.id == rule_id:
                updated_rule.id = rule_id  # Keep the same ID
                rules[i] = updated_rule
                self.save_rules(rules)
                return updated_rule
        
        return None
    
    def delete_rule(self, rule_id: int) -> bool:
        """Deletes a rule"""
        rules = self.load_rules()
        initial_count = len(rules)
        rules = [r for r in rules if r.id != rule_id]
        
        if len(rules) < initial_count:
            self.save_rules(rules)
            return True
        
        return False
    
    def get_rules_by_channel(self, channel_id: int) -> List[AutoAssignmentRule]:
        """Gets all rules for a specific channel"""
        rules = self.load_rules()
        return [r for r in rules if r.channel_id == channel_id]
    
    def get_next_id(self) -> int:
        """Gets the next available ID"""
        rules = self.load_rules()
        if rules:
            return max(r.id for r in rules) + 1
        return 1


class StreamMatcher:
    """Auto-assignment rules evaluator"""
    
    @staticmethod
    def _compare_value(actual: Optional[float], operator: str, expected: float) -> bool:
        """Compares two values according to operator"""
        if actual is None:
            return False
        
        if operator == '>':
            return actual > expected
        elif operator == '>=':
            return actual >= expected
        elif operator == '<':
            return actual < expected
        elif operator == '<=':
            return actual <= expected
        elif operator == '==':
            return actual == expected
        
        return False
    
    @staticmethod
    def _parse_resolution(resolution_str: Optional[str]) -> tuple[Optional[int], Optional[int]]:
        """
        Parses a resolution string (e.g.: '1920x1080') to tuple (width, height)
        """
        if not resolution_str:
            return None, None
        
        # Search for WIDTHxHEIGHT pattern
        match = re.search(r'(\d+)x(\d+)', str(resolution_str))
        if match:
            return int(match.group(1)), int(match.group(2))
        
        return None, None
    
    @staticmethod
    def _normalize_resolution(resolution_str: Optional[str]) -> Optional[str]:
        """
        Normalizes a resolution string to standard format (720p, 1080p, 2160p, SD)
        
        Args:
            resolution_str: Resolution string (e.g., '1920x1080', '1280x720', '3840x2160')
        
        Returns:
            Normalized resolution string or None
        """
        if not resolution_str:
            return None
        
        # Parse width and height
        width, height = StreamMatcher._parse_resolution(resolution_str)
        
        if height is None:
            return None
        
        # Map height to standard resolutions
        if height >= 2000:  # 4K (2160p)
            return '2160p'
        elif height >= 1000:  # Full HD (1080p)
            return '1080p'
        elif height >= 700:  # HD (720p)
            return '720p'
        else:  # SD (anything below 720p)
            return 'SD'
    
    @staticmethod
    def _extract_stream_stat(stream_stats: Optional[Dict], key: str, default=None):
        """Extracts a value from stream statistics"""
        if not stream_stats:
            return default
        
        return stream_stats.get(key, default)
    
    @staticmethod
    def _needs_stream_testing(stream_stats: Optional[Dict], 
                             force_retest: bool = False, 
                             retest_days_threshold: int = 7) -> bool:
        """
        Determines if a stream needs to be tested
        
        Args:
            stream_stats: Stream statistics dictionary
            force_retest: If True, always needs testing
            retest_days_threshold: Number of days after which stats are considered old
            
        Returns:
            True if stream needs testing, False otherwise
        """
        if force_retest:
            return True
        
        # No stats at all
        if not stream_stats or not isinstance(stream_stats, dict):
            return True
        
        # Check if stats are recent enough
        from datetime import datetime, timedelta, timezone
        
        threshold = datetime.now(timezone.utc) - timedelta(days=retest_days_threshold)
        
        # stream_stats should have a 'last_tested' or similar field
        # In Dispatcharr, check stream_stats_updated_at
        # For now, if we have stats, assume they're recent unless we can check the date
        return False
    
    @staticmethod
    def evaluate_rule(rule: AutoAssignmentRule, streams: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Evaluates a rule against a list of streams and returns matching ones
        
        Args:
            rule: Auto-assignment rule
            streams: List of streams (dictionaries with stream data)
        
        Returns:
            List of streams that meet ALL rule conditions
        """
        matching_streams = []
        
        for stream in streams:
            if StreamMatcher._stream_matches_rule(rule, stream):
                matching_streams.append(stream)
        
        return matching_streams
    
    @staticmethod
    def evaluate_basic_conditions(rule: AutoAssignmentRule, streams: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Evaluates ONLY basic conditions that don't require stream stats (regex, m3u_account)
        This is useful for pre-filtering before testing streams.
        
        Args:
            rule: Auto-assignment rule
            streams: List of streams (dictionaries with stream data)
        
        Returns:
            List of streams that meet basic conditions (regex, m3u_account)
        """
        matching_streams = []
        
        for stream in streams:
            if StreamMatcher._stream_matches_basic_conditions(rule, stream):
                matching_streams.append(stream)
        
        return matching_streams
    
    @staticmethod
    def _stream_matches_basic_conditions(rule: AutoAssignmentRule, stream: Dict[str, Any]) -> bool:
        """
        Verifies if a stream meets basic conditions that don't require stats
        (regex pattern, m3u_account_id)
        """
        # 1. Filter by regex in name
        if rule.regex_pattern:
            stream_name = stream.get('name', '')
            try:
                if not re.search(rule.regex_pattern, stream_name, re.IGNORECASE):
                    return False
            except re.error:
                # If regex is invalid, no match
                return False
        
        # 2. Filter by M3U account
        if rule.m3u_account_id is not None:
            if stream.get('m3u_account') != rule.m3u_account_id:
                return False
        
        return True
    
    @staticmethod
    def _stream_matches_rule(rule: AutoAssignmentRule, stream: Dict[str, Any]) -> bool:
        """Verifies if a stream meets all rule conditions"""
        
        # First check basic conditions
        if not StreamMatcher._stream_matches_basic_conditions(rule, stream):
            return False
        
        # Check if rule requires stream statistics
        rule_requires_stats = (
            rule.video_bitrate_operator or
            rule.video_codec or
            rule.video_resolution or
            rule.video_fps or
            rule.audio_codec
        )
        
        # From here, we need stream statistics
        stream_stats = stream.get('stream_stats')
        
        # If rule requires stats but stream doesn't have them, fail immediately
        if rule_requires_stats and not stream_stats:
            return False
        
        # 3. Filter by video bitrate
        if rule.video_bitrate_operator and rule.video_bitrate_value is not None:
            # Try both field names: output_bitrate (native) and ffmpeg_output_bitrate (legacy)
            video_bitrate = (
                StreamMatcher._extract_stream_stat(stream_stats, 'output_bitrate') or
                StreamMatcher._extract_stream_stat(stream_stats, 'ffmpeg_output_bitrate')
            )
            if not StreamMatcher._compare_value(
                video_bitrate, 
                rule.video_bitrate_operator, 
                rule.video_bitrate_value
            ):
                return False
        
        # 4. Filter by video codec
        if rule.video_codec:
            video_codec = StreamMatcher._extract_stream_stat(stream_stats, 'video_codec')
            # video_codec is now a list, check if stream's codec is in the list
            if video_codec not in rule.video_codec:
                return False
        
        # 5. Filter by video resolution
        if rule.video_resolution:
            # Get stream resolution and normalize it to the standard format
            # Dispatcharr uses 'resolution' key in stream_stats (e.g., "1920x1080")
            video_resolution = StreamMatcher._extract_stream_stat(stream_stats, 'resolution')
            normalized_resolution = StreamMatcher._normalize_resolution(video_resolution)
            
            # DEBUG: Print resolution comparison
            print(f"DEBUG - Stream '{stream.get('name', 'unknown')}': raw_resolution={video_resolution}, normalized={normalized_resolution}, required={rule.video_resolution}, has_stats={bool(stream_stats)}")
            
            # video_resolution is now a list, check if normalized resolution is in the list
            if normalized_resolution not in rule.video_resolution:
                print(f"  ❌ Resolution mismatch: {normalized_resolution} not in {rule.video_resolution}")
                return False
            print(f"  ✓ Resolution matches!")
        
        # 6. Filter by FPS
        if rule.video_fps is not None:
            # Dispatcharr uses 'source_fps' key in stream_stats
            video_fps = StreamMatcher._extract_stream_stat(stream_stats, 'source_fps')
            # video_fps is now a list, check if stream's fps is in the list
            if video_fps not in rule.video_fps:
                return False
        
        # 7. Filter by audio codec
        if rule.audio_codec:
            audio_codec = StreamMatcher._extract_stream_stat(stream_stats, 'audio_codec')
            # audio_codec is now a list, check if stream's codec is in the list
            if audio_codec not in rule.audio_codec:
                return False
        
        # If it passed all filters, the stream matches
        return True
    
    @staticmethod
    def preview_matches(rule: AutoAssignmentRule, streams: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Previews which streams would match the rule
        
        Returns:
            Dictionary with matching information:
            {
                'total_streams': int,
                'matching_streams': List[Dict],
                'match_count': int,
                'conditions_applied': List[str]
            }
        """
        matching = StreamMatcher.evaluate_rule(rule, streams)
        
        # List applied conditions
        conditions = []
        if rule.regex_pattern:
            conditions.append(f"Name matches regex: {rule.regex_pattern}")
        if rule.m3u_account_id is not None:
            conditions.append(f"M3U Account ID: {rule.m3u_account_id}")
        if rule.video_bitrate_operator and rule.video_bitrate_value:
            conditions.append(f"Video bitrate {rule.video_bitrate_operator} {rule.video_bitrate_value} kbps")
        if rule.video_codec:
            conditions.append(f"Video codec: {rule.video_codec}")
        if rule.video_resolution:
            conditions.append(f"Resolution: {rule.video_resolution}")
        if rule.video_fps is not None:
            conditions.append(f"FPS: {rule.video_fps}")
        if rule.audio_codec:
            conditions.append(f"Audio codec: {rule.audio_codec}")
        
        return {
            'total_streams': len(streams),
            'matching_streams': matching,
            'match_count': len(matching),
            'conditions_applied': conditions
        }
