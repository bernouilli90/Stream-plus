from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, Response, stream_with_context
import os
import json
import time
from queue import Queue
from threading import Thread
from dotenv import load_dotenv
from api.dispatcharr_client import DispatcharrClient
from models import RulesManager, AutoAssignmentRule, StreamMatcher
from stream_sorter_models import (
    SortingRulesManager,
    SortingRule,
    SortingCondition,
    StreamSorter
)

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Configure API client
dispatcharr_client = DispatcharrClient(
    base_url=os.getenv('DISPATCHARR_API_URL', 'http://localhost:8080'),
    username=os.getenv('DISPATCHARR_API_USER'),
    password=os.getenv('DISPATCHARR_API_PASSWORD')
)

# Initialize auto-assignment rules manager
rules_manager = RulesManager()

# Initialize sorting rules manager
sorting_rules_manager = SortingRulesManager()

# Dictionary to store progress queues for active executions
execution_queues = {}

@app.route('/')
def index():
    """Main page with channels and streams summary"""
    try:
        channels = dispatcharr_client.get_channels()
        return render_template('index.html', channels=channels)
    except Exception as e:
        flash(f'Error getting data: {str(e)}', 'error')
        return render_template('index.html', channels=[])

@app.route('/channels')
def channels():
    """Channel management page"""
    try:
        channels_data = dispatcharr_client.get_channels()
        return render_template('channels.html', channels=channels_data)
    except Exception as e:
        flash(f'Error getting channels: {str(e)}', 'error')
        return render_template('channels.html', channels=[])

@app.route('/streams')
def streams():
    """Stream management page"""
    try:
        streams_data = dispatcharr_client.get_streams()
        return render_template('streams.html', streams=streams_data)
    except Exception as e:
        flash(f'Error getting streams: {str(e)}', 'error')
        return render_template('streams.html', streams=[])

@app.route('/auto-assign')
def auto_assign():
    """Stream auto-assignment to channels page"""
    try:
        rules = rules_manager.load_rules()
        channels = dispatcharr_client.get_channels()
        
        # Create channels dictionary by ID for easy access
        channels_dict = {channel['id']: channel for channel in channels}
        
        return render_template('auto_assign.html', rules=rules, channels=channels_dict)
    except Exception as e:
        flash(f'Error loading rules: {str(e)}', 'error')
        return render_template('auto_assign.html', rules=[], channels={})

@app.route('/api/channels', methods=['GET'])
def api_get_channels():
    """API endpoint to get all channels"""
    try:
        channels = dispatcharr_client.get_channels()
        return jsonify(channels)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/channels/<channel_id>', methods=['GET'])
def api_get_channel(channel_id):
    """API endpoint to get a specific channel"""
    try:
        channel = dispatcharr_client.get_channel(int(channel_id))
        return jsonify(channel)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/channels/<channel_id>', methods=['PUT'])
