/**
 * Stream Sorter JavaScript
 * Handles sorting rules management with scoring system
 */

var currentRuleId = null;
var conditionCounter = 0;
var selectedChannelIds = [];
var selectedChannelGroupIds = [];
var allChannelsSelected = false;  // New flag for "all channels" mode

// Condition type configurations
var conditionTypes = {
    m3u_source: {
        label: 'M3U Source',
        hasOperator: false,
        valueType: 'select',
        valueSource: 'm3uAccounts'
    },
    video_bitrate: {
        label: 'Video Bitrate (kbps)',
        hasOperator: true,
        valueType: 'number',
        operators: ['>', '>=', '<', '<=', '==']
    },
    video_resolution: {
        label: 'Video Resolution',
        hasOperator: true,
        valueType: 'select',
        operators: ['==', '!='],
        values: ['720p', '1080p', '2160p', 'SD']
    },
    video_codec: {
        label: 'Video Codec',
        hasOperator: true,
        valueType: 'select',
        operators: ['==', '!='],
        values: ['h264', 'h265', 'hevc', 'vp9', 'av1', 'mpeg2']
    },
    audio_codec: {
        label: 'Audio Codec',
        hasOperator: true,
        valueType: 'select',
        operators: ['==', '!='],
        values: ['aac', 'ac3', 'eac3', 'mp3', 'opus', 'flac']
    },
    video_fps: {
        label: 'Video FPS',
        hasOperator: true,
        valueType: 'number',
        operators: ['>', '>=', '<', '<=', '==']
    }
};

/**
 * Show create rule modal
 */
function showCreateRuleModal() {
    // Update channel groups before showing modal
    updateChannelGroups().then(() => {
        currentRuleId = null;
        selectedChannelIds = [];
        selectedChannelGroupIds = [];
        allChannelsSelected = false;
        document.getElementById('sortingRuleModalTitle').textContent = 'New Sorting Rule';
        document.getElementById('sortingRuleForm').reset();
        document.getElementById('ruleId').value = '';
        document.getElementById('conditionsContainer').innerHTML = '';
        document.getElementById('selectedChannelTags').innerHTML = '';
        document.getElementById('selectedChannelGroupTags').innerHTML = '';
        conditionCounter = 0;
        
        // Reset test options
        document.getElementById('testStreamsBeforeSorting').checked = false;
        document.getElementById('forceRetestOldStreams').checked = false;
        document.getElementById('retestDaysThreshold').value = 7;
        document.getElementById('executionOrder').value = '';
        
        // Setup event listeners for modal
        setupModalEventListeners();
        toggleRetestOptions();
        
        updateMaxPossibleScore();
        
        const modal = new bootstrap.Modal(document.getElementById('sortingRuleModal'));
        modal.show();
    }).catch(error => {
        console.error('Error updating channel groups:', error);
        StreamPlus.showNotification('Error loading channel groups', 'error');
    });
}

/**
 * Add a new condition to the form
 */
