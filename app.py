from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import os
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
                description=data.get('description')
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
                description=data.get('description')
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


@app.route('/api/sorting-rules/<int:rule_id>/execute', methods=['POST'])
def execute_sorting_rule(rule_id):
    """API endpoint to execute a sorting rule on specific channel(s)"""
    try:
        data = request.get_json() or {}
        channel_id = data.get('channel_id')
        
        if not channel_id:
            return jsonify({'error': 'channel_id is required'}), 400
        
        # Get the rule
        rule = sorting_rules_manager.get_rule(rule_id)
        if not rule:
            return jsonify({'error': 'Rule not found'}), 404
        
        if not rule.enabled:
            return jsonify({'error': 'Rule is disabled'}), 400
        
        # Comprobar que el canal existe
        try:
            channel = dispatcharr_client.get_channel(channel_id)
            if not channel:
                return jsonify({'error': 'Channel not found'}), 404
        except Exception as e:
            # Si el canal no existe, Dispatcharr devuelve 404
            if '404' in str(e):
                return jsonify({'error': f'Channel {channel_id} not found'}), 404
            raise  # Re-lanzar si es otro tipo de error

        # Obtener streams del canal
        streams = dispatcharr_client.get_channel_streams(channel_id)
        if not streams:
            return jsonify({
                'success': True,
                'message': 'No streams to sort',
                'sorted_count': 0
            })

        # Ordenar streams usando la regla
        sorted_streams = StreamSorter.sort_streams(rule, streams)

        # Actualizar canal con el nuevo orden
        sorted_stream_ids = [s['id'] for s in sorted_streams]
        channel['streams'] = sorted_stream_ids

        # Guardar canal actualizado
        dispatcharr_client.update_channel(channel_id, channel)

        return jsonify({
            'success': True,
            'message': f'Successfully sorted {len(sorted_streams)} streams',
            'sorted_count': len(sorted_streams),
            'channel_id': channel_id
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
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))