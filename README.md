# Stream Plus

Web application for managing Dispatcharr channels and streams with intelligent auto-assignment and stream sorting capabilities.

## Features

- 🎯 **Channel & Stream Management**: Complete CRUD operations via web interface
- 🤖 **Auto-Assignment Rules**: Automatically assign streams to channels based on quality criteria
- 🏆 **Stream Sorter**: Score-based stream ordering with multi-condition rules
- 🎨 **Modern UI**: Responsive Bootstrap 5 interface

## Screenshots

### Auto-Assignment Rule Creation Form
![Auto-Assignment Rule Creation](1.png)

### Auto-Assignment Rules View
![Auto-Assignment Rules](2.png)

### Executing Auto-Assignment Rule
![Executing Auto-Assignment](3.png)

### Stream Sorting Rule Form
![Stream Sorting Rule Form](4.png)

### Stream Sorting Rules View
![Stream Sorting Rules](5.png)

### Stream Sorting Rule Preview
![Stream Sorting Preview](6.png)

### Executing Stream Sorting Rule
![Executing Stream Sorting](7.png)

### Result in Dispatcharr
![Dispatcharr Result](8.png)

## Quick Start (Docker)

### Production (Recommended)

```bash
# 1. Clone repository
git clone https://github.com/bernouilli90/Stream-plus.git
cd Stream-plus

# 2. Configure Dispatcharr credentials in docker-compose.yml
nano docker-compose.yml

# 3. Start container
docker-compose up -d

# Access at http://localhost:5000
```

### Development

```bash
# 1. Clone repository
git clone https://github.com/bernouilli90/Stream-plus.git
cd Stream-plus

# 2. Configure Dispatcharr credentials in docker-compose.dev.yml
nano docker-compose.dev.yml

# 3. Build and start container
docker-compose -f docker-compose.dev.yml up -d

# Access at http://localhost:5000
```

### Manual Build

```bash
# 1. Clone repository
git clone https://github.com/bernouilli90/Stream-plus.git
cd Stream-plus

# 2. Build image manually
./docker-build.sh

# 3. Configure Dispatcharr credentials in docker-compose.yml
nano docker-compose.yml

# 4. Start container
docker-compose up -d

# Access at http://localhost:5000
```

## Manual Installation

```bash
# Clone repository
git clone https://github.com/bernouilli90/Stream-plus.git
cd Stream-plus

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Set DISPATCHARR_API_URL, DISPATCHARR_API_USER, DISPATCHARR_API_PASSWORD

# Run application
python app.py
```

## Configuration

### Required Environment Variables

```env
DISPATCHARR_API_URL=http://dispatcharr:8080
DISPATCHARR_API_USER=admin
DISPATCHARR_API_PASSWORD=yourpassword
```

### Optional Variables

```env
PORT=5000
FLASK_DEBUG=False
SECRET_KEY=your-secret-key
TZ=UTC
```

## Docker Images

### Official Images

Pre-built Docker images are available on Docker Hub:

- **Production**: `bernouilli/stream-plus:latest` - Latest stable release
- **Development**: Build from source using `docker-compose.dev.yml`

### Image Features

- **Alpine Linux** base for minimal size
- **FFmpeg & FFprobe** included for stream analysis
- **Non-root user** (UID/GID 1000) for security
- **Health checks** for container monitoring
- **Timezone support** via TZ environment variable

### Docker Compose Files

- **`docker-compose.yml`**: Uses pre-built image from Docker Hub (recommended for production)
- **`docker-compose.dev.yml`**: Builds image from source (recommended for development)

## Auto-Assignment Rules

Create rules to automatically assign streams to channels based on criteria:

- **Stream name patterns**: Match by name/regex
- **Video resolution**: 1080p, 720p, SD, etc.
- **Video codec**: h264, h265, av1
- **Audio codec**: aac, ac3, eac3
- **Video FPS**: Frame rate matching
- **Bitrate**: Quality thresholds

**Example rule:**
```json
{
  "name": "HD Streams",
  "enabled": true,
  "channel_id": 123,
  "conditions": {
    "video_resolution": ["1080p", "720p"],
    "video_codec": ["h265", "h264"]
  }
}
```

## Stream Sorting

Score and reorder streams within channels based on quality metrics:

**Scoring Conditions:**
- M3U Source account
- Video bitrate (>, >=, <, <=, ==)
- Video resolution
- Video codec
- Audio codec
- Video FPS

**Example:**
```
Rule: "Best Quality First"
Conditions:
  - Video Bitrate >= 5000 → 10 points
  - Resolution >= 1920 → 15 points
  - Codec == "h265" → 8 points
```

Streams are reordered by total score (highest first).

## CLI Rule Execution

Execute rules from command line or cron:

```bash
# Execute all rules
docker exec stream-plus python execute_rules.py --all

# Assignment rules only
docker exec stream-plus python execute_rules.py --assignment

# Sorting rules only
docker exec stream-plus python execute_rules.py --sorting

# Specific rule by ID
docker exec stream-plus python execute_rules.py --all --rule-ids 2 --verbose
```

### Automation with Cron

```bash
# Execute all rules every hour
0 * * * * docker exec stream-plus python execute_rules.py --all >> /var/log/stream-plus.log 2>&1
```

## Docker Deployment

### Build with Custom UID/GID

```bash
docker build \
  --build-arg USER_UID=$(id -u) \
  --build-arg USER_GID=$(id -g) \
  -t stream-plus:latest .
```

### Data Persistence

Rule files persist in `./rules/` directory:
- `auto_assignment_rules.json` - Assignment rules
- `sorting_rules.json` - Sorting rules

Files are auto-created with empty structure if missing.