function addCondition(conditionData = null) {
    conditionCounter++;
    const conditionId = `condition_${conditionCounter}`;
    
    const conditionHtml = `
        <div class="card mb-2 condition-item" id="${conditionId}">
            <div class="card-body p-3">
                <div class="row g-2">
                    <!-- Condition Type -->
                    <div class="col-md-3">
                        <label class="form-label small">Condition Type</label>
                        <select class="form-select form-select-sm condition-type" 
                                onchange="updateConditionInputs('${conditionId}')">
                            ${Object.keys(conditionTypes).map(key => `
                                <option value="${key}" ${conditionData && conditionData.condition_type === key ? 'selected' : ''}>
                                    ${conditionTypes[key].label}
                                </option>
                            `).join('')}
                        </select>
                    </div>

                    <!-- Operator (conditional) -->
                    <div class="col-md-2 operator-container">
                        <label class="form-label small">Operator</label>
                        <select class="form-select form-select-sm condition-operator">
                            <!-- Will be populated dynamically -->
                        </select>
                    </div>

                    <!-- Value -->
                    <div class="col-md-4 value-container">
                        <label class="form-label small">Value</label>
                        <input type="text" class="form-control form-control-sm condition-value" 
                               placeholder="Enter value">
                    </div>

                    <!-- Points -->
                    <div class="col-md-2">
                        <label class="form-label small">Points</label>
                        <input type="number" class="form-control form-control-sm condition-points" 
                               value="${conditionData ? conditionData.points : 1}" min="1" max="1000"
                               onchange="updateMaxPossibleScore()">
                    </div>

                    <!-- Remove Button -->
                    <div class="col-md-1 d-flex align-items-end">
                        <button type="button" class="btn btn-sm btn-danger w-100" 
                                onclick="removeCondition('${conditionId}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    document.getElementById('conditionsContainer').insertAdjacentHTML('beforeend', conditionHtml);
    
    // Initialize the condition with the right inputs
    updateConditionInputs(conditionId);
    
    // If we have data, populate it
    if (conditionData) {
        const conditionElement = document.getElementById(conditionId);
        conditionElement.querySelector('.condition-operator').value = conditionData.operator || '';
        conditionElement.querySelector('.condition-value').value = conditionData.value || '';
    }
    
    updateMaxPossibleScore();
}

/**
 * Update condition inputs based on selected type
 */
function updateConditionInputs(conditionId) {
    const conditionElement = document.getElementById(conditionId);
    const typeSelect = conditionElement.querySelector('.condition-type');
    const operatorContainer = conditionElement.querySelector('.operator-container');
    const valueContainer = conditionElement.querySelector('.value-container');
    const operatorSelect = conditionElement.querySelector('.condition-operator');
    const valueInput = conditionElement.querySelector('.condition-value');
    
    const selectedType = typeSelect.value;
    const config = conditionTypes[selectedType];
    
    // Update operator visibility and options
    if (config.hasOperator) {
        operatorContainer.style.display = 'block';
        operatorSelect.innerHTML = config.operators.map(op => 
            `<option value="${op}">${op}</option>`
        ).join('');
    } else {
        operatorContainer.style.display = 'none';
    }
    
    // Update value input type
    if (config.valueType === 'select') {
        let options;
        if (config.valueSource === 'm3uAccounts') {
            options = m3uAccounts.map(account => 
                `<option value="${account.id}">${account.name || 'Account #' + account.id}</option>`
            ).join('');
        } else {
            options = config.values.map(val => {
                let displayText = val.toUpperCase();
                if (val === 'SD') {
                    displayText = 'SD (&lt; 720p)';
                }
                return `<option value="${val}">${displayText}</option>`;
            }).join('');
        }
        
        valueContainer.innerHTML = `
            <label class="form-label small">Value</label>
            <select class="form-select form-select-sm condition-value">
                ${options}
            </select>
        `;
    } else {
        valueContainer.innerHTML = `
            <label class="form-label small">Value</label>
            <input type="${config.valueType}" class="form-control form-control-sm condition-value" 
                   placeholder="${config.placeholder || 'Enter value'}">
        `;
    }
}

/**
 * Remove a condition
 */
function removeCondition(conditionId) {
    document.getElementById(conditionId).remove();
    updateMaxPossibleScore();
}

/**
 * Update max possible score display
 */
function updateMaxPossibleScore() {
    const conditions = document.querySelectorAll('.condition-item');
    let totalScore = 0;
    
    conditions.forEach(condition => {
        const points = parseInt(condition.querySelector('.condition-points').value) || 0;
        totalScore += points;
    });
    
    document.getElementById('maxPossibleScore').textContent = totalScore;
}

/**
 * Collect conditions from form
 */
function collectConditions() {
    const conditions = [];
    const conditionElements = document.querySelectorAll('.condition-item');
    
    conditionElements.forEach(element => {
        const conditionType = element.querySelector('.condition-type').value;
        const operator = element.querySelector('.condition-operator')?.value || null;
        const value = element.querySelector('.condition-value').value;
        const points = parseInt(element.querySelector('.condition-points').value) || 1;
        
        const config = conditionTypes[conditionType];
        
        conditions.push({
            condition_type: conditionType,
            operator: config.hasOperator ? operator : null,
            value: value,
            points: points
        });
    });
    
    return conditions;
}

/**
 * Add channel as tag
 */
function addChannelTag(channelId, channelName) {
    if (!channelId || channelId === '') {
        return;
    }
    
    const channelIdInt = parseInt(channelId);
    
    // Check if already added
    if (selectedChannelIds.includes(channelIdInt)) {
        return;
    }
    
    // If all channels was selected, clear it first
    if (allChannelsSelected) {
        allChannelsSelected = false;
        document.getElementById('selectedChannelTags').innerHTML = '';
    }
    
    // Add to array
    selectedChannelIds.push(channelIdInt);
    
    // Create tag
    const tag = document.createElement('span');
    tag.className = 'badge bg-primary me-1 mb-1';
    tag.style.cursor = 'pointer';
    tag.dataset.channelId = channelIdInt;
    tag.innerHTML = `${channelName} <i class="fas fa-times ms-1"></i>`;
    tag.onclick = function() {
        removeChannelTag(channelIdInt);
    };
    
    document.getElementById('selectedChannelTags').appendChild(tag);
}

/**
 * Remove channel tag
 */
function removeChannelTag(channelId) {
    // Remove from array
    selectedChannelIds = selectedChannelIds.filter(id => id !== channelId);
    
    // Remove tag element
    const tag = document.querySelector(`#selectedChannelTags [data-channel-id="${channelId}"]`);
    if (tag) {
        tag.remove();
    }
}

/**
 * Collect selected channel IDs
 */
function collectSelectedChannels() {
    return allChannelsSelected ? [] : selectedChannelIds;
}

/**
 * Add channel group as tag
 */
function addChannelGroupTag(groupId, groupName) {
    if (!groupId || groupId === '') {
        return;
    }
    
    const groupIdStr = String(groupId);
    
    // Check if already added
    if (selectedChannelGroupIds.includes(groupIdStr)) {
        return;
    }
    
    // If all channels was selected, clear it first
    if (allChannelsSelected) {
        allChannelsSelected = false;
        document.getElementById('selectedChannelTags').innerHTML = '';
    }
    
    // Add to array
    selectedChannelGroupIds.push(groupIdStr);
    
    // Create tag
    const tag = document.createElement('span');
    tag.className = 'badge bg-success me-1 mb-1';
    tag.style.cursor = 'pointer';
    tag.dataset.groupId = groupIdStr;
    tag.innerHTML = `${groupName} <i class="fas fa-times ms-1"></i>`;
    tag.onclick = function() {
        removeChannelGroupTag(groupIdStr);
    };
    
    document.getElementById('selectedChannelGroupTags').appendChild(tag);
}

