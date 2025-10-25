// Auto-assignment rules management

let currentChannels = [];
let currentM3UAccounts = [];
let currentRuleId = null;
let currentStreams = [];
let streamSelectorMode = null; // 'include' or 'exclude'

// Load initial data
document.addEventListener('DOMContentLoaded', function() {
    loadChannels();
    loadM3UAccounts();
});

// Load channels for dropdown
async function loadChannels() {
    try {
        const response = await fetch('/api/channels');
        if (!response.ok) throw new Error('Error loading channels');
        
        currentChannels = await response.json();
        
        // Setup channel search functionality
        setupChannelSearch();
    } catch (error) {
        console.error('Error loading channels:', error);
        showToast('Error loading channels', 'danger');
    }
}

// Setup channel search with autocomplete
function setupChannelSearch() {
    const searchInput = document.getElementById('channelSearch');
    const channelIdInput = document.getElementById('channelId');
    const dropdown = document.getElementById('channelDropdown');
    
    if (!searchInput || !dropdown) return;
    
    // Show dropdown on focus
    searchInput.addEventListener('focus', function() {
        filterChannels('');
        dropdown.classList.add('show');
    });
    
    // Filter channels on input
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        filterChannels(searchTerm);
        dropdown.classList.add('show');
        
        // Clear hidden input if text doesn't match selected channel
        if (!channelIdInput.value) {
            channelIdInput.removeAttribute('value');
        }
    });
    
    // Hide dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.classList.remove('show');
        }
    });
}

// Filter and display channels
function filterChannels(searchTerm) {
    const dropdown = document.getElementById('channelDropdown');
    const searchInput = document.getElementById('channelSearch');
    const channelIdInput = document.getElementById('channelId');
    
    if (!dropdown) return;
    
    // Filter channels
    const filtered = currentChannels.filter(channel => {
        const name = (channel.name || '').toLowerCase();
        const id = String(channel.id).toLowerCase();
        return name.includes(searchTerm) || id.includes(searchTerm);
    });
    
    // Clear dropdown
    dropdown.innerHTML = '';
    
    if (filtered.length === 0) {
        const noResults = document.createElement('div');
        noResults.className = 'dropdown-item text-muted';
        noResults.textContent = 'No channels found';
        dropdown.appendChild(noResults);
        return;
    }
    
    // Add filtered channels
    filtered.forEach(channel => {
        const item = document.createElement('a');
        item.className = 'dropdown-item';
        item.href = '#';
        item.style.cursor = 'pointer';
        
        // Create channel display with logo if available
        const displayHtml = `
            <div class="d-flex align-items-center">
                ${channel.logo ? 
                    `<img src="${channel.logo}" alt="${channel.name}" style="height: 20px; margin-right: 8px;">` : 
                    '<i class="fas fa-tv text-muted me-2"></i>'
                }
                <span>${channel.name || 'Channel #' + channel.id}</span>
                <small class="text-muted ms-2">(ID: ${channel.id})</small>
            </div>
        `;
        
        item.innerHTML = displayHtml;
        
        // Handle channel selection
        item.addEventListener('click', function(e) {
            e.preventDefault();
            searchInput.value = channel.name || `Channel #${channel.id}`;
            channelIdInput.value = channel.id;
            dropdown.classList.remove('show');
        });
        
        dropdown.appendChild(item);
    });
}

