"""
Stream Sorter data models for Stream Plus

This module provides scoring-based stream sorting functionality
"""
import json
import os
import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict, field


@dataclass
class SortingCondition:
    """
    Individual condition for scoring streams
    
    Attributes:
        condition_type: Type of condition (m3u_source, video_bitrate, video_resolution, 
                       video_codec, audio_codec, video_fps)
        operator: Comparison operator (>, >=, <, <=, ==, !=) - not used for m3u_source
        value: Value to compare against (depends on condition_type)
        points: Points awarded if condition is met
    """
    condition_type: str  # m3u_source, video_bitrate, video_resolution, video_codec, audio_codec, video_fps
    operator: Optional[str] = None  # >, >=, <, <=, ==, !=
    value: Optional[Any] = None
    points: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Converts condition to dictionary"""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'SortingCondition':
        """Creates a condition from a dictionary"""
        return SortingCondition(**data)


@dataclass
class SortingRule:
    """
    Rule for sorting streams within channels based on scoring
    
    Attributes:
        id: Unique rule ID
        name: Descriptive rule name
        enabled: Whether the rule is active
        channel_ids: List of channel IDs where this rule applies (empty = all channels)
        channel_group_ids: List of channel group IDs where this rule applies
        conditions: List of scoring conditions
        description: Optional description of the rule
        test_streams_before_sorting: Whether to test streams to obtain stats before sorting
    """
    id: int
    name: str
    enabled: bool = True
    channel_ids: List[int] = field(default_factory=list)
    channel_group_ids: List[int] = field(default_factory=list)
    conditions: List[SortingCondition] = field(default_factory=list)
    description: Optional[str] = None
    test_streams_before_sorting: bool = False
    force_retest_old_streams: bool = False
    retest_days_threshold: int = 7
    
    def to_dict(self) -> Dict[str, Any]:
        """Converts rule to dictionary"""
        data = asdict(self)
        # Convert SortingCondition objects to dicts
        data['conditions'] = [
            cond.to_dict() if isinstance(cond, SortingCondition) else cond 
            for cond in self.conditions
        ]
        return data
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'SortingRule':
        """Creates a rule from a dictionary"""
        # Convert condition dicts to SortingCondition objects
        if 'conditions' in data and data['conditions']:
            data['conditions'] = [
                SortingCondition.from_dict(cond) if isinstance(cond, dict) else cond
                for cond in data['conditions']
            ]
        else:
            data['conditions'] = []
        
        # Ensure lists exist
        if 'channel_ids' not in data:
            data['channel_ids'] = []
        if 'channel_group_ids' not in data:
            data['channel_group_ids'] = []
            
        return SortingRule(**data)


class SortingRulesManager:
    """Manager for sorting rules persistence"""
    
    def __init__(self, rules_file: str = 'sorting_rules.json'):
        self.rules_file = rules_file
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Creates the rules file if it doesn't exist"""
        if not os.path.exists(self.rules_file):
            with open(self.rules_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
    
    def load_rules(self) -> List[SortingRule]:
        """Loads all rules from the file"""
        try:
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Support both formats: {"rules": [...]} and [...]
                rules_data = data.get('rules', data) if isinstance(data, dict) else data
                return [SortingRule.from_dict(rule_data) for rule_data in rules_data]
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def save_rules(self, rules: List[SortingRule]):
        """Saves all rules to the file"""
        with open(self.rules_file, 'w', encoding='utf-8') as f:
            # Save in {"rules": [...]} format for consistency
            json.dump({"rules": [rule.to_dict() for rule in rules]}, f, indent=2, ensure_ascii=False)
    
    def get_rule(self, rule_id: int) -> Optional[SortingRule]:
        """Gets a rule by its ID"""
        rules = self.load_rules()
        for rule in rules:
            if rule.id == rule_id:
                return rule
        return None
    
    def create_rule(self, rule: SortingRule) -> SortingRule:
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
    
    def update_rule(self, rule_id: int, updated_rule: SortingRule) -> Optional[SortingRule]:
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
    
    def get_rules_for_channel(self, channel_id: int) -> List[SortingRule]:
        """Gets all active rules that apply to a specific channel"""
        rules = self.load_rules()
        applicable_rules = []
        
        for rule in rules:
            if not rule.enabled:
                continue
            
            # If no channels assigned, rule applies to all channels
            if not rule.channel_ids and not rule.channel_group_ids:
                applicable_rules.append(rule)
            # If channel is explicitly assigned
            elif channel_id in rule.channel_ids:
                applicable_rules.append(rule)
            # TODO: Add channel group logic when groups are implemented
        
        return applicable_rules
    
    def get_next_id(self) -> int:
        """Gets the next available ID"""
        rules = self.load_rules()
        if rules:
            return max(r.id for r in rules) + 1
        return 1


class StreamSorter:
    """Stream scoring and sorting engine"""
    
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
            resolution_str: Resolution string (e.g., '1920x1080', '1280x720')
        
        Returns:
            Normalized resolution: '720p', '1080p', '2160p', or 'SD'
        """
        if not resolution_str:
            return None
        
        width, height = StreamSorter._parse_resolution(resolution_str)
        
        if height is None:
            return None
        
        # Classify based on height
        if height >= 2000:
            return '2160p'
        elif height >= 1000:
            return '1080p'
        elif height >= 700:
            return '720p'
        else:
            return 'SD'
    
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
        elif operator == '!=':
            return actual != expected
        
        return False
    
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
        
        # If we have stats, assume they're recent unless we can check the date
        return False
    
    @staticmethod
    def _evaluate_condition(condition: SortingCondition, stream: Dict[str, Any]) -> int:
        """
        Evaluates a single condition against a stream
        Returns points if condition is met, 0 otherwise
        """
        stream_stats = stream.get('stream_stats') or {}
        
        # M3U Source condition
        if condition.condition_type == 'm3u_source':
            if stream.get('m3u_account') == condition.value:
                return condition.points
        
        # Video Bitrate condition
        elif condition.condition_type == 'video_bitrate':
            # Try multiple fields for bitrate (in kbps)
            # 1. output_bitrate (Dispatcharr native field)
            # 2. ffmpeg_output_bitrate (legacy field)
            # 3. bitrate_kbps (old format)
            # 4. bit_rate / 1000 (from format, convert to kbps)
            video_bitrate = None
            
            if 'output_bitrate' in stream_stats:
                video_bitrate = stream_stats['output_bitrate']
            elif 'ffmpeg_output_bitrate' in stream_stats:
                video_bitrate = stream_stats['ffmpeg_output_bitrate']
            elif 'bitrate_kbps' in stream_stats:
                video_bitrate = stream_stats['bitrate_kbps']
            elif 'bit_rate' in stream_stats and stream_stats['bit_rate']:
                video_bitrate = float(stream_stats['bit_rate']) / 1000  # Convert to kbps
            
            if video_bitrate and condition.operator and condition.value:
                if StreamSorter._compare_value(video_bitrate, condition.operator, float(condition.value)):
                    return condition.points
        
        # Video Resolution condition
        elif condition.condition_type == 'video_resolution':
            # Dispatcharr usa 'resolution' en stream_stats
            video_resolution = stream_stats.get('resolution')
            
            if video_resolution and condition.value:
                # Normalize the stream resolution to standard format (720p, 1080p, 2160p, SD)
                normalized_resolution = StreamSorter._normalize_resolution(video_resolution)
                
                if normalized_resolution:
                    # Compare normalized resolution with condition value
                    if condition.operator == '==':
                        if normalized_resolution == condition.value:
                            return condition.points
                    elif condition.operator == '!=':
                        if normalized_resolution != condition.value:
                            return condition.points
        
        # Video Codec condition
        elif condition.condition_type == 'video_codec':
            video_codec = stream_stats.get('video_codec')
            if video_codec and condition.value:
                if condition.operator == '==':
                    if video_codec.lower() == str(condition.value).lower():
                        return condition.points
                elif condition.operator == '!=':
                    if video_codec.lower() != str(condition.value).lower():
                        return condition.points
        
        # Audio Codec condition
        elif condition.condition_type == 'audio_codec':
            audio_codec = stream_stats.get('audio_codec')
            if audio_codec and condition.value:
                if condition.operator == '==':
                    if audio_codec.lower() == str(condition.value).lower():
                        return condition.points
                elif condition.operator == '!=':
                    if audio_codec.lower() != str(condition.value).lower():
                        return condition.points
        
        # Video FPS condition
        elif condition.condition_type == 'video_fps':
            # Dispatcharr usa 'source_fps' en stream_stats
            video_fps = stream_stats.get('source_fps')
            if video_fps and condition.operator and condition.value:
                if StreamSorter._compare_value(video_fps, condition.operator, float(condition.value)):
                    return condition.points
        
        return 0
    
    @staticmethod
    def score_stream(rule: SortingRule, stream: Dict[str, Any]) -> int:
        """
        Calculates total score for a stream based on all conditions in a rule
        Returns sum of points from all matching conditions
        """
        total_score = 0
        
        for condition in rule.conditions:
            total_score += StreamSorter._evaluate_condition(condition, stream)
        
        return total_score
    
    @staticmethod
    def sort_streams(rule: SortingRule, streams: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sorts streams by their total score (highest to lowest)
        Returns list of streams with added 'score' field
        """
        # Calculate score for each stream
        scored_streams = []
        for stream in streams:
            score = StreamSorter.score_stream(rule, stream)
            stream_with_score = stream.copy()
            stream_with_score['score'] = score
            scored_streams.append(stream_with_score)
        
        # Sort by score (descending)
        scored_streams.sort(key=lambda x: x['score'], reverse=True)
        
        return scored_streams
    
    @staticmethod
    def preview_sorting(rule: SortingRule, streams: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Previews how streams would be sorted
        
        Returns:
            Dictionary with sorting information:
            {
                'total_streams': int,
                'sorted_streams': List[Dict] (with scores),
                'conditions_count': int,
                'score_distribution': Dict[int, int]  # score -> count
            }
        """
        sorted_streams = StreamSorter.sort_streams(rule, streams)
        
        # Calculate score distribution
        score_distribution = {}
        for stream in sorted_streams:
            score = stream['score']
            score_distribution[score] = score_distribution.get(score, 0) + 1
        
        return {
            'total_streams': len(streams),
            'sorted_streams': sorted_streams,
            'conditions_count': len(rule.conditions),
            'score_distribution': score_distribution,
            'max_possible_score': sum(cond.points for cond in rule.conditions)
        }
