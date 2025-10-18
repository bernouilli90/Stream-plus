# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.9] - 2025-10-18

### Added
- **Score Breakdown Tooltips in Stream Sorter Preview**: Enhanced preview modal with detailed score information
  - Hover over score badges to see which conditions contributed to the total score
  - Tooltips show individual condition matches with points earned
  - Only displays on hover for clean UI without clutter
  - Bootstrap tooltips with proper HTML formatting and positioning
  - Real-time tooltip initialization after preview data loads

### Enhanced
- **Stream Scoring Engine**: Modified scoring system to track condition-by-condition contributions
  - `StreamSorter.score_stream()` now returns detailed breakdown alongside total score
  - Maintains backward compatibility with existing sorting functionality
  - Enables future enhancements for score analysis and debugging

### Fixed
- **Stream Testing Logic**: Fixed critical issue where streams with existing stats were not re-tested
  - When `test_streams_before_sorting=True`, ALL candidate streams are now tested regardless of existing stats
  - Previously, only streams without stats or with forced retest were tested, leaving stale stats for streams that should be re-evaluated
  - **Stream stats are now properly cleared** when testing fails, ensuring no stale data remains in Dispatcharr
  - Rules requiring stats (resolution, bitrate, etc.) now work correctly with fresh stream analysis
  - Improved reliability of auto-assignment rules with stream testing enabled

### Enhanced
- **FFprobe Stream Selection**: Primary ffprobe command now focuses on first video stream
  - Added `-select_streams v:0` to VLC-style ffprobe command for better compatibility
  - Improves stream analysis success rate for complex multi-stream sources
  - Maintains JSON output format for consistent data parsing

## [0.2.7] - 2025-10-18

### Added
- **CLI M3U Refresh Integration**: M3U sources are now automatically refreshed before executing rules via CLI
  - Auto-assignment rules (`execute_rules.py --assignment`) now refresh M3U sources first
  - Sorting rules (`execute_rules.py --sorting`) now refresh M3U sources first
  - Ensures rules execute against the most current stream data
  - Graceful error handling: rules execute even if M3U refresh fails
- **M3U Refresh Timestamp Persistence**: CLI rule execution now saves M3U refresh timestamps
  - Timestamp stored in `m3u_refresh_state.json` after successful refresh
  - UTC timezone format for consistent storage
  - Web UI displays accurate "Last M3U Refresh" times from CLI operations
  - Same timestamp logic used across web interface and CLI execution

### Enhanced
- **Rule Execution Workflow**: Improved CLI rule execution with integrated M3U refresh
  - Clear console output showing refresh status before rule processing
  - Timestamp updates only on successful M3U refresh operations
  - Maintains backward compatibility with existing rule execution behavior
- **FFprobe Stream Testing**: Improved stream compatibility with VLC-style ffprobe command
  - Primary command now uses VLC-style format for better stream compatibility
  - JSON format command available as fallback for detailed stream analysis
  - Enhanced error handling with dual command approach
  - Better success rate for streams with user-agent restrictions

### Fixed
- **FFprobe User-Agent Consistency**: Alternative VLC-style ffprobe command now uses the same user-agent as primary command
  - Ensures consistent user-agent behavior between primary and fallback ffprobe commands
  - Removes hardcoded VLC user-agent from alternative command
  - Improves stream testing reliability for user-agent sensitive streams

## [0.2.6] - 2025-10-16

### Added
- **Stream Testing User-Agent**: Added configurable user-agent for ffmpeg/ffprobe stream testing
  - Default user-agent: Chrome 132.0.0.0 Windows
  - Environment variable: `STREAM_TEST_USER_AGENT`
  - Prevents stream provider detection by mimicking browser requests
- **Enhanced Stream Testing Logging**: Added detailed command logging for ffmpeg and ffprobe operations
  - FFmpeg command logged before bitrate calculation
  - FFprobe command logged before metadata analysis
  - Full command strings with all parameters including user-agent
  - Improved readability with proper argument quoting
- **Dynamic Channel Groups Loading**: Channel groups are now reloaded on each page access
  - Groups refresh when accessing index, auto-assign, and stream-sorter pages
  - Ensures UI reflects real-time changes to channel groups
  - Prevents stale group data during application runtime
- **Dispatcharr Statistics Dashboard**: Added comprehensive overview statistics to the home page
  - Number of groups with channels assigned
  - Total number of channels in Dispatcharr
  - Total number of streams available
  - Number of streams assigned to channels
  - Real-time data loaded on each page access
  - Fixed calculation logic to correctly count streams referenced in channel objects
  - Fixed Jinja2 template filter error preventing dashboard display
- **UI Cleanup**: Removed useless text inputs from stream selector modals
  - Eliminated redundant search inputs in force include/exclude sections
  - Streamlined modal interface with descriptive action buttons
  - Improved user experience by removing confusing UI elements

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