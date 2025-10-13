# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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