/**
 * Remove channel group tag
 */
function removeChannelGroupTag(groupId) {
    // Remove from array
    selectedChannelGroupIds = selectedChannelGroupIds.filter(id => id !== groupId);
    
    // Remove tag element
    const tag = document.querySelector(`#selectedChannelGroupTags [data-group-id="${groupId}"]`);
    if (tag) {
        tag.remove();
    }
}

/**
 * Collect selected channel group IDs
 */
function collectSelectedChannelGroups() {
    return selectedChannelGroupIds;
}

/**
 * Save sorting rule
 */
async function saveSortingRule() {
    const ruleId = document.getElementById('ruleId').value;
    const name = document.getElementById('ruleName').value.trim();
    const description = document.getElementById('ruleDescription').value.trim();
    const channelIds = collectSelectedChannels();
    const channelGroupIds = collectSelectedChannelGroups();
    const conditions = collectConditions();
    const testStreamsBeforeSorting = document.getElementById('testStreamsBeforeSorting').checked;
    const forceRetestOldStreams = document.getElementById('forceRetestOldStreams').checked;
    const retestDaysThresholdValue = document.getElementById('retestDaysThreshold').value;
    const executionOrderValue = document.getElementById('executionOrder').value;
    const executionOrder = executionOrderValue !== '' ? parseInt(executionOrderValue) : null;
    
    if (!name) {
        StreamPlus.showNotification('Rule name is required', 'error');
        return;
    }
    
    if (conditions.length === 0) {
        StreamPlus.showNotification('At least one condition is required', 'warning');
        return;
    }
    
    const ruleData = {
        name: name,
        description: description || null,
        enabled: true,
        channel_ids: channelIds,
        channel_group_ids: channelGroupIds,
        all_channels: allChannelsSelected,
        conditions: conditions,
        test_streams_before_sorting: testStreamsBeforeSorting,
        force_retest_old_streams: testStreamsBeforeSorting && forceRetestOldStreams,
        retest_days_threshold: retestDaysThresholdValue,
        execution_order: executionOrder
    };
    
    try {
        StreamPlus.showLoading();
        
        const method = ruleId ? 'PUT' : 'POST';
        const url = ruleId 
            ? `/api/sorting-rules/${ruleId}` 
            : '/api/sorting-rules';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(ruleData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Error saving rule');
        }
        
        const result = await response.json();
        
        StreamPlus.showNotification(
            ruleId ? 'Rule updated successfully' : 'Rule created successfully',
            'success'
        );
        
        // Close modal and reload page
        bootstrap.Modal.getInstance(document.getElementById('sortingRuleModal')).hide();
        setTimeout(() => location.reload(), 500);
        
    } catch (error) {
        console.error('Error saving rule:', error);
        StreamPlus.showNotification(error.message, 'error');
    } finally {
        StreamPlus.hideLoading();
    }
}

/**
 * Edit sorting rule
 */
async function editSortingRule(ruleId) {
    try {
        StreamPlus.showLoading();
        
        // Update channel groups before editing
        await updateChannelGroups();
        
        const response = await fetch(`/api/sorting-rules/${ruleId}`);
        if (!response.ok) throw new Error('Error loading rule');
        
        const rule = await response.json();
        
        // Populate form
        currentRuleId = ruleId;
        selectedChannelIds = [];
        selectedChannelGroupIds = [];
        allChannelsSelected = rule.all_channels || false;
        document.getElementById('sortingRuleModalTitle').textContent = 'Edit Sorting Rule';
        document.getElementById('ruleId').value = ruleId;
        document.getElementById('ruleName').value = rule.name;
        document.getElementById('ruleDescription').value = rule.description || '';
        document.getElementById('executionOrder').value = rule.execution_order || '';
        
        // Clear tags container
        document.getElementById('selectedChannelTags').innerHTML = '';
        document.getElementById('selectedChannelGroupTags').innerHTML = '';
        
        // Handle all channels selection
        if (allChannelsSelected) {
            const allChannelsTag = document.createElement('span');
            allChannelsTag.className = 'badge bg-warning me-1 mb-1';
            allChannelsTag.style.cursor = 'pointer';
            allChannelsTag.innerHTML = 'All Channels <i class="fas fa-times ms-1"></i>';
            allChannelsTag.onclick = function() {
                allChannelsSelected = false;
                document.getElementById('selectedChannelTags').innerHTML = '';
            };
            document.getElementById('selectedChannelTags').appendChild(allChannelsTag);
        } else {
            // Add channel tags
            rule.channel_ids.forEach(channelId => {
                const channel = allChannels.find(ch => ch.id === channelId);
                if (channel) {
                    selectedChannelIds.push(channelId);
                    const tag = document.createElement('span');
                    tag.className = 'badge bg-primary me-1 mb-1';
                    tag.style.cursor = 'pointer';
                    tag.dataset.channelId = channelId;
                    tag.innerHTML = `${channel.name || 'Channel #' + channelId} <i class="fas fa-times ms-1"></i>`;
                    tag.onclick = function() {
                        removeChannelTag(channelId);
                    };
                    document.getElementById('selectedChannelTags').appendChild(tag);
                }
            });
        }
        
        // Add channel group tags
        rule.channel_group_ids.forEach(groupId => {
            const group = allChannelGroups.find(g => g.id === groupId);
            if (group) {
                selectedChannelGroupIds.push(groupId);
                const tag = document.createElement('span');
                tag.className = 'badge bg-success me-1 mb-1';
                tag.style.cursor = 'pointer';
                tag.dataset.groupId = groupId;
                tag.innerHTML = `${group.name || 'Group #' + groupId} <i class="fas fa-times ms-1"></i>`;
                tag.onclick = function() {
                    removeChannelGroupTag(groupId);
                };
                document.getElementById('selectedChannelGroupTags').appendChild(tag);
            }
        });
        
        // Clear and add conditions
        document.getElementById('conditionsContainer').innerHTML = '';
        conditionCounter = 0;
        
        rule.conditions.forEach(condition => {
            addCondition(condition);
        });
        
        // Set test streams checkbox and retest options
        document.getElementById('testStreamsBeforeSorting').checked = rule.test_streams_before_sorting || false;
        document.getElementById('forceRetestOldStreams').checked = rule.force_retest_old_streams || false;
        document.getElementById('retestDaysThreshold').value = rule.retest_days_threshold || 7;
        
        // Setup event listeners for modal
        setupModalEventListeners();
        
        // Update UI state based on loaded values
        toggleRetestOptions();
        
        updateMaxPossibleScore();
        
        const modal = new bootstrap.Modal(document.getElementById('sortingRuleModal'));
        modal.show();
        
    } catch (error) {
        console.error('Error editing rule:', error);
        StreamPlus.showNotification('Error loading rule', 'error');
    } finally {
        StreamPlus.hideLoading();
    }
}

