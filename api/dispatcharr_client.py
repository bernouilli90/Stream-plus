import requests
import json
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
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, params=params)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, params=params)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
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