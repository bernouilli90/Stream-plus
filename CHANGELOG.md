## [0.2.14] - 2025-10-21

### Changed
- **Complete Stream Testing Failure Behavior**: All stream statistics are now cleared whenever ANY part of stream testing fails
  - **ffprobe failures**: When ffprobe command fails or returns invalid data, all stats are cleared
  - **ffmpeg failures**: When ffmpeg fails to calculate bitrate, all stats are cleared (previous change)
  - **Timeouts**: When stream testing times out, all stats are cleared
  - **General errors**: When any exception occurs during testing, all stats are cleared
  - **Consistent behavior**: Stream testing now requires complete success of both ffprobe and ffmpeg for stats to be saved

## [0.2.13] - 2025-10-21

### Changed
- **Stream Testing Failure Behavior**: When ffmpeg fails to calculate bitrate, all stream statistics are now cleared instead of keeping partial ffprobe data
  - Previously: ffprobe data was saved even when bitrate calculation failed
  - Now: Complete failure when bitrate cannot be calculated, clearing all stats from Dispatcharr

## [0.2.12] - 2025-10-21

### Changed
- **Stream Testing**: Removed alternative ffprobe command fallback, now uses only the primary ffprobe command for stream analysis

## [0.2.11] - 2025-10-21

### Enhanced
- **Stream Testing Logging**: Completely redesigned logging output for stream testing operations
  - **Stream Information**: Now displays stream name and URL at the start of testing
  - **FFprobe Analysis**: Clear success/failure reporting with detailed stream information when successful
    - Shows video resolution, codec, framerate when available
    - Shows audio codec, channels, sample rate when available
    - Displays stream format type
    - Shows specific error messages when ffprobe fails
  - **FFmpeg Bitrate Analysis**: Enhanced logging for bitrate calculation process
    - Clear success/failure status with calculated bitrate when successful
    - Detailed error reporting when ffmpeg fails
    - Warning when using ffprobe data only (no bitrate calculation)
  - **Visual Structure**: Uses emojis and clear section headers for better readability
    - 🔍 Stream identification
    - 📊 FFprobe analysis section
    - 🎬 FFmpeg bitrate analysis section
    - 📊 Final statistics summary
  - **Improved Error Context**: Better error messages with return codes and specific failure reasons

### Fixed
- **Stream Testing UnboundLocalError**: Fixed critical bug where `test_stream()` method crashed with "UnboundLocalError: cannot access local variable 'quoted_cmd' where it is not associated with a value"
  - Issue occurred when stream testing failed early due to undefined variable reference in logging code
  - Properly structured command logging with correct variable definitions and scope
  - Fixed indentation and code structure issues from recent logging enhancements
  - Stream testing now handles all error conditions without crashing

### Fixed
- **Stream Stats Clearing on Test Failures**: Fixed critical issue where `clear_stream_stats()` method wasn't properly clearing stream statistics due to Dispatcharr API limitations with PATCH operations
  - Changed implementation from PATCH with partial updates to PUT with complete stream object retrieval and update
  - Method now retrieves current stream, clears `stream_stats` field, removes `stream_stats_updated_at` timestamp, and updates complete stream object
  - Ensures failed stream tests properly remove stale statistics that could affect rule evaluation
  - Added comprehensive unit tests covering success cases, error handling, and edge cases
  - Created integration test script for validation against real Dispatcharr instances

### Technical Details
- Modified `clear_stream_stats()` in `api/dispatcharr_client.py` to use PUT instead of PATCH
- Added unit tests in `test_clear_stats_put.py` with full mock coverage
- Created integration test in `test_clear_stats_integration.py` for real API validation
- Maintains backward compatibility while fixing the core clearing functionality

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
  - When `test_streams_before_sorting=True`, streams are now properly tested based on timestamp
  - Implemented proper timestamp checking using `stream_stats_updated_at` field
  - Streams with stats older than `retest_days_threshold` are re-tested automatically
  - **Stream stats are now properly updated** when testing succeeds or cleared when testing fails
  - Fixed issue where stale stats prevented proper rule evaluation
  - Improved reliability of auto-assignment rules with stream testing enabled
- **FFprobe Path Configuration**: Fixed Windows compatibility issue with ffprobe executable path
  - Updated `tools/ffprobe_path.txt` to use correct Windows path for local ffmpeg installation
  - Changed from Linux path (`/usr/bin/ffprobe`) to Windows relative path (`tools\ffmpeg\ffmpeg-7.1-essentials_build\bin\ffprobe.exe`)
  - Resolves "ffprobe executable not found" error on Windows systems
- **Stream Stats Clearing on Test Failures**: Fixed issue where failed stream tests didn't clear stale statistics
  - Modified `clear_stream_stats()` to only update `stream_stats` field, avoiding API issues with timestamp
  - Removed problematic `stream_stats_updated_at: None` that could cause API rejection
  - Added explicit logging to show when stats are cleared or clearing fails
  - Ensures failed streams have their invalid stats properly removed from Dispatcharr

### Enhanced
- **FFprobe Stream Selection**: Primary ffprobe command now focuses on first video stream
  - Added `-select_streams v:0` to VLC-style ffprobe command for better compatibility
  - Improves stream analysis success rate for complex multi-stream sources
  - Maintains JSON output format for consistent data parsing
- **Stream Testing Performance Optimization**: Reordered ffprobe and ffmpeg execution for faster failure detection
  - FFprobe now runs first as a quick accessibility check (faster than ffmpeg)
  - If ffprobe fails, ffmpeg is skipped entirely and test is marked as failed immediately
  - Reduces testing time for broken streams by avoiding unnecessary ffmpeg execution
  - Maintains full functionality when both tools succeed

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