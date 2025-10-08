# Stream Plus

Web application for managing Dispatcharr channels and streams with intelligent auto-assignment and stream sorting capabilities.

## Features

- 🎯 **Channel & Stream Management**: Complete CRUD operations via web interface
- 🤖 **Auto-Assignment Rules**: Automatically assign streams to channels based on quality criteria
- 🏆 **Stream Sorter**: Score-based stream ordering with multi-condition rules
- 📊 **Real-time Dashboard**: Monitor channel and stream status
- 🎨 **Modern UI**: Responsive Bootstrap 5 interface

## Quick Start (Docker)

```bash
# 1. Build image
./docker-build.sh

# 2. Configure Dispatcharr credentials in docker-compose.yml
nano docker-compose.yml

# 3. Start container
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

## Helper Script

Use `docker-helper.sh` for common operations:

```bash
./docker-helper.sh start       # Start container
./docker-helper.sh stop        # Stop container
./docker-helper.sh logs        # View logs
./docker-helper.sh exec-all    # Execute all rules
./docker-helper.sh exec-assign # Execute assignment rules
./docker-helper.sh exec-sort   # Execute sorting rules
./docker-helper.sh rules       # View configured rules
./docker-helper.sh health      # Check container health
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

### Network Configuration

**Dispatcharr in Docker:**
```yaml
environment:
  - DISPATCHARR_API_URL=http://dispatcharr:8080
networks:
  - dispatcharr-network
```

**Dispatcharr on Host:**
```yaml
environment:
  - DISPATCHARR_API_URL=http://192.168.1.100:8080
```

## API Endpoints

### Channels
- `GET/POST /api/channels` - List/create channels
- `GET/PUT/DELETE /api/channels/<id>` - Manage channel

### Streams
- `GET/POST /api/streams` - List/create streams
- `GET/PUT/DELETE /api/streams/<id>` - Manage stream
- `POST /api/streams/<id>/start` - Start stream
- `POST /api/streams/<id>/stop` - Stop stream

### Auto-Assignment Rules
- `GET/POST /api/auto-assignment-rules` - List/create rules
- `GET/PUT/DELETE /api/auto-assignment-rules/<id>` - Manage rule
- `POST /api/auto-assignment-rules/<id>/execute` - Execute rule

### Sorting Rules
- `GET/POST /api/sorting-rules` - List/create rules
- `GET/PUT/DELETE /api/sorting-rules/<id>` - Manage rule
- `POST /api/sorting-rules/<id>/preview` - Preview sorting
- `POST /api/sorting-rules/<id>/execute` - Apply sorting

## Troubleshooting

### Container fails to start
```bash
docker logs stream-plus
docker exec stream-plus env | grep DISPATCHARR
```

### Cannot connect to Dispatcharr
```bash
docker exec stream-plus wget -O- http://dispatcharr:8080
```

### Permission errors on ./rules
```bash
sudo chown -R 1000:1000 ./rules
```

### Rules not executing
```bash
# Verify JSON syntax
cat ./rules/auto_assignment_rules.json | jq .

# Test manually with verbose output
docker exec stream-plus python execute_rules.py --all --verbose
```

## Requirements

- Python 3.8+
- Dispatcharr API
- FFmpeg (for stream testing)
- Docker (for containerized deployment)

## License

MIT License

## Contributing

1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request