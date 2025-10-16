# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.6] - 2025-10-16

### Added
- **Stream Testing User-Agent**: Added configurable user-agent for ffmpeg/ffprobe stream testing
  - Default user-agent: Chrome 132.0.0.0 Windows
  - Environment variable: `STREAM_TEST_USER_AGENT`
  - Prevents stream provider detection by mimicking browser requests

### Configuration
Add to your `.env` file:
```bash
STREAM_TEST_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.3
```

## [0.2.5] - 2025-10-15

### Added
- **Manual Stream Inclusion/Exclusion**: New feature allowing users to force-include or force-exclude specific streams in auto-assignment rules
  - Force Include: Streams added to channel regardless of rule conditions
  - Force Exclude: Streams excluded from channel even if they match all conditions
  - UI components: Search and select streams with visual badges in rule cards and modals
  - Logic improvements: Forced includes/excludes applied during both testing and evaluation phases

### Fixed
- **Sorting rules M3U source evaluation**: Fixed sorting rules with `m3u_source` conditions not being evaluated because streams lacked M3U account information
- **Consistent filtering logic**: Ensured all execution paths (CLI, web interface, background) use the same stream filtering logic

### Configuration
Manual stream overrides can be configured through the web interface or API:
```json
{
  "force_include_stream_ids": [1620],
  "force_exclude_stream_ids": [2314, 2313]
}
```

## [0.2.4] - 2025-10-15

### Fixed

- **Stream enrichment for sorting**: Added M3U account information enrichment to streams before sorting evaluation
- **Consistent M3U data**: Ensured all sorting execution paths (CLI, web interface, background) have access to M3U account data for condition evaluation

### Technical Details
- Updated `execute_sorting_rules()` in `execute_rules.py` to check `rule.channel_group_ids` before defaulting to all channels
- Added group-to-channel resolution logic using `groups_manager.groups[group_id].channel_ids`
- Improved CLI output to show which groups are being processed and how many channels they contain
- Maintains backwards compatibility with existing `all_channels` and `channel_ids` configurations

## [0.2.3] - 2025-10-14

### Fixed
- **Docker user permissions**: Fixed UID/GID change functionality to work properly with runtime environment variables
- **File ownership**: Fixed ownership of automatically created rule files to match configured user instead of root

## [0.2.1] - 2025-10-13

### Fixed
- **Docker healthcheck**: Fixed failing healthcheck by replacing wget with curl and adding curl to Dockerfile

### Technical Details
- Added curl to Alpine Linux system dependencies
- Changed healthcheck command from wget to curl in Dockerfile and docker-compose files
- Healthcheck now properly verifies Flask application is running

## [0.2.0] - 2025-10-13

### Added
- **STREAM_TEST_DELAY parameter**: New environment variable to control delay between consecutive stream tests, preventing provider detection of multiple simultaneous streams
- **Channel filter**: Search and filter auto-assignment rules by channel name in real-time
- **Rule name filter**: Search and filter auto-assignment rules by rule name in real-time
- **Compact rule cards**: Redesigned rule cards with better space utilization and responsive grid layout
- **Channel logos**: Display channel logos prominently in rule cards with fallback icons
- **Bulk rule creation improvements**: Enhanced bulk creation modal with better user feedback

### Changed
- **UI Improvements**: Complete redesign of auto-assignment interface with modern card-based layout
- **Dropdown menus**: Fixed dropdown positioning and added dropup behavior to prevent overflow
- **Bulk creation logic**: Fixed success message display and automatic page reload after bulk operations
- **Environment configuration**: Updated .env.example and docker-compose.yml with new STREAM_TEST_DELAY parameter

### Fixed
- **Search filter functionality**: Fixed critical JavaScript errors and template syntax issues in auto-assignment rules page
- **Bulk rule creation**: Resolved issue where successful bulk operations showed error messages
- **Dropdown overflow**: Fixed dropdown menus being cut off by adjacent cards
- **Version display**: Improved version visibility in footer with better contrast
- **Template block structure**: Corrected Jinja2 template syntax and JavaScript variable scoping
- **Docker healthcheck**: Fixed failing healthcheck by replacing wget with curl and adding curl to Dockerfile

### Technical Details
- Added `STREAM_TEST_DELAY` environment variable (default: 3 seconds)
- Implemented delay logic in stream testing loops to avoid provider detection
- Redesigned auto-assign template with responsive Bootstrap grid
- Added JavaScript filtering functionality for rule cards with real-time search
- Fixed dropdown positioning with CSS z-index and boundary management
- Corrected template syntax errors and JavaScript DOM manipulation issues

### Configuration
Add to your `.env` file:
```bash
STREAM_TEST_DELAY=3
```

Or in `docker-compose.yml`:
```yaml
environment:
  - STREAM_TEST_DELAY=3
```

## [0.1.0] - 2025-10-01

### Added
- Initial release of Stream Plus
- Auto-assignment rules for automatic stream assignment
- Stream sorting functionality
- Docker support with docker-compose
- REST API for rule management
- Web interface for rule configuration
- Integration with Dispatcharr API
- Bulk operations for rule management

### Features
- Channel-based auto-assignment rules
- Regex pattern matching for streams
- M3U account filtering
- Video/audio codec conditions
- Resolution and FPS filtering
- Stream testing before assignment
- Progress tracking for long operations
- Rule execution and preview functionality</content>
<parameter name="filePath">c:\Users\josea\Desktop\Stream-plus\Stream-plus\CHANGELOG.md