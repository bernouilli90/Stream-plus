#!/usr/bin/env python3
"""
Test the new clear_stream_stats implementation using PUT with complete stream object
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import json

# Add the api directory to the path
import sys
sys.path.insert(0, 'api')

from dispatcharr_client import DispatcharrClient


class TestClearStreamStatsPUT(unittest.TestCase):
    def setUp(self):
        self.client = DispatcharrClient("http://localhost:8080")
        self.stream_id = 123

        # Mock stream object with stats
        self.mock_stream_with_stats = {
            'id': self.stream_id,
            'name': 'Test Stream',
            'stream_stats': {
                'bitrate': 5000,
                'codec': 'h264',
                'resolution': '1920x1080'
            },
            'stream_stats_updated_at': '2024-01-01T12:00:00Z',
            'other_field': 'some_value'
        }

        # Expected stream after clearing
        self.expected_cleared_stream = {
            'id': self.stream_id,
            'name': 'Test Stream',
            'stream_stats': {},
            'other_field': 'some_value'
            # Note: stream_stats_updated_at should be removed
        }

    @patch.object(DispatcharrClient, 'get_stream')
    @patch.object(DispatcharrClient, 'update_stream')
    def test_clear_stream_stats_success(self, mock_update_stream, mock_get_stream):
        """Test successful clearing of stream stats using PUT"""

        # Mock the get_stream to return current stream
        mock_get_stream.return_value = self.mock_stream_with_stats.copy()

        # Mock the update_stream to return the cleared stream
        mock_update_stream.return_value = self.expected_cleared_stream.copy()

        # Call the method
        result = self.client.clear_stream_stats(self.stream_id)

        # Verify get_stream was called to retrieve current stream
        mock_get_stream.assert_called_once_with(self.stream_id)

        # Verify update_stream was called with the cleared stream
        expected_cleared = self.expected_cleared_stream.copy()
        mock_update_stream.assert_called_once_with(self.stream_id, expected_cleared)

        # Verify the result
        self.assertEqual(result, self.expected_cleared_stream)

    @patch.object(DispatcharrClient, 'get_stream')
    @patch.object(DispatcharrClient, 'update_stream')
    def test_clear_stream_stats_without_timestamp(self, mock_update_stream, mock_get_stream):
        """Test clearing stats when stream has no timestamp field"""

        # Stream without timestamp
        stream_without_timestamp = {
            'id': self.stream_id,
            'name': 'Test Stream',
            'stream_stats': {'bitrate': 3000},
            'other_field': 'value'
        }

        expected_cleared = {
            'id': self.stream_id,
            'name': 'Test Stream',
            'stream_stats': {},
            'other_field': 'value'
        }

        mock_get_stream.return_value = stream_without_timestamp
        mock_update_stream.return_value = expected_cleared

        result = self.client.clear_stream_stats(self.stream_id)

        # Verify update_stream was called with stream without timestamp field
        mock_update_stream.assert_called_once_with(self.stream_id, expected_cleared)

        self.assertEqual(result, expected_cleared)

    @patch.object(DispatcharrClient, 'get_stream')
    def test_clear_stream_stats_get_fails(self, mock_get_stream):
        """Test handling when GET request fails"""

        mock_get_stream.side_effect = Exception("GET failed")

        with self.assertRaises(Exception):
            self.client.clear_stream_stats(self.stream_id)


if __name__ == '__main__':
    unittest.main()