/**
 * Delete sorting rule
 */
async function deleteSortingRule(ruleId) {
    if (!confirm('Are you sure you want to delete this sorting rule?')) {
        return;
    }
    
    try {
        StreamPlus.showLoading();
        
        const response = await fetch(`/api/sorting-rules/${ruleId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error('Error deleting rule');
        
        StreamPlus.showNotification('Rule deleted successfully', 'success');
        setTimeout(() => location.reload(), 500);
        
    } catch (error) {
        console.error('Error deleting rule:', error);
        StreamPlus.showNotification('Error deleting rule', 'error');
    } finally {
        StreamPlus.hideLoading();
    }
}

/**
 * Toggle sorting rule enabled/disabled
 */
async function toggleSortingRule(ruleId) {
    try {
        const response = await fetch(`/api/sorting-rules/${ruleId}/toggle`, {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Error toggling rule');
        
        const result = await response.json();
        StreamPlus.showNotification(result.message, 'success');
        
    } catch (error) {
        console.error('Error toggling rule:', error);
        StreamPlus.showNotification('Error toggling rule', 'error');
        // Reload to reset toggle state
        setTimeout(() => location.reload(), 500);
    }
}

/**
 * Preview sorting rule
 */
var currentPreviewRuleId = null;

async function previewSortingRule(ruleId) {
    currentPreviewRuleId = ruleId;
    
    try {
        // Get the rule details to find assigned channels
        const ruleResponse = await fetch(`/api/sorting-rules/${ruleId}`);
        if (!ruleResponse.ok) throw new Error('Error loading rule');
        const rule = await ruleResponse.json();
        
        // Get assigned channel IDs from both direct assignments and groups
        const assignedChannelIds = rule.channel_ids || [];
        const assignedGroupIds = rule.channel_group_ids || [];
        const ruleAppliesToAllChannels = rule.all_channels || false;
        
        // If no channels or groups are assigned and not all_channels, show error
        if (assignedChannelIds.length === 0 && assignedGroupIds.length === 0 && !ruleAppliesToAllChannels) {
            showAlert('This rule has no assigned channels. Please assign at least one channel.');
            return;
        }
        
        // Get all channels to find names
        const channelsResponse = await fetch('/api/channels');
        if (!channelsResponse.ok) throw new Error('Error loading channels');
        const allChannels = await channelsResponse.json();
        
        // Get channel groups if needed
        let allChannelGroups = [];
        if (assignedGroupIds.length > 0) {
            const groupsResponse = await fetch('/api/channel-groups');
            if (!groupsResponse.ok) throw new Error('Error loading channel groups');
            allChannelGroups = await groupsResponse.json();
        }
        
        // Collect all assigned channels (from direct assignment and groups)
        let assignedChannels = [];
        
        // If rule applies to all channels, use all available channels
        if (ruleAppliesToAllChannels) {
            assignedChannels = allChannels;
        } else {
            // Add directly assigned channels
            if (assignedChannelIds.length > 0) {
                assignedChannels = assignedChannels.concat(
                    allChannels.filter(ch => assignedChannelIds.includes(ch.id))
                );
            }
            
            // Add channels from assigned groups
            if (assignedGroupIds.length > 0) {
                for (const groupId of assignedGroupIds) {
                    const group = allChannelGroups.find(g => g.id === groupId);
                    if (group && group.channel_ids) {
                        const groupChannels = allChannels.filter(ch => group.channel_ids.includes(ch.id));
                        assignedChannels = assignedChannels.concat(groupChannels);
                    }
                }
            }
            // Remove duplicates
            assignedChannels = assignedChannels.filter((channel, index, self) => 
                index === self.findIndex(c => c.id === channel.id)
            );
            
            if (assignedChannels.length === 0) {
                showAlert('No channels found in the assigned groups. Please check your group assignments.');
                return;
            }
        }
        
        // If only one channel is assigned, load preview directly without showing selector
        if (assignedChannels.length === 1) {
            const channelId = assignedChannels[0].id;
            const channelName = assignedChannels[0].name || `Channel #${channelId}`;
            
            // Show modal with fixed channel
            const modal = new bootstrap.Modal(document.getElementById('previewModal'));
            const channelSelectContainer = document.getElementById('previewChannelSelectContainer');
            channelSelectContainer.innerHTML = `
                <div class="alert alert-info mb-3">
                    <strong>Channel:</strong> ${channelName}
                </div>
            `;
            
            // Set up apply button
            document.getElementById('applyFromPreviewBtn').onclick = () => {
                executeRuleOnChannel(ruleId, channelId);
                modal.hide();
            };
            
            modal.show();
            
            // Load preview immediately
            loadPreviewForChannel(ruleId, channelId);
        } else {
            // Multiple channels - show selector
            const modal = new bootstrap.Modal(document.getElementById('previewModal'));
            const channelSelectContainer = document.getElementById('previewChannelSelectContainer');
            
            // Build channel selector with only assigned channels
            const ruleScopeText = ruleAppliesToAllChannels ? 
                'This rule applies to ALL channels' : 
                `This rule applies to ${assignedChannels.length} assigned channel${assignedChannels.length !== 1 ? 's' : ''}`;
            
            let selectHtml = `
                <div class="mb-3">
                    <div class="alert alert-info mb-2">
                        <i class="fas fa-info-circle"></i> ${ruleScopeText}
                    </div>
                    <label class="form-label">Select Channel to Preview</label>
                    <select class="form-select" id="previewChannelSelect">
                        <option value="">Choose a channel...</option>
            `;
            
            assignedChannels.forEach(channel => {
                selectHtml += `<option value="${channel.id}">${channel.name || 'Channel #' + channel.id}</option>`;
            });
            
            selectHtml += `
                    </select>
                </div>
            `;
            
            channelSelectContainer.innerHTML = selectHtml;
            
            // Set up event listener for channel change
            document.getElementById('previewChannelSelect').addEventListener('change', () => {
                const channelId = document.getElementById('previewChannelSelect').value;
                if (channelId) {
                    loadPreviewForChannel(ruleId, parseInt(channelId));
                }
            });
            
            // Set up apply button
            document.getElementById('applyFromPreviewBtn').onclick = () => {
                const channelId = document.getElementById('previewChannelSelect').value;
                if (channelId) {
                    executeRuleOnChannel(ruleId, parseInt(channelId));
                    modal.hide();
                } else {
                    showAlert('Please select a channel first');
                }
            };
            
            modal.show();
            
            // Clear previous results
            document.getElementById('previewResults').innerHTML = '<p class="text-muted">Please select a channel</p>';
        }
        
    } catch (error) {
        console.error('Error loading preview:', error);
        showAlert('Error loading preview: ' + error.message, 'danger');
    }
}