// Load M3U accounts for dropdown
async function loadM3UAccounts() {
    try {
        const response = await fetch('/api/m3u-accounts');
        if (!response.ok) throw new Error('Error loading M3U accounts');
        
        currentM3UAccounts = await response.json();
        
        const select = document.getElementById('m3uAccountIds');
        select.innerHTML = '<option value="">All accounts...</option>';
        
        currentM3UAccounts.forEach(account => {
            const option = document.createElement('option');
            option.value = account.id;
            option.textContent = account.name || `M3U Account #${account.id}`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading M3U accounts:', error);
        // Don't show error if there are no M3U accounts
    }
}

// Show create rule modal
function showCreateRuleModal() {
    currentRuleId = null;
    document.getElementById('ruleModalTitle').textContent = 'New Rule';
    document.getElementById('ruleForm').reset();
    document.getElementById('ruleId').value = '';
    document.getElementById('ruleEnabled').checked = true;
    
    // Clear channel search
    document.getElementById('channelSearch').value = '';
    document.getElementById('channelId').value = '';
    
    // Reset test options
    document.getElementById('testStreamsBeforeSorting').checked = false;
    document.getElementById('forceRetestOldStreams').checked = false;
    document.getElementById('retestDaysThreshold').value = 7;
    
    // Clear manual stream overrides
    document.getElementById('forceIncludeStreamIds').value = '[]';
    document.getElementById('forceExcludeStreamIds').value = '[]';
    document.getElementById('forceIncludeStreamsList').innerHTML = '';
    document.getElementById('forceExcludeStreamsList').innerHTML = '';
    
    // Setup event listeners for modal
    setupModalEventListeners();
    toggleRetestOptions();
    
    const modal = new bootstrap.Modal(document.getElementById('ruleModal'));
    modal.show();
}

// Edit rule
async function editRule(ruleId) {
    try {
        const response = await fetch(`/api/auto-assign-rules/${ruleId}`);
        if (!response.ok) throw new Error('Error loading rule');
        
        const rule = await response.json();
        currentRuleId = ruleId;
        
        // Fill form
        document.getElementById('ruleModalTitle').textContent = 'Edit Rule';
        document.getElementById('ruleId').value = rule.id;
        document.getElementById('ruleName').value = rule.name;
        
        // Set channel with search field
        document.getElementById('channelId').value = rule.channel_id;
        const selectedChannel = currentChannels.find(c => c.id === rule.channel_id);
        if (selectedChannel) {
            document.getElementById('channelSearch').value = selectedChannel.name || `Channel #${selectedChannel.id}`;
        }
        
        document.getElementById('ruleEnabled').checked = rule.enabled;
        document.getElementById('replaceExisting').checked = rule.replace_existing_streams;
        document.getElementById('regexPattern').value = rule.regex_pattern || '';
        
        // Set M3U account selections
        const m3uSelect = document.getElementById('m3uAccountIds');
        Array.from(m3uSelect.options).forEach(option => {
            option.selected = rule.m3u_account_ids && rule.m3u_account_ids.includes(parseInt(option.value));
        });
        
        document.getElementById('bitrateOperator').value = rule.video_bitrate_operator || '';
        document.getElementById('bitrateValue').value = rule.video_bitrate_value || '';
        
        // Helper function to set selected values in multiple select
        const setMultipleSelectValues = (selectId, values) => {
            const select = document.getElementById(selectId);
            // Clear all selections first
            Array.from(select.options).forEach(opt => opt.selected = false);
            
            if (values) {
                // Handle both array and single value
                const valueArray = Array.isArray(values) ? values : [values];
                valueArray.forEach(value => {
                    // Convert to string for comparison
                    const strValue = String(value);
                    Array.from(select.options).forEach(opt => {
                        if (opt.value === strValue) {
                            opt.selected = true;
                        }
                    });
                });
            }
        };
        
        // Set multiple select fields
        setMultipleSelectValues('videoCodec', rule.video_codec);
        setMultipleSelectValues('resolution', rule.video_resolution);
        setMultipleSelectValues('videoFps', rule.video_fps);
        setMultipleSelectValues('audioCodec', rule.audio_codec);
        
        // Load stream testing options
        document.getElementById('testStreamsBeforeSorting').checked = rule.test_streams_before_sorting || false;
        document.getElementById('forceRetestOldStreams').checked = rule.force_retest_old_streams || false;
        document.getElementById('retestDaysThreshold').value = rule.retest_days_threshold || 7;
        
        // Load manual stream overrides
        document.getElementById('forceIncludeStreamIds').value = JSON.stringify(rule.force_include_stream_ids || []);
        document.getElementById('forceExcludeStreamIds').value = JSON.stringify(rule.force_exclude_stream_ids || []);
        
        // Populate stream lists
        populateStreamLists(rule.force_include_stream_ids || [], rule.force_exclude_stream_ids || []);
        
        // Setup event listeners for modal
        setupModalEventListeners();
        toggleRetestOptions();
        
        const modal = new bootstrap.Modal(document.getElementById('ruleModal'));
        modal.show();
    } catch (error) {
        console.error('Error loading rule:', error);
        showToast('Error loading rule', 'danger');
    }
}

// Save rule (create or update)
async function saveRule() {
    const form = document.getElementById('ruleForm');
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    const testStreamsBeforeSorting = document.getElementById('testStreamsBeforeSorting').checked;
    const forceRetestOldStreams = document.getElementById('forceRetestOldStreams').checked;
    const retestDaysThreshold = parseInt(document.getElementById('retestDaysThreshold').value) || 7;
    
    // Get selected values from multiple select fields
    const getSelectedValues = (selectId) => {
        const select = document.getElementById(selectId);
        const selected = Array.from(select.selectedOptions).map(opt => opt.value);
        return selected.length > 0 ? selected : null;
    };
    
    // Get selected integer values from multiple select fields
    const getSelectedIntValues = (selectId) => {
        const select = document.getElementById(selectId);
        const selected = Array.from(select.selectedOptions).map(opt => parseInt(opt.value)).filter(val => !isNaN(val));
        return selected.length > 0 ? selected : null;
    };
    
    // Get numeric values for FPS
    const getFpsValues = () => {
        const select = document.getElementById('videoFps');
        const selected = Array.from(select.selectedOptions).map(opt => parseFloat(opt.value));
        return selected.length > 0 ? selected : null;
    };
    
    const ruleData = {
        name: document.getElementById('ruleName').value,
        channel_id: parseInt(document.getElementById('channelId').value),
        enabled: document.getElementById('ruleEnabled').checked,
        replace_existing_streams: document.getElementById('replaceExisting').checked,
        regex_pattern: document.getElementById('regexPattern').value || null,
        m3u_account_ids: getSelectedIntValues('m3uAccountIds'),
        bitrate_operator: document.getElementById('bitrateOperator').value || null,
        bitrate_value: document.getElementById('bitrateValue').value ? parseFloat(document.getElementById('bitrateValue').value) : null,
        video_codec: getSelectedValues('videoCodec'),
        video_resolution: getSelectedValues('resolution'),
        video_fps: getFpsValues(),
        audio_codec: getSelectedValues('audioCodec'),
        test_streams_before_sorting: testStreamsBeforeSorting,
        force_retest_old_streams: testStreamsBeforeSorting && forceRetestOldStreams,
        retest_days_threshold: retestDaysThreshold,
        force_include_stream_ids: JSON.parse(document.getElementById('forceIncludeStreamIds').value || '[]'),
        force_exclude_stream_ids: JSON.parse(document.getElementById('forceExcludeStreamIds').value || '[]')
    };
    
    try {
        let response;
        if (currentRuleId) {
            // Update existing rule
            response = await fetch(`/api/auto-assign-rules/${currentRuleId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(ruleData)
            });
        } else {
            // Create new rule
            response = await fetch('/api/auto-assign-rules', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(ruleData)
            });
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Error saving rule');
        }
        
        showToast(currentRuleId ? 'Rule updated successfully' : 'Rule created successfully', 'success');
        
        // Close modal and reload page
        bootstrap.Modal.getInstance(document.getElementById('ruleModal')).hide();
        setTimeout(() => location.reload(), 500);
    } catch (error) {
        console.error('Error saving rule:', error);
        showToast(error.message, 'danger');
    }
}

// Delete rule
async function deleteRule(ruleId) {
    if (!confirm('Are you sure you want to delete this rule?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/auto-assign-rules/${ruleId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Error deleting rule');
        }
        
        showToast('Rule deleted successfully', 'success');
        setTimeout(() => location.reload(), 500);
    } catch (error) {
        console.error('Error deleting rule:', error);
        showToast(error.message, 'danger');
    }
}

// Toggle rule enabled/disabled
async function toggleRule(ruleId) {
    const checkbox = document.getElementById(`enableRule${ruleId}`);
    const originalState = checkbox.checked;
    
    try {
        const response = await fetch(`/api/auto-assign-rules/${ruleId}/toggle`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Error changing rule status');
        }
        
        const result = await response.json();
        showToast(result.message, 'success');
        
        // Reload page to update visual status
        setTimeout(() => location.reload(), 500);
        
    } catch (error) {
        console.error('Error toggling rule:', error);
        // Revert checkbox state
        checkbox.checked = !originalState;
        showToast(error.message, 'danger');
    }
}

// Preview rule matches
async function previewRule(ruleId) {
    const modal = new bootstrap.Modal(document.getElementById('previewModal'));
    modal.show();
    
    document.getElementById('previewContent').innerHTML = `
        <div class="text-center">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Analyzing streams...</p>
        </div>
    `;
    
    try {
        const response = await fetch(`/api/auto-assign-rules/${ruleId}/preview`);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Error getting preview');
        }
        
        const preview = await response.json();
        
        let html = `
            <div class="alert alert-info">
                <h5><i class="fas fa-info-circle"></i> Summary</h5>
                <p class="mb-1"><strong>${preview.match_count}</strong> stream(s) fully match all conditions.</p>
                <p class="mb-1"><strong>${preview.regex_match_count}</strong> stream(s) match the basic regex filter.</p>
                <p class="mb-0"><small class="text-muted">Showing all regex matches with highlighting</small></p>
            </div>
        `;
        
        if (preview.conditions_applied && preview.conditions_applied.length > 0) {
            html += `
                <div class="mb-3">
                    <h6>Applied conditions:</h6>
                    <ul>
                        ${preview.conditions_applied.map(cond => `<li>${cond}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        // Helper function to format stream row
        function formatStreamRow(stream, rowClass = '', statusBadge = '') {
            const stats = stream.stream_stats || {};
            
            // Format bitrate
            let bitrateDisplay = 'N/A';
            if (stats.ffmpeg_output_bitrate) {
                bitrateDisplay = `${Math.round(stats.ffmpeg_output_bitrate)} kbps`;
            }
            
            // Format resolution
            let resolutionDisplay = 'N/A';
            if (stats.resolution) {
                resolutionDisplay = normalizeResolution(stats.resolution);
            }
            
            // Format FPS
            let fpsDisplay = 'N/A';
            if (stats.source_fps) {
                fpsDisplay = Math.round(stats.source_fps);
            }
            
            // Format M3U source
            let m3uSource = 'Unknown';
            if (stream.m3u_source) {
                const m3uAccount = currentM3UAccounts.find(acc => acc.id === parseInt(stream.m3u_source));
                m3uSource = m3uAccount ? m3uAccount.name : `M3U Account #${stream.m3u_source}`;
            }
            
            // Format Audio Codec
            const audioCodec = stats.audio_codec || 'N/A';
            
            return `
                <tr class="${rowClass}">
                    <td>${stream.id}</td>
                    <td>${m3uSource}</td>
                    <td>${stream.name || 'N/A'} ${statusBadge}</td>
                    <td>${bitrateDisplay}</td>
                    <td>${stats.video_codec || 'N/A'}</td>
                    <td>${audioCodec}</td>
                    <td>${resolutionDisplay}</td>
                    <td>${fpsDisplay}</td>
                </tr>
            `;
        }
        
        if (preview.regex_matching_streams && preview.regex_matching_streams.length > 0) {
            html += `
                <h6>Regex matching streams:</h6>
                <div class="mb-2">
                    <small class="text-muted">
                        <i class="fas fa-circle text-success"></i> Fully matches all conditions &nbsp;&nbsp;
                        <i class="fas fa-circle text-secondary"></i> Matches regex but fails other conditions &nbsp;&nbsp;
                        <i class="fas fa-circle text-warning"></i> Matches regex but lacks required stats
                    </small>
                </div>
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>M3U Source</th>
                                <th>Name</th>
                                <th>Bitrate</th>
                                <th>Video Codec</th>
                                <th>Audio Codec</th>
                                <th>Resolution</th>
                                <th>FPS</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            // Create sets for quick lookup
            const fullyMatchingIds = new Set(preview.fully_matching_streams.map(s => s.id));
            const noStatsIds = new Set(preview.no_stats_streams.map(s => s.id));
            
            // Sort streams by ID for consistent display
            const sortedStreams = [...preview.regex_matching_streams].sort((a, b) => a.id - b.id);
            
            sortedStreams.forEach(stream => {
                if (fullyMatchingIds.has(stream.id)) {
                    // Fully matching - green highlight
                    html += formatStreamRow(stream, 'table-success', '<i class="fas fa-check-circle text-success ms-1" title="Fully matches all conditions"></i>');
                } else if (noStatsIds.has(stream.id)) {
                    // No stats - yellow/orange highlight
                    html += formatStreamRow(stream, 'table-warning', '<i class="fas fa-exclamation-triangle text-warning ms-1" title="Lacks required statistics"></i>');
                } else {
                    // Partially matching - gray highlight
                    html += formatStreamRow(stream, 'table-secondary', '<i class="fas fa-times-circle text-secondary ms-1" title="Fails other conditions"></i>');
                }
            });
            
            html += `
                        </tbody>
                    </table>
                </div>
            `;
        } else {
            html += `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    No streams found matching the basic regex filter.
                </div>
            `;
        }
        
        document.getElementById('previewContent').innerHTML = html;
    } catch (error) {
        console.error('Error previewing rule:', error);
        document.getElementById('previewContent').innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-times-circle"></i>
                Error getting preview: ${error.message}
            </div>
        `;
    }
}

// Preview rule from form (before saving)
function previewRuleFromForm() {
    showToast('Save the rule first to see the preview', 'info');
}

// Execute rule
async function executeRule(ruleId) {
    if (!confirm('Do you want to execute this rule and assign matching streams to the channel?')) {
        return;
    }
    
    try {
        // First, get rule details to check if testing is required
        const ruleResponse = await fetch(`/api/auto-assign-rules/${ruleId}`);
        if (!ruleResponse.ok) {
            throw new Error('Failed to fetch rule details');
        }
        const rule = await ruleResponse.json();
        
        // Determine if we should use SSE (streaming) mode
        const useStream = rule && rule.test_streams_before_sorting === true;
        
        const response = await fetch(`/api/auto-assign-rules/${ruleId}/execute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                stream: useStream
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Error executing rule');
        }
        
        const result = await response.json();
        
        // If result has stream=true and execution_id, use progress modal with SSE
        if (result.stream && result.execution_id) {
            showExecutionProgressModal(ruleId, result.execution_id);
            return;
        }
        
        // Otherwise, show simple toast notification
        showToast(
            `Rule executed: ${result.streams_added} stream(s) added from ${result.matches_found} matches`,
            'success'
        );
    } catch (error) {
        console.error('Error executing rule:', error);
        showToast(error.message, 'danger');
    }
}

// Show toast notification
function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    
    // Create toast
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    container.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

/**
 * Toggle retest options based on test streams checkbox
 */
function toggleRetestOptions() {
    const testEnabled = document.getElementById('testStreamsBeforeSorting').checked;
    const forceRetestCheckbox = document.getElementById('forceRetestOldStreams');
    const retestDaysInput = document.getElementById('retestDaysThreshold');
    
    if (forceRetestCheckbox && retestDaysInput) {
        forceRetestCheckbox.disabled = !testEnabled;
        // Threshold is always enabled if testing is enabled
        retestDaysInput.disabled = !testEnabled;
        
        if (!testEnabled) {
            forceRetestCheckbox.checked = false;
        }
    }
}

/**
 * Setup event listeners for modal form controls
 */
function setupModalEventListeners() {
    const testCheckbox = document.getElementById('testStreamsBeforeSorting');
    const forceRetestCheckbox = document.getElementById('forceRetestOldStreams');
    
    if (testCheckbox) {
        // Remove existing listeners to avoid duplicates
        testCheckbox.removeEventListener('change', toggleRetestOptions);
        testCheckbox.addEventListener('change', toggleRetestOptions);
    }
}

/**
 * Normalizes a resolution string to standard format (720p, 1080p, 2160p, SD)
 */
function normalizeResolution(resolutionStr) {
    if (!resolutionStr) return 'N/A';
    
    // Parse width x height
    const match = resolutionStr.match(/(\d+)x(\d+)/);
    if (!match) return resolutionStr;
    
    const height = parseInt(match[2]);
    
    if (height >= 2000) return '2160p';  // 4K
    if (height >= 1000) return '1080p';  // Full HD
    if (height >= 700) return '720p';    // HD
    return 'SD';  // Standard Definition
}

// ========== BULK RULE CREATION FUNCTIONS ==========

let currentChannelGroups = [];

// Load channel groups for bulk creation
async function loadChannelGroups() {
    try {
        const response = await fetch('/api/channel-groups');
        if (!response.ok) throw new Error('Error loading channel groups');
        
        currentChannelGroups = await response.json();
        
        // Populate bulk creation modal
        populateBulkGroupSelect();
    } catch (error) {
        console.error('Error loading channel groups:', error);
        showToast('Error loading channel groups', 'danger');
    }
}

// Populate group select in bulk creation modal
function populateBulkGroupSelect() {
    const select = document.getElementById('bulkGroupId');
    if (!select) return;
    
    select.innerHTML = '<option value="">Select a group...</option>';
    
    currentChannelGroups.forEach(group => {
        const option = document.createElement('option');
        option.value = group.id;
        option.textContent = `${group.name} (${group.channel_ids.length} channels)`;
        if (group.description) {
            option.title = group.description;
        }
        select.appendChild(option);
    });
}

// Show bulk create modal
function showBulkCreateModal() {
    // Load channel groups if not already loaded
    if (currentChannelGroups.length === 0) {
        loadChannelGroups();
    } else {
        populateBulkGroupSelect();
    }
    
    // Reset form
    document.getElementById('bulkCreateForm').reset();
    document.getElementById('bulkEnabled').checked = true;
    
    // Setup event listeners for bulk modal
    setupBulkModalEventListeners();
    toggleBulkRetestOptions();
    
    const modal = new bootstrap.Modal(document.getElementById('bulkCreateModal'));
    modal.show();
}

// Setup event listeners for bulk modal form controls
function setupBulkModalEventListeners() {
    const testCheckbox = document.getElementById('bulkTestStreamsBeforeSorting');
    const forceRetestCheckbox = document.getElementById('bulkForceRetestOldStreams');
    
    if (testCheckbox) {
        // Remove existing listeners to avoid duplicates
        testCheckbox.removeEventListener('change', toggleBulkRetestOptions);
        testCheckbox.addEventListener('change', toggleBulkRetestOptions);
    }
}

// Toggle bulk retest options
function toggleBulkRetestOptions() {
    const testCheckbox = document.getElementById('bulkTestStreamsBeforeSorting');
    const forceRetestCheckbox = document.getElementById('bulkForceRetestOldStreams');
    const retestDaysInput = document.getElementById('bulkRetestDaysThreshold');
    const retestContainer = document.getElementById('bulkRetestThresholdContainer');
    
    const testEnabled = testCheckbox && testCheckbox.checked;
    
    if (forceRetestCheckbox) {
        forceRetestCheckbox.disabled = !testEnabled;
    }
    if (retestDaysInput) {
        retestDaysInput.disabled = !testEnabled;
    }
    if (retestContainer) {
        retestContainer.style.display = testEnabled ? 'block' : 'none';
    }
    
    if (!testEnabled) {
        if (forceRetestCheckbox) forceRetestCheckbox.checked = false;
    }
}

// Create bulk rules
async function createBulkRules() {
    try {
        // Validate form
        const groupId = document.getElementById('bulkGroupId').value;
        if (!groupId) {
            showToast('Please select a channel group', 'warning');
            return;
        }
        
        // Collect form data
        const formData = {
            group_id: parseInt(groupId),
            skip_existing_channels: document.getElementById('bulkSkipExisting').checked,
            enabled: document.getElementById('bulkEnabled').checked,
            replace_existing_streams: document.getElementById('bulkReplaceExisting').checked,
            test_streams_before_sorting: document.getElementById('bulkTestStreamsBeforeSorting').checked,
            force_retest_old_streams: document.getElementById('bulkForceRetestOldStreams').checked,
            retest_days_threshold: parseInt(document.getElementById('bulkRetestDaysThreshold').value) || 7,
            m3u_account_ids: Array.from(document.getElementById('bulkM3uAccountIds').selectedOptions).map(opt => parseInt(opt.value)).filter(id => id),
            bitrate_operator: document.getElementById('bulkBitrateOperator').value === 'No restriction...' ? null : document.getElementById('bulkBitrateOperator').value,
            bitrate_value: document.getElementById('bulkBitrateValue').value ? parseInt(document.getElementById('bulkBitrateValue').value) : null,
            video_codec: Array.from(document.getElementById('bulkVideoCodec').selectedOptions).map(opt => opt.value),
            video_resolution: Array.from(document.getElementById('bulkResolution').selectedOptions).map(opt => opt.value),
            video_fps: Array.from(document.getElementById('bulkVideoFps').selectedOptions).map(opt => parseInt(opt.value)),
            audio_codec: Array.from(document.getElementById('bulkAudioCodec').selectedOptions).map(opt => opt.value)
        };
        
        // Clean empty arrays
        if (formData.m3u_account_ids.length === 0) delete formData.m3u_account_ids;
        if (formData.video_codec.length === 0) delete formData.video_codec;
        if (formData.video_resolution.length === 0) delete formData.video_resolution;
        if (formData.video_fps.length === 0) delete formData.video_fps;
        if (formData.audio_codec.length === 0) delete formData.audio_codec;
        
        // Show loading
        const createBtn = document.querySelector('#bulkCreateModal .btn-success');
        const originalText = createBtn.innerHTML;
        createBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating...';
        createBtn.disabled = true;
        
        // Make API call
        const response = await fetch('/api/auto-assign-rules/bulk-create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showToast(result.message, 'success');
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('bulkCreateModal'));
            modal.hide();
            
            // Reload page to show new rules
            setTimeout(() => {
                window.location.reload();
            }, 1000);
            
            // Show detailed results
            if (result.errors && result.errors.length > 0) {
                let details = `Processed ${result.channels_processed} channels`;
                if (result.rules_created && result.rules_created.length > 0) {
                    details += ` (${result.rules_created.length} created`;
                }
                if (result.rules_updated && result.rules_updated.length > 0) {
                    details += `${result.rules_created && result.rules_created.length > 0 ? ', ' : ' ('}${result.rules_updated.length} updated`;
                }
                details += `).\n`;
                if (result.channels_skipped > 0) {
                    details += `Skipped ${result.channels_skipped} channels with existing rules.\n`;
                }
                details += `\nErrors:\n${result.errors.join('\n')}`;
                alert(details);
            } else {
                let details = `Successfully processed ${result.channels_processed} channels`;
                if (result.rules_created && result.rules_created.length > 0) {
                    details += ` (${result.rules_created.length} created`;
                }
                if (result.rules_updated && result.rules_updated.length > 0) {
                    details += `${result.rules_created && result.rules_created.length > 0 ? ', ' : ' ('}${result.rules_updated.length} updated`;
                }
                details += `).`;
                if (result.channels_skipped > 0) {
                    details += `\nSkipped ${result.channels_skipped} channels with existing rules.`;
                }
                alert(details);
            }
            
        } else {
            showToast(result.error || 'Error creating bulk rules', 'danger');
        }
        
    } catch (error) {
        console.error('Error creating bulk rules:', error);
        showToast('Error creating bulk rules', 'danger');
    } finally {
        // Restore button
        const createBtn = document.querySelector('#bulkCreateModal .btn-success');
        createBtn.innerHTML = '<i class="fas fa-magic"></i> Create Rules';
        createBtn.disabled = false;
    }
}

// Stream selection functionality
async function loadStreams() {
    try {
        const response = await fetch('/api/streams');
        if (!response.ok) throw new Error('Error loading streams');
        
        currentStreams = await response.json();
    } catch (error) {
        console.error('Error loading streams:', error);
        showToast('Error loading streams', 'danger');
    }
}

function showStreamSelector(mode) {
    streamSelectorMode = mode;
    const modal = new bootstrap.Modal(document.getElementById('streamSelectorModal'));
    const title = mode === 'include' ? 'Select Streams to Force Include' : 'Select Streams to Force Exclude';
    document.getElementById('streamSelectorTitle').textContent = title;
    
    // Load streams if not already loaded
    if (currentStreams.length === 0) {
        loadStreams().then(() => {
            renderStreamList('');
            modal.show();
        });
    } else {
        renderStreamList('');
        modal.show();
    }
}

function renderStreamList(searchTerm) {
    const streamList = document.getElementById('streamList');
    const filteredStreams = currentStreams.filter(stream => 
        stream.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        stream.id.toString().includes(searchTerm)
    );
    
    streamList.innerHTML = '';
    
    if (filteredStreams.length === 0) {
        streamList.innerHTML = '<div class="p-3 text-muted">No streams found</div>';
        return;
    }
    
    filteredStreams.forEach(stream => {
        const streamItem = document.createElement('div');
        streamItem.className = 'p-2 border-bottom d-flex align-items-center';
        streamItem.innerHTML = `
            <div class="form-check me-3">
                <input class="form-check-input stream-checkbox" type="checkbox" 
                       value="${stream.id}" id="stream_${stream.id}">
            </div>
            <div class="flex-grow-1">
                <strong>${stream.name}</strong>
                <small class="text-muted d-block">ID: ${stream.id}</small>
            </div>
        `;
        streamList.appendChild(streamItem);
    });
}

function addSelectedStreams() {
    const selectedCheckboxes = document.querySelectorAll('#streamList .stream-checkbox:checked');
    const selectedStreamIds = Array.from(selectedCheckboxes).map(cb => parseInt(cb.value));
    
    if (selectedStreamIds.length === 0) {
        showToast('No streams selected', 'warning');
        return;
    }
    
    const selectedStreams = currentStreams.filter(stream => selectedStreamIds.includes(stream.id));
    
    if (streamSelectorMode === 'include') {
        addStreamsToIncludeList(selectedStreams);
    } else {
        addStreamsToExcludeList(selectedStreams);
    }
    
    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('streamSelectorModal'));
    modal.hide();
}

function addStreamsToIncludeList(streams) {
    const listContainer = document.getElementById('forceIncludeStreamsList');
    const hiddenInput = document.getElementById('forceIncludeStreamIds');
    
    let currentIds = JSON.parse(hiddenInput.value || '[]');
    
    streams.forEach(stream => {
        if (!currentIds.includes(stream.id)) {
            currentIds.push(stream.id);
            
            const streamBadge = document.createElement('span');
            streamBadge.className = 'badge bg-success me-1 mb-1';
            streamBadge.innerHTML = `
                ${stream.name} 
                <button type="button" class="btn-close btn-close-white ms-1" 
                        onclick="removeStreamFromInclude(${stream.id})" 
                        style="font-size: 0.6rem;"></button>
            `;
            listContainer.appendChild(streamBadge);
        }
    });
    
    hiddenInput.value = JSON.stringify(currentIds);
}

function addStreamsToExcludeList(streams) {
    const listContainer = document.getElementById('forceExcludeStreamsList');
    const hiddenInput = document.getElementById('forceExcludeStreamIds');
    
    let currentIds = JSON.parse(hiddenInput.value || '[]');
    
    streams.forEach(stream => {
        if (!currentIds.includes(stream.id)) {
            currentIds.push(stream.id);
            
            const streamBadge = document.createElement('span');
            streamBadge.className = 'badge bg-danger me-1 mb-1';
            streamBadge.innerHTML = `
                ${stream.name} 
                <button type="button" class="btn-close btn-close-white ms-1" 
                        onclick="removeStreamFromExclude(${stream.id})" 
                        style="font-size: 0.6rem;"></button>
            `;
            listContainer.appendChild(streamBadge);
        }
    });
    
    hiddenInput.value = JSON.stringify(currentIds);
}

function removeStreamFromInclude(streamId) {
    const listContainer = document.getElementById('forceIncludeStreamsList');
    const hiddenInput = document.getElementById('forceIncludeStreamIds');
    
    let currentIds = JSON.parse(hiddenInput.value || '[]');
    currentIds = currentIds.filter(id => id !== streamId);
    hiddenInput.value = JSON.stringify(currentIds);
    
    // Remove badge
    const badges = listContainer.querySelectorAll('.badge');
    badges.forEach(badge => {
        if (badge.textContent.includes(`ID: ${streamId}`) || badge.innerHTML.includes(`removeStreamFromInclude(${streamId})`)) {
            badge.remove();
        }
    });
}

function removeStreamFromExclude(streamId) {
    const listContainer = document.getElementById('forceExcludeStreamsList');
    const hiddenInput = document.getElementById('forceExcludeStreamIds');
    
    let currentIds = JSON.parse(hiddenInput.value || '[]');
    currentIds = currentIds.filter(id => id !== streamId);
    hiddenInput.value = JSON.stringify(currentIds);
    
    // Remove badge
    const badges = listContainer.querySelectorAll('.badge');
    badges.forEach(badge => {
        if (badge.textContent.includes(`ID: ${streamId}`) || badge.innerHTML.includes(`removeStreamFromExclude(${streamId})`)) {
            badge.remove();
        }
    });
}

async function populateStreamLists(includeIds, excludeIds) {
    // Load streams if not already loaded
    if (currentStreams.length === 0) {
        await loadStreams();
    }
    
    // Clear existing lists
    document.getElementById('forceIncludeStreamsList').innerHTML = '';
    document.getElementById('forceExcludeStreamsList').innerHTML = '';
    
    // Populate include list
    if (includeIds && includeIds.length > 0) {
        const includeStreams = currentStreams.filter(stream => includeIds.includes(stream.id));
        includeStreams.forEach(stream => {
            const streamBadge = document.createElement('span');
            streamBadge.className = 'badge bg-success me-1 mb-1';
            streamBadge.innerHTML = `
                ${stream.name} 
                <button type="button" class="btn-close btn-close-white ms-1" 
                        onclick="removeStreamFromInclude(${stream.id})" 
                        style="font-size: 0.6rem;"></button>
            `;
            document.getElementById('forceIncludeStreamsList').appendChild(streamBadge);
        });
    }
    
    // Populate exclude list
    if (excludeIds && excludeIds.length > 0) {
        const excludeStreams = currentStreams.filter(stream => excludeIds.includes(stream.id));
        excludeStreams.forEach(stream => {
            const streamBadge = document.createElement('span');
            streamBadge.className = 'badge bg-danger me-1 mb-1';
            streamBadge.innerHTML = `
                ${stream.name} 
                <button type="button" class="btn-close btn-close-white ms-1" 
                        onclick="removeStreamFromExclude(${stream.id})" 
                        style="font-size: 0.6rem;"></button>
            `;
            document.getElementById('forceExcludeStreamsList').appendChild(streamBadge);
        });
    }
}

// Initialize bulk functionality when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadChannels();
    loadM3UAccounts();
    loadChannelGroups();  // Load groups for bulk creation
    
    // Setup stream search
    const streamSearchInput = document.getElementById('streamSearchInput');
    if (streamSearchInput) {
        streamSearchInput.addEventListener('input', function() {
            renderStreamList(this.value);
        });
    }
    
    // Setup stream selection confirmation
    const confirmBtn = document.getElementById('confirmStreamSelection');
    if (confirmBtn) {
        confirmBtn.addEventListener('click', addSelectedStreams);
    }
});
