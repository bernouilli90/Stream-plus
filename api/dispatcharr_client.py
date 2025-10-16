import requests
import json
import os
from typing import Dict, List, Optional, Any

class DispatcharrClient:
    """Client to interact with the dispatcharr API"""
    
    def __init__(self, base_url: str, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize dispatcharr client with JWT authentication
        Args:
            base_url: Base URL of the dispatcharr API
            username: User for login
            password: Password for login
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.token = None
        self.refresh_token = None
        self.username = username
        self.password = password
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        if self.username and self.password:
            self.login()

    def login(self):
        """
        Authenticate and obtain JWT token using the correct endpoint
        """
        url = f"{self.base_url}/api/accounts/token/"
        data = {"username": self.username, "password": self.password}
        response = self.session.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        token = result.get('access')
        if not token:
            raise Exception(f"No JWT token received when authenticating. Response: {result}")
        self.token = token
        self.refresh_token = result.get('refresh')
        self.session.headers.update({
            'Authorization': f'Bearer {self.token}'
        })
    
    def refresh_access_token(self):
        """
        Refresh the access token using the refresh token
        """
        if not self.refresh_token:
            # If no refresh token, do a full login
            self.login()
            return
        
        url = f"{self.base_url}/api/accounts/token/refresh/"
        data = {"refresh": self.refresh_token}
        try:
            response = self.session.post(url, json=data)
            response.raise_for_status()
            result = response.json()
            token = result.get('access')
            if not token:
                # If refresh fails, do a full login
                self.login()
                return
            self.token = token
            self.session.headers.update({
                'Authorization': f'Bearer {self.token}'
            })
        except requests.RequestException:
            # If refresh fails, do a full login
            self.login()
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make an HTTP request to the API
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: Data to send in request body
            params: Query string parameters
            
        Returns:
            API response as dictionary
            
        Raises:
            requests.RequestException: If there's an error in the request
        """
        url = f"{self.base_url}{endpoint}"
        
        def make_http_request():
            """Internal function to make the actual HTTP request"""
            if method.upper() == 'GET':
                return self.session.get(url, params=params)
            elif method.upper() == 'POST':
                return self.session.post(url, json=data, params=params)
            elif method.upper() == 'PUT':
                return self.session.put(url, json=data, params=params)
            elif method.upper() == 'DELETE':
                return self.session.delete(url, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
        
        try:
            response = make_http_request()
            
            # If we get 401, try to refresh the token and retry once
            if response.status_code == 401 and self.username and self.password:
                self.refresh_access_token()
                response = make_http_request()
            
            response.raise_for_status()
            
            # Try to decode JSON, if it fails return text
            try:
                return response.json()
            except json.JSONDecodeError:
                return {'message': response.text}
                
        except requests.RequestException as e:
            raise requests.RequestException(f"Error in request to {url}: {str(e)}")
    
    def get_channels(self, search: Optional[str] = None, ordering: Optional[str] = None, page: Optional[int] = None, page_size: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all channels (with automatic pagination)
        
        Args:
            search: Optional search term
            ordering: Field to order by
            page: Specific page number (if provided, doesn't use automatic pagination)
            page_size: Page size
        
        Returns:
            List of channels
        """
        # If a page is specified, make simple request
        if page is not None:
            params = {}
            if search:
                params['search'] = search
            if ordering:
                params['ordering'] = ordering
            params['page'] = page
            if page_size:
                params['page_size'] = page_size
            result = self._make_request('GET', '/api/channels/channels/', params=params)
            # API may return direct list or paginated object
            if isinstance(result, list):
                return result
            return result.get('results', [])
        
        # Automatic pagination to get ALL channels
        all_channels = []
        current_page = 1
        params = {}
        if search:
            params['search'] = search
        if ordering:
            params['ordering'] = ordering
        if page_size:
            params['page_size'] = page_size
        else:
            params['page_size'] = 100  # Use large pages to reduce requests
        
        while True:
            params['page'] = current_page
            result = self._make_request('GET', '/api/channels/channels/', params=params)
            
            # Handle direct list or paginated response
            if isinstance(result, list):
                all_channels.extend(result)
                break  # If it returns direct list, there's no pagination
            
            channels_page = result.get('results', [])
            all_channels.extend(channels_page)
            
            # Check if there are more pages
            if not result.get('next'):
                break
            
            current_page += 1
        
        return all_channels
    
    def get_channel(self, channel_id: str) -> Dict[str, Any]:
        """
        Get information from a specific channel
        
        Args:
            channel_id: Channel ID
            
        Returns:
            Channel information
        """
        return self._make_request('GET', f'/api/channels/channels/{channel_id}/')
    
    def create_channel(self, channel_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new channel
        
        Args:
            channel_data: Channel data to create
            
        Returns:
            Created channel information
        """
        return self._make_request('POST', '/api/channels/channels/', channel_data)
    
    def update_channel(self, channel_id: str, channel_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing channel
        
        Args:
            channel_id: Channel ID
            channel_data: Updated channel data
            
        Returns:
            Updated channel information
        """
        return self._make_request('PUT', f'/api/channels/channels/{channel_id}/', channel_data)
    
    def delete_channel(self, channel_id: str) -> Dict[str, Any]:
        """
        Delete a channel
        
        Args:
            channel_id: Channel ID
            
        Returns:
            Deletion confirmation
        """
        return self._make_request('DELETE', f'/api/channels/channels/{channel_id}/')
    
    def get_streams(self, search: Optional[str] = None, ordering: Optional[str] = None, page: Optional[int] = None, page_size: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all streams (with automatic pagination)
        
        Args:
            search: Optional search term
            ordering: Field to order by
            page: Specific page number (if provided, doesn't use automatic pagination)
            page_size: Page size
            
        Returns:
            List of streams
        """
        # If a page is specified, make simple request
        if page is not None:
            params = {}
            if search:
                params['search'] = search
            if ordering:
                params['ordering'] = ordering
            params['page'] = page
            if page_size:
                params['page_size'] = page_size
            result = self._make_request('GET', '/api/channels/streams/', params=params)
            # API may return direct list or paginated object
            if isinstance(result, list):
                return result
            return result.get('results', [])
        
        # Automatic pagination to get ALL streams
        all_streams = []
        current_page = 1
        params = {}
        if search:
            params['search'] = search
        if ordering:
            params['ordering'] = ordering
        if page_size:
            params['page_size'] = page_size
        else:
            params['page_size'] = 100  # Use large pages to reduce requests
        
        while True:
            params['page'] = current_page
            result = self._make_request('GET', '/api/channels/streams/', params=params)
            
            # Handle direct list or paginated response
            if isinstance(result, list):
                all_streams.extend(result)
                break  # If it returns direct list, there's no pagination
            
            streams_page = result.get('results', [])
            all_streams.extend(streams_page)
            
            # Check if there are more pages
            if not result.get('next'):
                break
            
            current_page += 1
        
        return all_streams
    
    def get_stream(self, stream_id: int) -> Dict[str, Any]:
        """
        Get information from a specific stream
        Args:
            stream_id: Stream ID (int)
        Returns:
            Stream information
        """
        return self._make_request('GET', f'/api/channels/streams/{stream_id}/')
    
    def get_channel_streams(self, channel_id: int) -> List[Dict[str, Any]]:
        """
        Get all streams from a specific channel
        Args:
            channel_id: Channel ID (int)
        Returns:
            List of channel streams
        """
        result = self._make_request('GET', f'/api/channels/channels/{channel_id}/streams/')
        # API may return direct list or paginated object
        if isinstance(result, list):
            return result
        return result.get('results', [])
    
    def add_stream_to_channel(self, channel_id: int, stream_id: int) -> Dict[str, Any]:
        """
        Add a stream to a channel
        Args:
            channel_id: Channel ID (int)
            stream_id: Stream ID to add (int)
        Returns:
            Updated channel information
        """
        # First get current channel
        channel = self.get_channel(channel_id)
        # Get current streams
        current_streams = channel.get('streams', [])
        # Add new stream if it doesn't exist
        if stream_id not in current_streams:
            current_streams.append(stream_id)
        # Update streams in channel
        channel['streams'] = current_streams
        # Update complete channel
        return self.update_channel(channel_id, channel)
    
    def remove_stream_from_channel(self, channel_id: int, stream_id: int) -> Dict[str, Any]:
        """
        Remove a stream from a channel
        Args:
            channel_id: Channel ID (int)
            stream_id: Stream ID to remove (int)
        Returns:
            Updated channel information
        """
        # First get current channel
        channel = self.get_channel(channel_id)
        # Get current streams
        current_streams = channel.get('streams', [])
        # Remove stream if it exists
        if stream_id in current_streams:
            current_streams.remove(stream_id)
        # Update streams in channel
        channel['streams'] = current_streams
        # Update complete channel
        return self.update_channel(channel_id, channel)
    
    def create_stream(self, stream_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new stream
        Args:
            stream_data: Stream data to create
        Returns:
            Created stream information
        """
        return self._make_request('POST', '/api/channels/streams/', stream_data)
    
    def update_stream(self, stream_id: int, stream_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing stream
        Args:
            stream_id: Stream ID (int)
            stream_data: Updated stream data
        Returns:
            Updated stream information
        """
        return self._make_request('PUT', f'/api/channels/streams/{stream_id}/', stream_data)
    
    def delete_stream(self, stream_id: int) -> Dict[str, Any]:
        """
        Delete a stream
        Args:
            stream_id: Stream ID (int)
        Returns:
            Deletion confirmation
        """
        return self._make_request('DELETE', f'/api/channels/streams/{stream_id}/')
    
    def start_stream(self, stream_id: str) -> Dict[str, Any]:
        """
        Start a stream
        
        Args:
            stream_id: Stream ID
            
        Returns:
            Stream status
        """
        return self._make_request('POST', f'/api/streams/{stream_id}/start')
    
    def stop_stream(self, stream_id: str) -> Dict[str, Any]:
        """
        Stop a stream
        
        Args:
            stream_id: Stream ID
            
        Returns:
            Stream status
        """
        return self._make_request('POST', f'/api/streams/{stream_id}/stop')
    

    
    def get_stream_status(self, stream_id: str) -> Dict[str, Any]:
        """
        Get stream status
        
        Args:
            stream_id: Stream ID
            
        Returns:
            Current stream status
        """
        return self._make_request('GET', f'/api/streams/{stream_id}/status')
    
    def get_stream_logs(self, stream_id: str, lines: int = 100) -> Dict[str, Any]:
        """
        Get stream logs
        
        Args:
            stream_id: Stream ID
            lines: Number of log lines to retrieve
            
        Returns:
            Stream logs
        """
        return self._make_request('GET', f'/api/streams/{stream_id}/logs?lines={lines}')
    
    def test_connection(self) -> bool:
        """
        Test connection with dispatcharr API
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            response = self._make_request('GET', '/api/health')
            return True
        except Exception:
            return False
    
    def get_m3u_accounts(self) -> List[Dict[str, Any]]:
        """
        Get all M3U accounts
        
        Returns:
            List of M3U accounts
        """
        result = self._make_request('GET', '/api/m3u/accounts/')
        # API may return direct list or paginated object
        if isinstance(result, list):
            return result
        return result.get('results', [])
    
    def get_channel_groups(self) -> List[Dict[str, Any]]:
        """
        Get all channel groups
        
        Returns:
            List of channel groups
        """
        result = self._make_request('GET', '/api/channels/groups/')
        # API may return direct list or paginated object
        if isinstance(result, list):
            return result
        return result.get('results', [])
    
    def get_logos(self, page: Optional[int] = None, page_size: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all logos
        
        Args:
            page: Page number for pagination (if None, gets all pages)
            page_size: Number of results per page
            
        Returns:
            List of logos
        """
        if page is not None:
            # Single page request
            params = {}
            if page is not None:
                params['page'] = page
            if page_size is not None:
                params['page_size'] = page_size
                
            result = self._make_request('GET', '/api/channels/logos/', params=params)
            # API may return direct list or paginated object
            if isinstance(result, list):
                return result
            return result.get('results', [])
        else:
            # Get all pages
            all_logos = []
            current_page = 1
            default_page_size = page_size or 100
            
            while True:
                params = {'page': current_page, 'page_size': default_page_size}
                result = self._make_request('GET', '/api/channels/logos/', params=params)
                
                if isinstance(result, list):
                    logos = result
                else:
                    logos = result.get('results', [])
                
                if not logos:
                    break
                    
                all_logos.extend(logos)
                
                # Check if there are more pages
                if isinstance(result, dict) and not result.get('next'):
                    break
                    
                current_page += 1
                
            return all_logos
    
    def test_stream(self, stream_id: int, test_duration: int = None) -> Dict[str, Any]:
        """
        Test a stream using ffprobe to analyze its properties and quality.
        Uses the stream's direct URL. Updates the stream in Dispatcharr with the analyzed statistics.
        
        Args:
            stream_id: ID of the stream to test
            test_duration: How long to analyze the stream (in seconds). If None, uses STREAM_TEST_DURATION env var or default 10
            
        Returns:
            Dict with test results
            
        Environment Variables:
            STREAM_TEST_USER_AGENT: User-Agent string to use for ffmpeg/ffprobe requests (default: Chrome 132 user agent)
        """
        # Get configurable parameters from environment
        if test_duration is None:
            test_duration = int(os.getenv('STREAM_TEST_DURATION', '10'))
        
        timeout_buffer = int(os.getenv('STREAM_TEST_TIMEOUT_BUFFER', '30'))
        user_agent = os.getenv('STREAM_TEST_USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.3')
        import subprocess
        import time
        
        try:
            # Get the stream object from Dispatcharr
            stream_obj = self.get_stream(stream_id)
            stream_url = stream_obj.get('url')
            
            if not stream_url:
                return {
                    'success': False,
                    'message': f'Stream {stream_id} does not have a URL'
                }
            
            # Try to find ffprobe executable
            import os as os_module
            ffprobe_executable = 'ffprobe'

            # First, check for Docker-specific ffprobe path file
            ffprobe_path_file = os_module.path.join(
                os_module.path.dirname(os_module.path.dirname(os_module.path.abspath(__file__))),
                'tools', 'ffprobe_path.txt'
            )
            
            # Check for local installations (development environment)
            local_ffprobe = os_module.path.join(
                os_module.path.dirname(os_module.path.dirname(os_module.path.abspath(__file__))),
                'tools', 'ffmpeg', 'ffmpeg-7.1-essentials_build', 'bin', 'ffprobe.exe'
            )
            local_ffmpeg = os_module.path.join(
                os_module.path.dirname(os_module.path.dirname(os_module.path.abspath(__file__))),
                'tools', 'ffmpeg', 'ffmpeg-7.1-essentials_build', 'bin', 'ffmpeg.exe'
            )

            if os_module.path.exists(ffprobe_path_file):
                try:
                    with open(ffprobe_path_file, 'r') as f:
                        docker_ffprobe_path = f.read().strip()
                        if os_module.path.exists(docker_ffprobe_path):
                            ffprobe_executable = docker_ffprobe_path
                            print(f"Using Docker ffprobe: {docker_ffprobe_path}")
                        else:
                            print(f"Docker ffprobe path {docker_ffprobe_path} does not exist, using system ffprobe")
                except Exception as e:
                    print(f"Error reading ffprobe path file: {e}, using system ffprobe")
            else:
                if os_module.path.exists(local_ffprobe):
                    ffprobe_executable = local_ffprobe
                    print(f"Using local ffprobe: {local_ffprobe}")
                else:
                    print(f"Local ffprobe not found at {local_ffprobe}, using system ffprobe")

            if os_module.path.exists(local_ffmpeg):
                ffmpeg_executable = local_ffmpeg
                print(f"Using local ffmpeg: {local_ffmpeg}")
            else:
                ffmpeg_executable = 'ffmpeg'
                print("Local ffmpeg not found, using system ffmpeg")

            # Verify executables exist and are executable
            import shutil
            if not shutil.which(ffprobe_executable):
                return {
                    'success': False,
                    'message': f'ffprobe executable not found: {ffprobe_executable}'
                }
            if not shutil.which(ffmpeg_executable):
                return {
                    'success': False,
                    'message': f'ffmpeg executable not found: {ffmpeg_executable}'
                }
            
            # Step 1: Use ffmpeg to read the stream and get bitrate info
            # We'll run it for the specified duration and capture the output
            print(f"Reading stream for {test_duration} seconds to calculate bitrate...")

            ffmpeg_cmd = [
                ffmpeg_executable,
                '-user_agent', user_agent,
                '-t', str(test_duration),  # Read for test_duration seconds
                '-i', stream_url,
                '-c', 'copy',  # Copy without re-encoding
                '-f', 'null',  # Discard output
                '-'
            ]

            # Print command with proper quoting for readability
            quoted_cmd = []
            for arg in ffmpeg_cmd:
                if ' ' in arg or '(' in arg or ')' in arg:
                    quoted_cmd.append(f'"{arg}"')
                else:
                    quoted_cmd.append(arg)
            print(f"FFmpeg command: {' '.join(quoted_cmd)}")

            ffmpeg_result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                timeout=test_duration + timeout_buffer
            )

            # Parse bitrate from ffmpeg stderr output
            # Look for output size line like: "video:5607KiB audio:125KiB"
            calculated_bitrate = None
            calculated_bitrate_kbps = None

            for line in ffmpeg_result.stderr.split('\n'):
                # Look for the final summary line with data sizes
                if 'video:' in line and 'audio:' in line and ('KiB' in line or 'kB' in line):
                    try:
                        # Extract video and audio sizes
                        video_size_kb = 0
                        audio_size_kb = 0

                        # Parse video size
                        if 'video:' in line:
                            # Handle both KiB and kB formats
                            if 'KiB' in line:
                                video_part = line.split('video:')[1].split('KiB')[0].strip()
                            elif 'kB' in line:
                                video_part = line.split('video:')[1].split('kB')[0].strip()
                            else:
                                video_part = None
                            
                            if video_part:
                                video_size_kb = float(video_part)

                        # Parse audio size
                        if 'audio:' in line:
                            # Handle both KiB and kB formats
                            if 'KiB' in line:
                                audio_part = line.split('audio:')[1].split('KiB')[0].strip()
                            elif 'kB' in line:
                                audio_part = line.split('audio:')[1].split('kB')[0].strip()
                            else:
                                audio_part = None
                            
                            if audio_part:
                                audio_size_kb = float(audio_part)

                        # Calculate total bitrate: (total_KB * 8) / duration_seconds = kbits/s
                        total_size_kb = video_size_kb + audio_size_kb
                        calculated_bitrate_kbps = (total_size_kb * 8) / test_duration
                        calculated_bitrate = calculated_bitrate_kbps * 1000  # Convert to bits/s

                    except (ValueError, IndexError) as e:
                        print(f"Error parsing data sizes from line '{line}': {e}")
                        pass

            # Fallback: try to parse from progress line
            if not calculated_bitrate:
                for line in ffmpeg_result.stderr.split('\n'):
                    if 'bitrate=' in line and 'kbits/s' in line:
                        try:
                            bitrate_part = line.split('bitrate=')[1].split('kbits/s')[0].strip()
                            if bitrate_part and bitrate_part != 'N/A':
                                calculated_bitrate_kbps = float(bitrate_part)
                                calculated_bitrate = calculated_bitrate_kbps * 1000
                        except (ValueError, IndexError):
                            pass
            
            # Step 2: Use ffprobe to get codec information
            print(f"Analyzing stream metadata with ffprobe...")

            ffprobe_cmd = [
                ffprobe_executable,
                '-user_agent', user_agent,
                '-analyzeduration', str(test_duration * 2000000),  # Increased for Docker (2x)
                '-probesize', str(test_duration * 10000000),  # Increased for Docker (2x)
                '-v', 'error',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                stream_url
            ]

            # Print command with proper quoting for readability
            quoted_cmd = []
            for arg in ffprobe_cmd:
                if ' ' in arg or '(' in arg or ')' in arg:
                    quoted_cmd.append(f'"{arg}"')
                else:
                    quoted_cmd.append(arg)
            print(f"FFprobe command: {' '.join(quoted_cmd)}")

            # Run ffprobe
            result = subprocess.run(
                ffprobe_cmd,
                capture_output=True,
                text=True,
                timeout=test_duration + timeout_buffer
            )

            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else "Unknown error"
                return {
                    'success': False,
                    'message': f'ffprobe failed: {error_msg}',
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            
            # Parse ffprobe output
            import json as json_lib
            probe_data = json_lib.loads(result.stdout)
            
            # Second fallback: try to get bitrate from format bitrate in ffprobe
            if not calculated_bitrate_kbps:
                format_bitrate = probe_data.get('format', {}).get('bit_rate')
                if format_bitrate:
                    try:
                        calculated_bitrate_kbps = float(format_bitrate) / 1000.0  # Convert from bps to kbps
                        calculated_bitrate = float(format_bitrate)
                    except (ValueError, TypeError) as e:
                        pass
                else:
                    print("No bitrate available from ffprobe format either")
            
            # Extract video and audio stream info
            video_stream = None
            audio_stream = None
            
            for stream in probe_data.get('streams', []):
                if stream.get('codec_type') == 'video' and not video_stream:
                    video_stream = stream
                elif stream.get('codec_type') == 'audio' and not audio_stream:
                    audio_stream = stream
            
            # Build statistics object using Dispatcharr's original format
            # Based on stream 556 format (10 fields)
            stats = {}
            
            # Video fields
            if video_stream:
                width = video_stream.get('width')
                height = video_stream.get('height')
                if width and height:
                    stats['resolution'] = f"{width}x{height}"
                
                # Convert fps fraction (e.g., "25/1") to float
                fps_str = video_stream.get('avg_frame_rate', '0/1')
                try:
                    numerator, denominator = fps_str.split('/')
                    stats['source_fps'] = float(numerator) / float(denominator)
                except (ValueError, ZeroDivisionError):
                    stats['source_fps'] = 0.0
                
                stats['video_codec'] = video_stream.get('codec_name')
                stats['pixel_format'] = video_stream.get('pix_fmt')
            
            # Audio fields
            if audio_stream:
                stats['audio_codec'] = audio_stream.get('codec_name')
                
                # Sample rate as integer
                sample_rate = audio_stream.get('sample_rate')
                if sample_rate:
                    stats['sample_rate'] = int(sample_rate)
                
                # Audio bitrate in kbps (from bps)
                audio_bitrate_bps = audio_stream.get('bit_rate')
                if audio_bitrate_bps:
                    stats['audio_bitrate'] = float(audio_bitrate_bps) / 1000.0
                
                # Audio channels as string: "stereo" or "mono"
                channels = audio_stream.get('channels')
                if channels:
                    stats['audio_channels'] = 'stereo' if int(channels) == 2 else 'mono'
            
            # Stream type (format name)
            format_name = probe_data.get('format', {}).get('format_name')
            if format_name:
                stats['stream_type'] = format_name
            
            # Output bitrate - the KEY field for sorting
            # Save with both names for compatibility
            if calculated_bitrate_kbps:
                stats['output_bitrate'] = calculated_bitrate_kbps  # Dispatcharr native field
                stats['ffmpeg_output_bitrate'] = calculated_bitrate_kbps  # Legacy field
                print(f"Final calculated bitrate: {calculated_bitrate_kbps} kbps")
            else:
                print("Warning: No bitrate could be calculated from ffmpeg output")

            print(f"Collected statistics: {stats}")

            # Update the stream object with the new statistics
            stream_obj['stream_stats'] = stats

            # Update the stats timestamp to current UTC time
            from datetime import datetime, timezone
            stream_obj['stream_stats_updated_at'] = datetime.now(timezone.utc).isoformat()

            print(f"Attempting to save statistics to Dispatcharr for stream {stream_id}...")

            # Save the updated stream back to Dispatcharr
            try:
                updated_stream = self.update_stream(stream_id, stream_obj)

                print(f"Successfully saved statistics to Dispatcharr for stream {stream_id}")
                return {
                    'success': True,
                    'message': f'Stream {stream_id} analyzed successfully and statistics saved to Dispatcharr',
                    'stream_id': stream_id,
                    'stream_url': stream_url,
                    'statistics': stats,
                    'raw_probe_data': probe_data,
                    'updated_stream': updated_stream
                }
            except Exception as e:
                # Even if we can't save, return the statistics
                print(f"Failed to save statistics to Dispatcharr: {str(e)}")
                return {
                    'success': True,
                    'message': f'Stream {stream_id} analyzed successfully but failed to save to Dispatcharr: {str(e)}',
                    'stream_id': stream_id,
                    'stream_url': stream_url,
                    'statistics': stats,
                    'raw_probe_data': probe_data,
                    'save_error': str(e)
                }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'message': f'ffprobe timeout after {test_duration} seconds'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error testing stream {stream_id}: {str(e)}'
            }