async function loadPreviewForChannel(ruleId, channelId) {
    const resultsDiv = document.getElementById('previewResults');
    
    if (!channelId) {
        resultsDiv.innerHTML = '<p class="text-muted">Please select a channel</p>';
        return;
    }
    
    try {
        resultsDiv.innerHTML = '<div class="text-center"><div class="spinner-border"></div></div>';
        
        const response = await fetch(`/api/sorting-rules/${ruleId}/preview`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ channel_id: parseInt(channelId) })
        });
        
        if (!response.ok) throw new Error('Error loading preview');
        
        const preview = await response.json();
        
        // Display preview results
        let html = `
            <div class="alert alert-info">
                <strong>Total Streams:</strong> ${preview.total_streams}<br>
                <strong>Conditions:</strong> ${preview.conditions_count}<br>
                <strong>Max Possible Score:</strong> ${preview.max_possible_score} points
            </div>
            
            <h6>Score Distribution:</h6>
            <ul class="list-group mb-3">
        `;
        
        const sortedScores = Object.keys(preview.score_distribution)
            .map(Number)
            .sort((a, b) => b - a);
            
        sortedScores.forEach(score => {
            const count = preview.score_distribution[score];
            html += `
                <li class="list-group-item d-flex justify-content-between">
                    <span><strong>${score} points:</strong></span>
                    <span>${count} stream(s)</span>
                </li>
            `;
        });
        
        html += `</ul><h6>Sorted Streams (Top 10):</h6><div class="list-group">`;
        
        preview.sorted_streams.slice(0, 10).forEach((stream, index) => {
            // Format M3U source name
            let m3uSourceName = 'Unknown';
            if (stream.m3u_account) {
                const m3uAccount = m3uAccounts.find(acc => acc.id === parseInt(stream.m3u_account));
                m3uSourceName = m3uAccount ? m3uAccount.name : `M3U Account #${stream.m3u_account}`;
            }
            
            html += `
                <div class="list-group-item">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>#${index + 1}</strong> - ${stream.name || 'Stream #' + stream.id}
                            <br><small class="text-muted">${m3uSourceName}</small>
                        </div>
                        <span class="badge bg-primary">${stream.score} pts</span>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        
        if (preview.sorted_streams.length > 10) {
            html += `<p class="text-muted mt-2">... and ${preview.sorted_streams.length - 10} more streams</p>`;
        }
        
        resultsDiv.innerHTML = html;
        
    } catch (error) {
        console.error('Error loading preview:', error);
        resultsDiv.innerHTML = `<div class="alert alert-danger">Error loading preview: ${error.message}</div>`;
    }
}

/**
 * Execute sorting rule
 */
async function executeSortingRule(ruleId) {
    if (!confirm('Execute this sorting rule on its assigned channels?')) {
        return;
    }
    
    try {
        StreamPlus.showLoading();
        
        // First, get rule details to check if testing is required
        const ruleResponse = await fetch(`/api/sorting-rules/${ruleId}`);
        if (!ruleResponse.ok) {
            throw new Error('Failed to fetch rule details');
        }
        const rule = await ruleResponse.json();
        
        // Determine if we should use SSE (streaming) mode
        const useStream = rule && rule.test_streams_before_sorting === true;
        
        // Execute the rule
        const response = await fetch(`/api/sorting-rules/${ruleId}/execute`, {
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
            StreamPlus.hideLoading();
            showExecutionProgressModal(ruleId, result.execution_id);
        } else {
            // Normal synchronous execution completed - show success message
            let detailMessage = result.message;
            if (result.processed_channels && result.processed_channels.length > 0) {
                detailMessage += '\n\nChannels processed:';
                result.processed_channels.forEach(ch => {
                    detailMessage += `\n- ${ch.channel_name}: ${ch.sorted_count} streams sorted`;
                });
            }
            if (result.errors && result.errors.length > 0) {
                detailMessage += '\n\nErrors:\n' + result.errors.join('\n');
            }
            
            StreamPlus.showNotification(detailMessage, 'success');
            StreamPlus.hideLoading();
        }
        
    } catch (error) {
        console.error('Error executing rule:', error);
        StreamPlus.showNotification(error.message, 'error');
        StreamPlus.hideLoading();
    }
}

/**
 * Execute sorting rule on a specific channel
 */
async function executeRuleOnChannel(ruleId, channelId) {
    if (!confirm(`Execute this sorting rule on channel ${channelId}?`)) {
        return;
    }
    
    try {
        StreamPlus.showLoading();
        
        // First, get rule details to check if testing is required
        const ruleResponse = await fetch(`/api/sorting-rules/${ruleId}`);
        if (!ruleResponse.ok) {
            throw new Error('Failed to fetch rule details');
        }
        const rule = await ruleResponse.json();
        
        // Determine if we should use SSE (streaming) mode
        const useStream = rule && rule.test_streams_before_sorting === true;
        
        // Execute the rule on the specific channel
        const response = await fetch(`/api/sorting-rules/${ruleId}/execute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                channel_id: channelId,
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
            StreamPlus.hideLoading();
            showExecutionProgressModal(ruleId, result.execution_id);
        } else {
            // Normal synchronous execution completed - show success message
            StreamPlus.hideLoading();
            StreamPlus.showNotification(result.message, 'success');
            
            // Reload the page to reflect changes
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        }
        
    } catch (error) {
        console.error('Error executing rule on channel:', error);
        StreamPlus.showNotification(error.message, 'error');
        StreamPlus.hideLoading();
    }
}

