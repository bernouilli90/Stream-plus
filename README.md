# Stream Plus - Web Manager for Dispatcharr

Stream Plus is a web application developed in Python with Flask that provides a modern and easy-to-use interface for managing Dispatcharr channels and streams.

## Features

- 🎯 **Channel Management**: Create, edit, delete and monitor channels
- 🎬 **Stream Control**: Start, stop and configure streams
- 📊 **Dashboard**: Overview of channel and stream status
- 🔄 **Real Time**: Automatic status updates
- 📱 **Responsive**: Mobile-optimized interface
- 🔍 **Search and Filters**: Quickly find channels and streams
- 📋 **Logs**: Real-time stream log visualization
- 🎨 **Modern Interface**: Clean design with Bootstrap 5
- 🤖 **Auto-Assignment**: Intelligent automatic stream assignment to channels
- 🏆 **Stream Sorter**: Score-based stream ordering system with custom rules

## Requirements

- Python 3.8 or higher
- Dispatcharr API available and configured

## Installation

1. **Clone or download the project**
   ```bash
   git clone <repository-url>
   cd Stream-plus
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   # Copy the example file
   copy .env.example .env
   
   # Edit .env with your settings
   notepad .env
   ```

5. **Set up variables in .env**
   ```env
   FLASK_DEBUG=True
   SECRET_KEY=your-very-secure-secret-key
   DISPATCHARR_API_URL=http://your-dispatcharr-server:port
   DISPATCHARR_API_KEY=your-dispatcharr-api-key
   ```

## Dispatcharr Configuration

Before using Stream Plus, make sure your Dispatcharr instance is:

1. **Running and accessible** at the configured URL
2. **API enabled** with the configured key
3. **Proper permissions** to create, modify and delete channels/streams

### Dispatcharr configuration example

```yaml
# dispatcharr.yml
api:
  enabled: true
  port: 8080
  api_key: "your-api-key-here"
  
server:
  host: "0.0.0.0"
  port: 8080
```

## Usage

1. **Start the application**
   ```bash
   python app.py
   ```

2. **Access the application**
   Open in browser: `http://localhost:5000`

3. **Verify connection**
   - Click "Test API" in the navigation bar
   - Verify "Connected to Dispatcharr" appears

## Project Structure

```
Stream-plus/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env.example          # Configuration example
├── api/
│   ├── __init__.py       # API module
│   └── dispatcharr_client.py  # Dispatcharr API client
├── templates/            # HTML templates
│   ├── base.html        # Base template
│   ├── index.html       # Main page
│   ├── channels.html    # Channel management
│   └── streams.html     # Stream management
└── static/              # Static files
    ├── css/
    │   └── style.css    # Custom styles
    └── js/
        └── app.js       # Application JavaScript
```

## API Endpoints

### Channels
- `GET /api/channels` - Get all channels
- `GET /api/channels/<id>` - Get specific channel
- `POST /api/channels` - Create new channel
- `PUT /api/channels/<id>` - Update channel
- `DELETE /api/channels/<id>` - Delete channel

### Streams
- `GET /api/streams` - Get all streams
- `GET /api/streams/<id>` - Get specific stream
- `POST /api/streams` - Create new stream
- `PUT /api/streams/<id>` - Update stream
- `DELETE /api/streams/<id>` - Delete stream
- `POST /api/streams/<id>/start` - Start stream
- `POST /api/streams/<id>/stop` - Stop stream

## Advanced Features

### Stream Sorter
The Stream Sorter allows you to create intelligent sorting rules that score and reorder streams within a channel based on quality metrics.

#### Key Features
- **Multi-condition Scoring**: Each rule can have multiple scoring conditions
- **Flexible Targeting**: Apply rules to specific channels or channel groups
- **Preview Mode**: Test rules before applying them
- **Weighted Scoring**: Assign different point values to each condition

#### Scoring Parameters
1. **M3U Source**: Match streams from specific M3U accounts
2. **Video Bitrate**: Score based on bitrate thresholds (>, >=, <, <=, ==)
3. **Video Resolution**: Score based on resolution (e.g., 1920x1080)
4. **Video Codec**: Score specific codecs (h264, h265, av1, etc.)
5. **Audio Codec**: Score audio formats (aac, ac3, eac3, etc.)
6. **Video FPS**: Score based on frame rate

#### Usage Example
Create a rule to prioritize high-quality streams:
```
Rule: "High Quality Preference"
Conditions:
  - Video Bitrate >= 5000 → 10 points
  - Video Resolution >= 1920 → 15 points
  - Video Codec == "h265" → 8 points
  - Audio Codec == "eac3" → 5 points
  - Video FPS >= 50 → 7 points

Max Score: 45 points
```

Streams matching more conditions will score higher and appear first in the channel.

#### API Endpoints
- `GET/POST /api/sorting-rules` - List/create sorting rules
- `GET/PUT/DELETE /api/sorting-rules/<id>` - Manage specific rule
- `POST /api/sorting-rules/<id>/preview` - Preview sorting results
- `POST /api/sorting-rules/<id>/execute` - Apply sorting to channel
- `POST /api/sorting-rules/<id>/toggle` - Enable/disable rule

### Auto-Assignment
Automatically assign streams to channels based on customizable rules.

### Auto-refresh
The application automatically updates data every 30 seconds when the page is visible.

### Keyboard Shortcuts
- `Ctrl+R`: Refresh data
- `Ctrl+E`: Export data
- `Escape`: Close modals

### Notifications
Real-time notification system to inform about operation status.

### Responsive Design
The interface automatically adapts to mobile devices and tablets.

## Development

### Development Structure
```bash
# Install development dependencies
pip install flask-testing pytest

# Run tests
pytest

# Run in development mode
export FLASK_DEBUG=1
python app.py
```

### Customization

#### Add new endpoints
1. Edit `app.py` to add routes
2. Update `dispatcharr_client.py` if you need new API functions
3. Create/modify templates as needed

#### Modify styles
- Edit `static/css/style.css` for style changes
- Main colors are defined as CSS variables in `:root`

#### Add JavaScript functionality
- Edit `static/js/app.js`
- Use the `StreamPlus` object for global functions

## Production Deployment

### Production Configuration
```env
FLASK_DEBUG=False
SECRET_KEY=super-secret-production-key
DISPATCHARR_API_URL=https://your-dispatcharr.com
DISPATCHARR_API_KEY=production-api-key
```

### With Docker (Optional)
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "app.py"]
```

### With Nginx + Gunicorn
```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Troubleshooting

### Connection error with Dispatcharr
1. Verify that Dispatcharr is running
2. Check URL and port in `.env`
3. Verify API key
4. Check firewall/network permissions

### Permission errors
1. Verify user has permissions in Dispatcharr
2. Check CORS configuration if necessary

### Performance issues
1. Adjust auto-refresh interval in `app.js`
2. Implement pagination for large amounts of data
3. Use Redis for caching (future implementation)

## Contributing

1. Fork the repository
2. Create branch for new features
3. Commit changes
4. Push to branch
5. Create Pull Request

## License

This project is under the MIT license. See LICENSE file for more details.

## Support

To report bugs or request features:
1. Create an issue on GitHub
2. Include relevant logs
3. Describe steps to reproduce the problem

## Changelog

### v1.0.0
- Basic channel and stream management
- Responsive web interface
- Complete REST API
- Notification system
- Auto-refresh
- Log visualization