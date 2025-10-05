// Auto-assignment rules management

let currentChannels = [];
let currentM3UAccounts = [];
let currentRuleId = null;

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
                <span>${channel.name || 'Canal #' + channel.id}</span>
                <small class="text-muted ms-2">(ID: ${channel.id})</small>
            </div>
        `;
        
        item.innerHTML = displayHtml;
        
        // Handle channel selection
        item.addEventListener('click', function(e) {
            e.preventDefault();
            searchInput.value = channel.name || `Canal #${channel.id}`;
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
        
        const select = document.getElementById('m3uAccountId');
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
            document.getElementById('channelSearch').value = selectedChannel.name || `Canal #${selectedChannel.id}`;
        }
        
        document.getElementById('ruleEnabled').checked = rule.enabled;
        document.getElementById('replaceExisting').checked = rule.replace_existing_streams;
        document.getElementById('regexPattern').value = rule.regex_pattern || '';
        document.getElementById('m3uAccountId').value = rule.m3u_account_id || '';
        document.getElementById('bitrateOperator').value = rule.video_bitrate_operator || '';
        document.getElementById('bitrateValue').value = rule.video_bitrate_value || '';
        document.getElementById('videoCodec').value = rule.video_codec || '';
        document.getElementById('resolution').value = rule.video_resolution || '';
        document.getElementById('videoFps').value = rule.video_fps || '';
        document.getElementById('audioCodec').value = rule.audio_codec || '';
        
        // Load stream testing options
        document.getElementById('testStreamsBeforeSorting').checked = rule.test_streams_before_sorting || false;
        document.getElementById('forceRetestOldStreams').checked = rule.force_retest_old_streams || false;
        document.getElementById('retestDaysThreshold').value = rule.retest_days_threshold || 7;
        
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
    
    const ruleData = {
        name: document.getElementById('ruleName').value,
        channel_id: parseInt(document.getElementById('channelId').value),
        enabled: document.getElementById('ruleEnabled').checked,
        replace_existing_streams: document.getElementById('replaceExisting').checked,
        regex_pattern: document.getElementById('regexPattern').value || null,
        m3u_account_id: document.getElementById('m3uAccountId').value || null,
        bitrate_operator: document.getElementById('bitrateOperator').value || null,
        bitrate_value: document.getElementById('bitrateValue').value || null,
        video_codec: document.getElementById('videoCodec').value || null,
        video_resolution: document.getElementById('resolution').value || null,
        video_fps: document.getElementById('videoFps').value || null,
        audio_codec: document.getElementById('audioCodec').value || null,
        test_streams_before_sorting: testStreamsBeforeSorting,
        force_retest_old_streams: testStreamsBeforeSorting && forceRetestOldStreams,
        retest_days_threshold: retestDaysThreshold
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
                <p class="mb-0"><strong>${preview.match_count}</strong> stream(s) match this rule.</p>
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
        
        if (preview.matching_streams && preview.matching_streams.length > 0) {
            html += `
                <h6>Matching streams:</h6>
                <div class="table-responsive">
                    <table class="table table-sm table-striped">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Name</th>
                                <th>Bitrate</th>
                                <th>Codec</th>
                                <th>Resolution</th>
                                <th>FPS</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            preview.matching_streams.forEach(stream => {
                const stats = stream.stream_stats || {};
                html += `
                    <tr>
                        <td>${stream.id}</td>
                        <td>${stream.name || 'N/A'}</td>
                        <td>${stats.video_bitrate || 'N/A'}</td>
                        <td>${stats.video_codec || 'N/A'}</td>
                        <td>${stats.video_resolution || 'N/A'}</td>
                        <td>${stats.video_fps || 'N/A'}</td>
                    </tr>
                `;
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
                    No streams found matching this rule.
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