/**
 * Toggle retest options based on test streams checkbox
 */
/**
 * Toggle retest options based on test streams checkbox
 */
function toggleRetestOptions() {
    const testEnabled = document.getElementById('testStreamsBeforeSorting').checked;
    const forceRetestCheckbox = document.getElementById('forceRetestOldStreams');
    const retestDaysInput = document.getElementById('retestDaysThreshold');
    
    if (forceRetestCheckbox && retestDaysInput) {
        forceRetestCheckbox.disabled = !testEnabled;
        // El threshold siempre está habilitado si el testeo está habilitado
        retestDaysInput.disabled = !testEnabled;
        
        if (!testEnabled) {
            forceRetestCheckbox.checked = false;
        }
    }
}

/**
 * Toggle days threshold input based on force retest checkbox
 */
function toggleDaysThreshold() {
    const testEnabled = document.getElementById('testStreamsBeforeSorting').checked;
    const retestDaysInput = document.getElementById('retestDaysThreshold');
    
    if (retestDaysInput) {
        // El threshold siempre está habilitado si el testeo está habilitado
        retestDaysInput.disabled = !testEnabled;
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
    
    if (forceRetestCheckbox) {
        // Remove existing listeners to avoid duplicates
        forceRetestCheckbox.removeEventListener('change', toggleDaysThreshold);
        forceRetestCheckbox.addEventListener('change', toggleDaysThreshold);
    }
    
    // Setup channel search functionality
    setupChannelSearch();
    setupChannelGroupSearch();
}

/**
 * Setup channel search functionality
 */
function setupChannelSearch() {
    const searchInput = document.getElementById('channelSearch');
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
    });
    
    // Hide dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.classList.remove('show');
        }
    });
    
    // Handle Enter key to add channel
    searchInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            const firstItem = dropdown.querySelector('.dropdown-item:not(.text-muted)');
            if (firstItem) {
                firstItem.click();
            }
        }
    });
}

/**
 * Filter and display channels in dropdown
 */
