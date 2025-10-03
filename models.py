"""
Data models for Stream Plus
"""
import json
import os
import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict


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
        video_resolution_operator: Comparison operator
        video_resolution_width: Minimum/maximum resolution width
        video_resolution_height: Minimum/maximum resolution height
        video_fps: Required exact FPS
        
        # Audio stats conditions:
        audio_codec: Required audio codec (ac3, aac, etc.)
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
    video_codec: Optional[str] = None
    video_resolution_operator: Optional[str] = None
    video_resolution_width: Optional[int] = None
    video_resolution_height: Optional[int] = None
    video_fps: Optional[float] = None
    
    # Audio conditions
    audio_codec: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converts rule to dictionary"""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'AutoAssignmentRule':
        """Creates a rule from a dictionary"""
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
                return [AutoAssignmentRule.from_dict(rule_data) for rule_data in data]
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def save_rules(self, rules: List[AutoAssignmentRule]):
        """Saves all rules to the file"""
        with open(self.rules_file, 'w', encoding='utf-8') as f:
            json.dump([rule.to_dict() for rule in rules], f, indent=2, ensure_ascii=False)
    
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
    def _extract_stream_stat(stream_stats: Optional[Dict], key: str, default=None):
        """Extracts a value from stream statistics"""
        if not stream_stats:
            return default
        
        return stream_stats.get(key, default)
    
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
    def _stream_matches_rule(rule: AutoAssignmentRule, stream: Dict[str, Any]) -> bool:
        """Verifies if a stream meets all rule conditions"""
        
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
        
        # From here, we need stream statistics
        stream_stats = stream.get('stream_stats')
        
        # 3. Filter by video bitrate
        if rule.video_bitrate_operator and rule.video_bitrate_value is not None:
            video_bitrate = StreamMatcher._extract_stream_stat(stream_stats, 'video_bitrate')
            if not StreamMatcher._compare_value(
                video_bitrate, 
                rule.video_bitrate_operator, 
                rule.video_bitrate_value
            ):
                return False
        
        # 4. Filter by video codec
        if rule.video_codec:
            video_codec = StreamMatcher._extract_stream_stat(stream_stats, 'video_codec')
            if video_codec != rule.video_codec:
                return False
        
        # 5. Filter by video resolution
        if rule.video_resolution_operator and (
            rule.video_resolution_width is not None or 
            rule.video_resolution_height is not None
        ):
            # Get stream resolution
            video_resolution = StreamMatcher._extract_stream_stat(stream_stats, 'video_resolution')
            stream_width, stream_height = StreamMatcher._parse_resolution(video_resolution)
            
            # Compare width if specified
            if rule.video_resolution_width is not None:
                if not StreamMatcher._compare_value(
                    stream_width,
                    rule.video_resolution_operator,
                    rule.video_resolution_width
                ):
                    return False
            
            # Compare height if specified
            if rule.video_resolution_height is not None:
                if not StreamMatcher._compare_value(
                    stream_height,
                    rule.video_resolution_operator,
                    rule.video_resolution_height
                ):
                    return False
        
        # 6. Filter by FPS
        if rule.video_fps is not None:
            video_fps = StreamMatcher._extract_stream_stat(stream_stats, 'video_fps')
            # For FPS we use exact comparison
            if video_fps != rule.video_fps:
                return False
        
        # 7. Filter by audio codec
        if rule.audio_codec:
            audio_codec = StreamMatcher._extract_stream_stat(stream_stats, 'audio_codec')
            if audio_codec != rule.audio_codec:
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
        if rule.video_resolution_operator and (rule.video_resolution_width or rule.video_resolution_height):
            res_desc = f"{rule.video_resolution_width or '?'}x{rule.video_resolution_height or '?'}"
            conditions.append(f"Resolution {rule.video_resolution_operator} {res_desc}")
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