def api_update_channel(channel_id):
    """API endpoint to update a channel"""
    try:
        data = request.get_json()
        result = dispatcharr_client.update_channel(int(channel_id), data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/streams', methods=['GET'])
def api_get_streams():
    """API endpoint to get all streams with optional search"""
    try:
        search_term = request.args.get('search', '').strip()
        streams = dispatcharr_client.get_streams()
        
        # Filter by search term if provided
        if search_term:
            search_lower = search_term.lower()
            streams = [
                stream for stream in streams 
                if search_lower in (stream.get('name', '') or '').lower() or
                   search_lower in str(stream.get('id', '')) or
                   search_lower in (stream.get('url', '') or '').lower()
            ]
            # Limit to 10 results for search
            streams = streams[:10]
        
        return jsonify(streams)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/streams/<stream_id>', methods=['GET'])
def api_get_stream(stream_id):
    """API endpoint to get a specific stream"""
    try:
        stream = dispatcharr_client.get_stream(int(stream_id))
        return jsonify(stream)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/streams/<stream_id>', methods=['PUT'])
def api_update_stream(stream_id):
    """API endpoint to update a stream"""
    try:
        data = request.get_json()
        result = dispatcharr_client.update_stream(int(stream_id), data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/streams/<stream_id>/start', methods=['POST'])
def api_start_stream(stream_id):
    """API endpoint to start a stream"""
    try:
        result = dispatcharr_client.start_stream(int(stream_id))
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/streams/<stream_id>/stop', methods=['POST'])
def api_stop_stream(stream_id):
    """API endpoint to stop a stream"""
    try:
        result = dispatcharr_client.stop_stream(int(stream_id))
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/channels/<int:channel_id>/streams', methods=['GET'])
def get_channel_streams(channel_id):
    """Endpoint to get all streams from a specific channel"""
    try:
        streams = dispatcharr_client.get_channel_streams(channel_id)
        return jsonify(streams)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/channels/<int:channel_id>/streams/<int:stream_id>', methods=['POST', 'DELETE'])
def manage_channel_stream(channel_id, stream_id):
    """Endpoint to add or remove a stream from a channel"""
    try:
        if request.method == 'POST':
            # Add stream to channel
            result = dispatcharr_client.add_stream_to_channel(channel_id, stream_id)
            return jsonify(result)
        elif request.method == 'DELETE':
            # Remove stream from channel
            result = dispatcharr_client.remove_stream_from_channel(channel_id, stream_id)
            return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== Auto-Assignment Rules Endpoints ==========

@app.route('/api/auto-assign-rules', methods=['GET', 'POST'])
def api_auto_assign_rules():
    """API endpoint to list and create auto-assignment rules"""
    try:
        if request.method == 'GET':
            # Get all rules
            rules = rules_manager.load_rules()
            return jsonify([rule.to_dict() for rule in rules])
        
        elif request.method == 'POST':
            # Create new rule
            data = request.get_json()
            
            # Validate required fields
            if not data.get('name'):
                return jsonify({'error': 'The "name" field is required'}), 400
            if not data.get('channel_id'):
                return jsonify({'error': 'The "channel_id" field is required'}), 400
            
            # Verify that channel exists
            channel_id = int(data['channel_id'])
            try:
                channel = dispatcharr_client.get_channel(channel_id)
                if not channel:
                    return jsonify({
                        'error': f'Channel with ID {channel_id} does not exist',
                        'details': 'Please select a valid channel'
                    }), 404
            except Exception as e:
                return jsonify({
                    'error': f'Could not verify channel with ID {channel_id}',
                    'details': str(e)
                }), 404
            
            # Create rule from data
            rule = AutoAssignmentRule(
                id=0,  # Will be auto-assigned
                name=data['name'],
                channel_id=int(data['channel_id']),
                enabled=data.get('enabled', True),
                replace_existing_streams=data.get('replace_existing_streams', False),
                regex_pattern=data.get('regex_pattern'),
                m3u_account_id=int(data['m3u_account_id']) if data.get('m3u_account_id') else None,
                video_bitrate_operator=data.get('bitrate_operator'),
                video_bitrate_value=int(data['bitrate_value']) if data.get('bitrate_value') else None,
                video_codec=data.get('video_codec'),
                video_resolution_operator=data.get('resolution_operator'),
                video_resolution_width=int(data['resolution_width']) if data.get('resolution_width') else None,
                video_resolution_height=int(data['resolution_height']) if data.get('resolution_height') else None,
                video_fps=int(data['video_fps']) if data.get('video_fps') else None,
                audio_codec=data.get('audio_codec')
            )
            
            # Save rule
            created_rule = rules_manager.create_rule(rule)
            return jsonify(created_rule.to_dict()), 201
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auto-assign-rules/<int:rule_id>', methods=['GET', 'PUT', 'DELETE'])
def api_auto_assign_rule(rule_id):
    """API endpoint to get, update or delete a specific rule"""
    try:
        if request.method == 'GET':
            # Get specific rule
            rule = rules_manager.get_rule(rule_id)
            if not rule:
                return jsonify({'error': 'Rule not found'}), 404
            return jsonify(rule.to_dict())
        
        elif request.method == 'PUT':
            # Update rule
            data = request.get_json()
            
            # Validate required fields
            if not data.get('name'):
                return jsonify({'error': 'The "name" field is required'}), 400
            if not data.get('channel_id'):
                return jsonify({'error': 'The "channel_id" field is required'}), 400
            
            # Verify that channel exists
            channel_id = int(data['channel_id'])
            try:
                channel = dispatcharr_client.get_channel(channel_id)
                if not channel:
                    return jsonify({
                        'error': f'Channel with ID {channel_id} does not exist',
                        'details': 'Please select a valid channel'
                    }), 404
            except Exception as e:
                return jsonify({
                    'error': f'Could not verify channel with ID {channel_id}',
                    'details': str(e)
                }), 404
            
            # Create updated rule
            updated_rule = AutoAssignmentRule(
                id=rule_id,
                name=data['name'],
                channel_id=int(data['channel_id']),
                enabled=data.get('enabled', True),
                replace_existing_streams=data.get('replace_existing_streams', False),
                regex_pattern=data.get('regex_pattern'),
                m3u_account_id=int(data['m3u_account_id']) if data.get('m3u_account_id') else None,
                video_bitrate_operator=data.get('bitrate_operator'),
                video_bitrate_value=int(data['bitrate_value']) if data.get('bitrate_value') else None,
                video_codec=data.get('video_codec'),
                video_resolution_operator=data.get('resolution_operator'),
                video_resolution_width=int(data['resolution_width']) if data.get('resolution_width') else None,
                video_resolution_height=int(data['resolution_height']) if data.get('resolution_height') else None,
                video_fps=int(data['video_fps']) if data.get('video_fps') else None,
                audio_codec=data.get('audio_codec')
            )
            
            # Update rule
            result = rules_manager.update_rule(rule_id, updated_rule)
            if not result:
                return jsonify({'error': 'Rule not found'}), 404
            return jsonify(result.to_dict())
        
        elif request.method == 'DELETE':
            # Delete rule
            if rules_manager.delete_rule(rule_id):
                return jsonify({'message': 'Rule deleted successfully'}), 200
            else:
                return jsonify({'error': 'Rule not found'}), 404
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auto-assign-rules/<int:rule_id>/preview', methods=['GET'])
def api_preview_rule(rule_id):
    """API endpoint to preview streams matching a rule"""
    try:
        # Get rule
        rule = rules_manager.get_rule(rule_id)
        if not rule:
            return jsonify({'error': 'Rule not found'}), 404
        
        # Verify that channel exists
        try:
            channel = dispatcharr_client.get_channel(rule.channel_id)
            if not channel:
                return jsonify({
                    'error': f'Channel with ID {rule.channel_id} does not exist',
                    'details': 'The channel assigned to this rule has been deleted or does not exist'
                }), 404
        except Exception as e:
            return jsonify({
                'error': f'Could not verify channel with ID {rule.channel_id}',
                'details': str(e)
            }), 404
        
        # Get all streams
        streams = dispatcharr_client.get_streams()
        
        # Preview matches
        preview = StreamMatcher.preview_matches(rule, streams)
        
        return jsonify(preview)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auto-assign-rules/<int:rule_id>/execute', methods=['POST'])
def api_execute_rule(rule_id):
    """API endpoint to execute an auto-assignment rule"""
    try:
        # Get rule
        rule = rules_manager.get_rule(rule_id)
        if not rule:
            return jsonify({'error': 'Rule not found'}), 404
        
        if not rule.enabled:
            return jsonify({'error': 'Rule is disabled'}), 400
        
        # Verify that channel exists
        try:
            channel = dispatcharr_client.get_channel(rule.channel_id)
            if not channel:
                return jsonify({
                    'error': f'Channel with ID {rule.channel_id} does not exist',
                    'details': 'The channel assigned to this rule has been deleted or does not exist'
                }), 404
        except Exception as e:
            return jsonify({
                'error': f'Could not verify channel with ID {rule.channel_id}',
                'details': str(e)
            }), 404
        
        # Get all streams
        streams = dispatcharr_client.get_streams()
        
        # Evaluate rule to get matching streams
        matching_streams = StreamMatcher.evaluate_rule(rule, streams)
        
        # If should replace, first remove existing streams from channel
        if rule.replace_existing_streams:
            existing_streams = dispatcharr_client.get_channel_streams(rule.channel_id)
            for stream in existing_streams:
                dispatcharr_client.remove_stream_from_channel(rule.channel_id, stream['id'])
        
        # Add matching streams to channel
        added_count = 0
        for stream in matching_streams:
            try:
                dispatcharr_client.add_stream_to_channel(rule.channel_id, stream['id'])
                added_count += 1
            except Exception as e:
                # Continue even if some stream fails (it may already be assigned)
                print(f"Error adding stream {stream['id']}: {str(e)}")
        
        return jsonify({
            'message': 'Rule executed successfully',
            'matches_found': len(matching_streams),
            'streams_added': added_count,
            'replaced_existing': rule.replace_existing_streams
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/m3u-accounts', methods=['GET'])
def api_get_m3u_accounts():
    """API endpoint to get all M3U accounts"""
    try:
        accounts = dispatcharr_client.get_m3u_accounts()
        return jsonify(accounts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auto-assign-rules/<int:rule_id>/toggle', methods=['POST'])
def api_toggle_rule(rule_id):
    """API endpoint to enable/disable a rule"""
    try:
        # Get current rule
        rule = rules_manager.get_rule(rule_id)
        if not rule:
            return jsonify({'error': 'Rule not found'}), 404
        
        # Toggle enabled state
        rule.enabled = not rule.enabled
        
        # Update rule
        updated_rule = rules_manager.update_rule(rule_id, rule)
        if not updated_rule:
            return jsonify({'error': 'Error updating rule'}), 500
        
        return jsonify({
            'success': True,
            'enabled': updated_rule.enabled,
            'message': f'Rule {"enabled" if updated_rule.enabled else "disabled"}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# STREAM SORTER ROUTES
# ============================================================================

@app.route('/stream-sorter')
def stream_sorter():
    """Stream sorting rules management page"""
    try:
        channels = dispatcharr_client.get_channels()
        sorting_rules = sorting_rules_manager.load_rules()
        m3u_accounts = dispatcharr_client.get_m3u_accounts()
        
        return render_template(
            'stream_sorter.html',
            channels=channels,
            sorting_rules=sorting_rules,
            m3u_accounts=m3u_accounts
        )
    except Exception as e:
        flash(f'Error loading sorting rules: {str(e)}', 'error')
        return render_template('stream_sorter.html', channels=[], sorting_rules=[], m3u_accounts=[])


@app.route('/api/sorting-rules', methods=['GET', 'POST'])
def api_sorting_rules():
    """API endpoint to list and create sorting rules"""
    try:
        if request.method == 'GET':
            # Get all rules
            rules = sorting_rules_manager.load_rules()
            return jsonify([rule.to_dict() for rule in rules])
        
        elif request.method == 'POST':
            # Create new rule
            data = request.get_json()
            
            # Validate required fields
            if not data.get('name'):
                return jsonify({'error': 'The "name" field is required'}), 400
            
            # Convert conditions from dict to SortingCondition objects
            conditions = []
            if 'conditions' in data and data['conditions']:
                for cond_data in data['conditions']:
                    conditions.append(SortingCondition.from_dict(cond_data))
            
            # Create rule object
            rule = SortingRule(
                id=0,  # Will be assigned by manager
                name=data['name'],
                enabled=data.get('enabled', True),
                channel_ids=data.get('channel_ids', []),
                channel_group_ids=data.get('channel_group_ids', []),
                conditions=conditions,
                description=data.get('description'),
                test_streams_before_sorting=data.get('test_streams_before_sorting', False),
                force_retest_old_streams=data.get('force_retest_old_streams', False),
                retest_days_threshold=data.get('retest_days_threshold', 7)
            )
            
            # Save rule
            created_rule = sorting_rules_manager.create_rule(rule)
            return jsonify(created_rule.to_dict()), 201
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sorting-rules/<int:rule_id>', methods=['GET', 'PUT', 'DELETE'])
def api_sorting_rule(rule_id):
    """API endpoint to get, update or delete a specific sorting rule"""
    try:
        if request.method == 'GET':
            # Get rule by ID
            rule = sorting_rules_manager.get_rule(rule_id)
            if not rule:
                return jsonify({'error': 'Rule not found'}), 404
            return jsonify(rule.to_dict())
        
        elif request.method == 'PUT':
            # Update rule
            data = request.get_json()
            
            # Validate required fields
            if not data.get('name'):
                return jsonify({'error': 'The "name" field is required'}), 400
            
            # Convert conditions from dict to SortingCondition objects
            conditions = []
            if 'conditions' in data and data['conditions']:
                for cond_data in data['conditions']:
                    if isinstance(cond_data, dict):
                        conditions.append(SortingCondition.from_dict(cond_data))
                    else:
                        conditions.append(cond_data)
            
            # Create updated rule object
            rule = SortingRule(
                id=rule_id,
                name=data['name'],
                enabled=data.get('enabled', True),
                channel_ids=data.get('channel_ids', []),
                channel_group_ids=data.get('channel_group_ids', []),
                conditions=conditions,
                description=data.get('description'),
                test_streams_before_sorting=data.get('test_streams_before_sorting', False),
                force_retest_old_streams=data.get('force_retest_old_streams', False),
                retest_days_threshold=data.get('retest_days_threshold', 7)
            )
            
            # Update rule
            updated_rule = sorting_rules_manager.update_rule(rule_id, rule)
            if not updated_rule:
                return jsonify({'error': 'Rule not found'}), 404
            
            return jsonify(updated_rule.to_dict())
        
        elif request.method == 'DELETE':
            # Delete rule
            success = sorting_rules_manager.delete_rule(rule_id)
            if not success:
                return jsonify({'error': 'Rule not found'}), 404
            return jsonify({'success': True, 'message': 'Rule deleted successfully'})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sorting-rules/<int:rule_id>/execute-stream')
def execute_sorting_rule_stream(rule_id):
    """SSE endpoint to stream execution progress"""
    execution_id = request.args.get('execution_id')
    
    if not execution_id or execution_id not in execution_queues:
        return jsonify({'error': 'Invalid execution ID'}), 400
    
    def generate():
        queue = execution_queues[execution_id]
        
        try:
            while True:
                # Get message from queue (block for max 30 seconds)
                try:
                    message = queue.get(timeout=30)
                    
                    if message is None:  # Signal to stop
                        break
                    
                    # Send SSE message
                    yield f"data: {json.dumps(message)}\n\n"
                    
                except Exception as e:
                    # Timeout or error, send keepalive
                    yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"
        finally:
            # Clean up queue when client disconnects
            if execution_id in execution_queues:
                del execution_queues[execution_id]
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )


def execute_sorting_in_background(rule_id, channel_ids, queue):
    """Execute sorting rule in background thread and send progress updates"""
    try:
        # Get the rule
        rule = sorting_rules_manager.get_rule(rule_id)
        if not rule:
            queue.put({'type': 'error', 'message': 'Rule not found'})
            queue.put(None)
            return
        
        total_sorted = 0
        total_tested = 0
        total_failed = 0
        total_skipped = 0
        processed_channels = []
        errors = []
        
        queue.put({
            'type': 'start',
            'message': f'Starting execution of rule: {rule.name}',
            'total_channels': len(channel_ids)
        })
        
        for idx, channel_id in enumerate(channel_ids, 1):
            tested_count = 0
            failed_tests = 0
            skipped_count = 0
            
            try:
                # Get channel
                queue.put({
                    'type': 'channel_start',
                    'channel_id': channel_id,
                    'channel_index': idx,
                    'total_channels': len(channel_ids),
                    'message': f'Processing channel {channel_id}...'
                })
                
                channel = None
                try:
                    channel = dispatcharr_client.get_channel(channel_id)
                except Exception as e:
                    if '404' in str(e):
                        error_msg = f'Channel {channel_id} not found'
                        errors.append(error_msg)
                        queue.put({'type': 'error', 'message': error_msg})
                        continue
                    raise
                
                if not channel or not isinstance(channel, dict):
                    error_msg = f'Channel {channel_id} not found or invalid'
                    errors.append(error_msg)
                    queue.put({'type': 'error', 'message': error_msg})
                    continue

                # Get streams
                streams = dispatcharr_client.get_channel_streams(channel_id)
                if not streams:
                    queue.put({
                        'type': 'info',
                        'message': f'Channel {channel_id} has no streams'
                    })
                    continue
                
                streams = [s for s in streams if s is not None and isinstance(s, dict)]
                if not streams:
                    continue

                queue.put({
                    'type': 'info',
                    'message': f'Found {len(streams)} streams in channel {channel.get("name", channel_id)}'
                })

                # Test streams if needed
                if rule.test_streams_before_sorting:
                    from datetime import datetime, timedelta, timezone
                    
                    streams_to_test = []
                    
                    if rule.force_retest_old_streams:
                        threshold = datetime.now(timezone.utc) - timedelta(days=rule.retest_days_threshold)
                        
                        for stream in streams:
                            has_stats = stream.get('stream_stats') and isinstance(stream.get('stream_stats'), dict)
                            stream_stats_date_str = stream.get('stream_stats_updated_at')
                            
                            if not has_stats or not stream_stats_date_str:
                                streams_to_test.append(stream['id'])
                            else:
                                try:
                                    stream_stats_date = datetime.fromisoformat(stream_stats_date_str.replace('Z', '+00:00'))
                                    
                                    if stream_stats_date <= threshold:
                                        streams_to_test.append(stream['id'])
                                    else:
                                        skipped_count += 1
                                except (ValueError, AttributeError) as e:
                                    streams_to_test.append(stream['id'])
                    else:
                        streams_to_test = [s['id'] for s in streams]
                    
                    queue.put({
                        'type': 'test_start',
                        'total_streams': len(streams_to_test),
                        'message': f'Testing {len(streams_to_test)} stream(s)...'
                    })
                    
                    # Test streams
                    for stream_idx, stream_id in enumerate(streams_to_test, 1):
                        try:
                            stream_name = next((s.get('name', f'Stream {stream_id}') for s in streams if s['id'] == stream_id), f'Stream {stream_id}')
                            
                            queue.put({
                                'type': 'test_progress',
                                'stream_id': stream_id,
                                'stream_name': stream_name,
                                'current': stream_idx,
                                'total': len(streams_to_test),
                                'message': f'Testing stream {stream_idx}/{len(streams_to_test)}: {stream_name}'
                            })
                            
                            result = dispatcharr_client.test_stream(stream_id, test_duration=10)
                            if result.get('success'):
                                tested_count += 1
                                queue.put({
                                    'type': 'test_success',
                                    'stream_id': stream_id,
                                    'message': f'✓ Stream {stream_name} tested successfully'
                                })
                            else:
                                failed_tests += 1
                                queue.put({
                                    'type': 'test_fail',
                                    'stream_id': stream_id,
                                    'message': f'✗ Failed to test stream {stream_name}: {result.get("message", "Unknown error")}'
                                })
                        except Exception as e:
                            failed_tests += 1
                            queue.put({
                                'type': 'test_fail',
                                'stream_id': stream_id,
                                'message': f'✗ Error testing stream {stream_id}: {str(e)}'
                            })
                    
                    # Reload streams
                    queue.put({
                        'type': 'info',
                        'message': 'Reloading streams with updated stats...'
                    })
                    streams = dispatcharr_client.get_channel_streams(channel_id)
                    streams = [s for s in streams if s is not None and isinstance(s, dict)]

                # Sort streams
                queue.put({
                    'type': 'sorting',
                    'message': 'Sorting streams...'
                })
                
                sorted_streams = StreamSorter.sort_streams(rule, streams)

                # Update channel
                queue.put({
                    'type': 'updating',
                    'message': f'Updating channel order...'
                })
                
                sorted_stream_ids = [s['id'] for s in sorted_streams]
                channel['streams'] = sorted_stream_ids
                dispatcharr_client.update_channel(channel_id, channel)

                # Accumulate results
                total_sorted += len(sorted_streams)
                total_tested += tested_count
                total_failed += failed_tests
                total_skipped += skipped_count
                
                processed_channels.append({
                    'channel_id': channel_id,
                    'channel_name': channel.get('name', f'Channel {channel_id}'),
                    'sorted_count': len(sorted_streams),
                    'tested_count': tested_count,
                    'failed_tests': failed_tests,
                    'skipped_count': skipped_count
                })
                
                queue.put({
                    'type': 'channel_complete',
                    'channel_id': channel_id,
                    'message': f'✓ Channel {channel.get("name", channel_id)} processed successfully ({len(sorted_streams)} streams sorted)'
                })
                
            except Exception as e:
                error_msg = f'Error processing channel {channel_id}: {str(e)}'
                errors.append(error_msg)
                queue.put({'type': 'error', 'message': error_msg})
                continue
        
        # Send final summary
        message = f'Successfully sorted {total_sorted} streams in {len(processed_channels)} channel(s)'
        if rule.test_streams_before_sorting:
            message += f' (tested: {total_tested}, failed: {total_failed}'
            if rule.force_retest_old_streams:
                message += f', skipped: {total_skipped}'
            message += ')'
        
        queue.put({
            'type': 'complete',
            'success': len(processed_channels) > 0,
            'message': message,
            'total_sorted': total_sorted,
            'total_tested': total_tested,
            'total_failed': total_failed,
            'total_skipped': total_skipped,
            'processed_channels': processed_channels,
            'errors': errors
        })
        
    except Exception as e:
        queue.put({
            'type': 'error',
            'message': f'Fatal error: {str(e)}'
        })
    finally:
        # Signal end of stream
        queue.put(None)


@app.route('/api/sorting-rules/<int:rule_id>/execute', methods=['POST'])
def execute_sorting_rule(rule_id):
    """API endpoint to execute a sorting rule on its assigned channel(s)"""
    try:
        # Get the rule
        rule = sorting_rules_manager.get_rule(rule_id)
        if not rule:
            return jsonify({'error': 'Rule not found'}), 404
        
        if not rule.enabled:
            return jsonify({'error': 'Rule is disabled'}), 400
        
        # Determinar los canales a procesar
        data = request.get_json() or {}
        manual_channel_id = data.get('channel_id')
        use_stream = data.get('stream', False)  # If true, use SSE streaming
        
        if manual_channel_id:
            # Si se proporciona un canal manualmente, usar ese
            channel_ids = [manual_channel_id]
        elif rule.channel_ids:
            # Si la regla tiene canales asignados, usar esos
            channel_ids = rule.channel_ids
        else:
            # Si no hay canales asignados ni proporcionados, error
            return jsonify({'error': 'No channels specified. Rule has no assigned channels.'}), 400
        
        # If streaming requested and rule requires testing, use background execution
        if use_stream and rule.test_streams_before_sorting:
            import uuid
            execution_id = str(uuid.uuid4())
            
            # Create queue for this execution
            queue = Queue()
            execution_queues[execution_id] = queue
            
            # Start background thread
            thread = Thread(
                target=execute_sorting_in_background,
                args=(rule_id, channel_ids, queue)
            )
            thread.daemon = True
            thread.start()
            
            return jsonify({
                'success': True,
                'execution_id': execution_id,
                'stream': True,
                'message': 'Execution started. Connect to SSE endpoint to monitor progress.'
            })
        
        # Otherwise, execute synchronously (original behavior)
        # Procesar cada canal
        total_sorted = 0
        total_tested = 0
        total_failed = 0
        total_skipped = 0
        processed_channels = []
        errors = []
        
        for channel_id in channel_ids:
            tested_count = 0
            failed_tests = 0
            skipped_count = 0
            
            try:
                # Comprobar que el canal existe
                channel = None
                try:
                    channel = dispatcharr_client.get_channel(channel_id)
                except Exception as e:
                    if '404' in str(e):
                        errors.append(f'Channel {channel_id} not found')
                        continue
                    raise
                
                if not channel or not isinstance(channel, dict):
                    print(f"DEBUG: Channel {channel_id} is None or not a dict")
                    errors.append(f'Channel {channel_id} not found or invalid')
                    continue

                # Obtener streams del canal
                streams = dispatcharr_client.get_channel_streams(channel_id)
                if not streams:
                    continue
                
                # Filtrar streams None o inválidos
                streams = [s for s in streams if s is not None and isinstance(s, dict)]
                if not streams:
                    continue

                if rule.test_streams_before_sorting:
                    from datetime import datetime, timedelta, timezone
                    
                    # Determinar qué streams testear
                    streams_to_test = []
                    
                    if rule.force_retest_old_streams:
                        # Solo testear streams con stats antiguas o sin stats
                        threshold = datetime.now(timezone.utc) - timedelta(days=rule.retest_days_threshold)
                        
                        for stream in streams:
                            # Verificar si el stream tiene stats válidos
                            has_stats = stream.get('stream_stats') and isinstance(stream.get('stream_stats'), dict)
                            stream_stats_date_str = stream.get('stream_stats_updated_at')
                            
                            if not has_stats or not stream_stats_date_str:
                                # Sin stats o sin fecha de stats, testear
                                streams_to_test.append(stream['id'])
                            else:
                                try:
                                    # Parsear la fecha del stat
                                    stream_stats_date = datetime.fromisoformat(stream_stats_date_str.replace('Z', '+00:00'))
                                    
                                    # Si es más antiguo o igual que el threshold, testear
                                    if stream_stats_date <= threshold:
                                        streams_to_test.append(stream['id'])
                                    else:
                                        # Stats recientes, omitir
                                        skipped_count += 1
                                except (ValueError, AttributeError) as e:
                                    # Error parseando fecha, testear por seguridad
                                    print(f"Error parsing stats_date for stream {stream['id']}: {e}")
                                    streams_to_test.append(stream['id'])
                    else:
                        # Testear todos los streams
                        streams_to_test = [s['id'] for s in streams]
                    
                    # Testear streams seleccionados
                    for stream_id in streams_to_test:
                        try:
                            result = dispatcharr_client.test_stream(stream_id, test_duration=10)
                            if result.get('success'):
                                tested_count += 1
                                print(f"Stream {stream_id} tested successfully")
                            else:
                                failed_tests += 1
                                print(f"Failed to test stream {stream_id}: {result.get('message', 'Unknown error')}")
                        except Exception as e:
                            failed_tests += 1
                            print(f"Error testing stream {stream_id}: {e}")
                    
                    # Recargar streams para obtener stats actualizados
                    streams = dispatcharr_client.get_channel_streams(channel_id)
                    # Filtrar streams None o inválidos después de recargar
                    streams = [s for s in streams if s is not None and isinstance(s, dict)]

                # Ordenar streams usando la regla
                sorted_streams = StreamSorter.sort_streams(rule, streams)

                # Actualizar canal con el nuevo orden
                sorted_stream_ids = [s['id'] for s in sorted_streams]
                channel['streams'] = sorted_stream_ids

                # Guardar canal actualizado
                dispatcharr_client.update_channel(channel_id, channel)

                # Acumular resultados
                total_sorted += len(sorted_streams)
                total_tested += tested_count
                total_failed += failed_tests
                total_skipped += skipped_count
                processed_channels.append({
                    'channel_id': channel_id,
                    'channel_name': channel.get('name', f'Channel {channel_id}'),
                    'sorted_count': len(sorted_streams),
                    'tested_count': tested_count,
                    'failed_tests': failed_tests,
                    'skipped_count': skipped_count
                })
                
            except Exception as e:
                errors.append(f'Error processing channel {channel_id}: {str(e)}')
                print(f"Error processing channel {channel_id}: {str(e)}")
                continue
        
        # Preparar mensaje de respuesta
        if not processed_channels:
            return jsonify({
                'success': False,
                'message': 'No channels were processed successfully',
                'errors': errors
            }), 400
        
        message = f'Successfully sorted {total_sorted} streams in {len(processed_channels)} channel(s)'
        if rule.test_streams_before_sorting:
            message += f' (tested: {total_tested}, failed: {total_failed}'
            if rule.force_retest_old_streams:
                message += f', skipped: {total_skipped}'
            message += ')'
        
        return jsonify({
            'success': True,
            'message': message,
            'total_sorted': total_sorted,
            'total_tested': total_tested if rule.test_streams_before_sorting else 0,
            'total_failed': total_failed if rule.test_streams_before_sorting else 0,
            'total_skipped': total_skipped if rule.test_streams_before_sorting and rule.force_retest_old_streams else 0,
            'processed_channels': processed_channels,
            'errors': errors if errors else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sorting-rules/<int:rule_id>/preview', methods=['POST'])
def preview_sorting_rule(rule_id):
    """API endpoint to preview sorting results without applying them"""
    try:
        data = request.get_json() or {}
        channel_id = data.get('channel_id')
        
        if not channel_id:
            return jsonify({'error': 'channel_id is required'}), 400
        
        # Get the rule
        rule = sorting_rules_manager.get_rule(rule_id)
        if not rule:
            return jsonify({'error': 'Rule not found'}), 404
        
        # Get streams from the channel
        streams = dispatcharr_client.get_channel_streams(channel_id)
        
        # Generate preview
        preview = StreamSorter.preview_sorting(rule, streams)
        
        return jsonify(preview)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sorting-rules/<int:rule_id>/toggle', methods=['POST'])
def toggle_sorting_rule(rule_id):
    """API endpoint to enable/disable a sorting rule"""
    try:
        # Get the rule
        rule = sorting_rules_manager.get_rule(rule_id)
        if not rule:
            return jsonify({'error': 'Rule not found'}), 404
        
        # Toggle enabled state
        rule.enabled = not rule.enabled
        
        # Update rule
        updated_rule = sorting_rules_manager.update_rule(rule_id, rule)
        if not updated_rule:
            return jsonify({'error': 'Error updating rule'}), 500
        
        return jsonify({
            'success': True,
            'enabled': updated_rule.enabled,
            'message': f'Rule {"enabled" if updated_rule.enabled else "disabled"}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Use watchdog reloader for better Windows compatibility
    app.run(debug=True, use_reloader=True, reloader_type='stat', host='0.0.0.0', port=int(os.getenv('PORT', 5000)))