function filterChannels(searchTerm) {
    const dropdown = document.getElementById('channelDropdown');
    const searchInput = document.getElementById('channelSearch');
    
    if (!dropdown) return;
    
    // Filter channels
    const filtered = allChannels.filter(channel => {
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
            addChannelTag(channel.id, channel.name || `Channel #${channel.id}`);
            searchInput.value = '';
            dropdown.classList.remove('show');
        });
        
        dropdown.appendChild(item);
    });
}

/**
 * Setup channel group search functionality
 */
function setupChannelGroupSearch() {
    const searchInput = document.getElementById('channelGroupSearch');
    const dropdown = document.getElementById('channelGroupDropdown');
    
    if (!searchInput || !dropdown) return;
    
    // Show dropdown on focus
    searchInput.addEventListener('focus', function() {
        filterChannelGroups('');
        dropdown.classList.add('show');
    });
    
    // Filter channel groups on input
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        filterChannelGroups(searchTerm);
        dropdown.classList.add('show');
    });
    
    // Hide dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.classList.remove('show');
        }
    });
    
    // Handle Enter key to add channel group
    searchInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            const firstItem = dropdown.querySelector('.dropdown-item:not(.text-muted)');
            if (firstItem) {
                firstItem.click();
            }
        }
    });
}

/**
 * Filter and display channel groups in dropdown
 */
function filterChannelGroups(searchTerm) {
    const dropdown = document.getElementById('channelGroupDropdown');
    const searchInput = document.getElementById('channelGroupSearch');
    
    if (!dropdown) return;
    
    // Filter channel groups
    const filtered = allChannelGroups.filter(group => {
        // Only show groups that have channels
        if (!group.channel_ids || group.channel_ids.length === 0) {
            return false;
        }
        
        const name = (group.name || '').toLowerCase();
        const id = String(group.id).toLowerCase();
        return name.includes(searchTerm) || id.includes(searchTerm);
    });
    
    // Clear dropdown
    dropdown.innerHTML = '';
    
    if (filtered.length === 0) {
        const noResults = document.createElement('div');
        noResults.className = 'dropdown-item text-muted';
        noResults.textContent = 'No channel groups found';
        dropdown.appendChild(noResults);
        return;
    }
    
    // Add filtered channel groups
    filtered.forEach(group => {
        const item = document.createElement('a');
        item.className = 'dropdown-item';
        item.href = '#';
        item.style.cursor = 'pointer';
        
        // Create channel group display
        const displayHtml = `
            <div class="d-flex align-items-center">
                <i class="fas fa-layer-group text-primary me-2"></i>
                <span>${group.name || 'Group #' + group.id}</span>
                <small class="text-muted ms-2">(ID: ${group.id})</small>
                <small class="text-muted ms-2">(${group.channel_ids ? group.channel_ids.length : 0} channels)</small>
            </div>
        `;
        
        item.innerHTML = displayHtml;
        
        // Handle channel group selection
        item.addEventListener('click', function(e) {
            e.preventDefault();
            addChannelGroupTag(group.id, group.name || `Group #${group.id}`);
            searchInput.value = '';
            dropdown.classList.remove('show');
        });
        
        dropdown.appendChild(item);
    });
}

/**
 * Update channel groups from server
 */
async function updateChannelGroups() {
    try {
        const response = await fetch('/api/channel-groups');
        if (!response.ok) throw new Error('Error loading channel groups');
        
        const groups = await response.json();
        // Update the global variable
        window.allChannelGroups = groups;
        
        console.log(`Updated ${groups.length} channel groups from server`);
        return groups;
    } catch (error) {
        console.error('Error updating channel groups:', error);
        throw error;
    }
}

/**
 * Add all available channels to the current rule
 */
function addAllChannels() {
    if (!allChannels || allChannels.length === 0) {
        StreamPlus.showNotification('No channels available', 'warning');
        return;
    }
    
    // Clear existing channel tags
    document.getElementById('selectedChannelTags').innerHTML = '';
    selectedChannelIds = [];
    
    // Set all channels flag
    allChannelsSelected = true;
    
    // Create special "All channels" tag
    const allChannelsTag = document.createElement('span');
    allChannelsTag.className = 'badge bg-warning me-1 mb-1';
    allChannelsTag.style.cursor = 'pointer';
    allChannelsTag.innerHTML = 'All Channels <i class="fas fa-times ms-1"></i>';
    allChannelsTag.onclick = function() {
        allChannelsSelected = false;
        document.getElementById('selectedChannelTags').innerHTML = '';
    };
    
    document.getElementById('selectedChannelTags').appendChild(allChannelsTag);
    
    StreamPlus.showNotification('Rule will apply to all channels', 'success');
}

/**
 * Execute all sorting rules
 */
async function executeAllSortingRules() {
    try {
        StreamPlus.showLoading();
        
        const requestData = { stream: true };
        console.log('Sending request data:', requestData);
        console.log('JSON stringified:', JSON.stringify(requestData));
        
        // Start execution
        const response = await fetch('/api/sorting-rules/execute-all', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        console.log('Response status:', response.status);
        console.log('Response status text:', response.statusText);
        console.log('Response headers:', Object.fromEntries(response.headers.entries()));
        console.log('Response ok:', response.ok);
        
        if (!response.ok) {
            let errorMessage = 'Error starting execution';
            try {
                const error = await response.json();
                errorMessage = error.error || errorMessage;
            } catch (e) {
                // If response is not JSON, use status text
                const responseText = await response.text();
                console.log('Response text:', responseText);
                errorMessage = `HTTP ${response.status}: ${response.statusText}`;
            }
            throw new Error(errorMessage);
        }
        
        const result = await response.json();
        
        if (result.stream && result.execution_id) {
            // Show progress modal for streaming execution
            showAllRulesExecutionModal(result.execution_id);
        } else {
            // Simple execution completed
            StreamPlus.showNotification(result.message, 'success');
        }
        
    } catch (error) {
        console.error('Error executing all rules:', error);
        StreamPlus.showNotification(error.message, 'error');
    } finally {
        StreamPlus.hideLoading();
    }
}

/**
 * Show modal for executing all rules with progress
 */
function showAllRulesExecutionModal(executionId) {
    // Create modal HTML
    const modalHtml = `
        <div class="modal fade" id="allRulesExecutionModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-play text-success me-2"></i>
                            Executing All Sorting Rules
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div id="allRulesExecutionProgress" class="mb-3">
                            <div class="text-center">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">Loading...</span>
                                </div>
                                <p class="mt-2">Starting execution...</p>
                            </div>
                        </div>
                        <div id="allRulesExecutionLog" class="border rounded p-3 bg-light" style="max-height: 400px; overflow-y: auto; font-family: monospace; font-size: 0.875rem;">
                            <!-- Execution log will be appended here -->
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if present
    const existingModal = document.getElementById('allRulesExecutionModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('allRulesExecutionModal'));
    modal.show();
    
    // Start listening for progress updates
    listenForAllRulesExecutionProgress(executionId);
}

/**
 * Listen for execution progress updates
 */
function listenForAllRulesExecutionProgress(executionId) {
    const eventSource = new EventSource(`/api/sorting-rules/execute-all/stream?execution_id=${executionId}`);
    const progressDiv = document.getElementById('allRulesExecutionProgress');
    const logDiv = document.getElementById('allRulesExecutionLog');
    
    eventSource.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            
            if (data.type === 'start') {
                progressDiv.innerHTML = `
                    <div class="alert alert-info">
                        <strong>Starting execution:</strong> ${data.message}
                    </div>
                `;
                logDiv.innerHTML += `<div class="text-info">[START] ${data.message}</div>`;
                
            } else if (data.type === 'rule_start') {
                progressDiv.innerHTML = `
                    <div class="alert alert-primary">
                        <strong>Executing Rule ${data.rule_index}/${data.total_rules}:</strong> ${data.rule_name}
                        <div class="progress mt-2">
                            <div class="progress-bar" role="progressbar" style="width: ${(data.rule_index-1)/data.total_rules*100}%"></div>
                        </div>
                    </div>
                `;
                logDiv.innerHTML += `<div class="text-primary fw-bold">[RULE ${data.rule_index}/${data.total_rules}] Starting: ${data.rule_name}</div>`;
                logDiv.scrollTop = logDiv.scrollHeight;
                
            } else if (data.type === 'rule_progress') {
                progressDiv.innerHTML = `
                    <div class="alert alert-primary">
                        <strong>Executing Rule ${data.rule_index}/${data.total_rules}:</strong> ${data.rule_name}
                        <div class="progress mt-2">
                            <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" 
                                 style="width: ${data.progress}%"></div>
                        </div>
                        <small class="text-muted">${data.message}</small>
                    </div>
                `;
                logDiv.innerHTML += `<div class="text-muted">${data.message}</div>`;
                logDiv.scrollTop = logDiv.scrollHeight;
                
            } else if (data.type === 'rule_complete') {
                logDiv.innerHTML += `<div class="text-success">[COMPLETE] Rule ${data.rule_index}/${data.total_rules}: ${data.rule_name} - ${data.channels_sorted} channels sorted</div>`;
                logDiv.scrollTop = logDiv.scrollHeight;
                
            } else if (data.type === 'complete') {
                progressDiv.innerHTML = `
                    <div class="alert alert-success">
                        <strong>Execution Complete!</strong><br>
                        ${data.rules_executed} rules executed, ${data.total_channels_sorted} channels sorted
                    </div>
                `;
                logDiv.innerHTML += `<div class="text-success fw-bold">[FINISHED] All rules executed successfully</div>`;
                logDiv.scrollTop = logDiv.scrollHeight;
                
                // Close EventSource after a delay
                setTimeout(() => eventSource.close(), 2000);
                
            } else if (data.type === 'error') {
                progressDiv.innerHTML = `
                    <div class="alert alert-danger">
                        <strong>Error:</strong> ${data.message}
                    </div>
                `;
                logDiv.innerHTML += `<div class="text-danger">[ERROR] ${data.message}</div>`;
                logDiv.scrollTop = logDiv.scrollHeight;
                eventSource.close();
                
            } else if (data.type === 'keepalive') {
                // Keep-alive message, ignore
            }
            
        } catch (e) {
            console.error('Error parsing SSE data:', e);
        }
    };
    
    eventSource.onerror = function(error) {
        console.error('EventSource error:', error);
        progressDiv.innerHTML = `
            <div class="alert alert-warning">
                <strong>Connection lost</strong> - Refresh the page to check execution status
            </div>
        `;
        eventSource.close();
    };
}
