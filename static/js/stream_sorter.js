/**
 * Stream Sorter JavaScript
 * Handles sorting rules management with scoring system
 */

let currentRuleId = null;
let conditionCounter = 0;
let selectedChannelIds = [];

// Condition type configurations
const conditionTypes = {
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
        valueType: 'text',
        operators: ['>', '>=', '<', '<=', '=='],
        placeholder: '1920 or 1920x1080'
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
    currentRuleId = null;
    selectedChannelIds = [];
    document.getElementById('sortingRuleModalTitle').textContent = 'New Sorting Rule';
    document.getElementById('sortingRuleForm').reset();
    document.getElementById('ruleId').value = '';
    document.getElementById('conditionsContainer').innerHTML = '';
    document.getElementById('selectedChannelTags').innerHTML = '';
    conditionCounter = 0;
    updateMaxPossibleScore();
    
    const modal = new bootstrap.Modal(document.getElementById('sortingRuleModal'));
    modal.show();
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
            options = config.values.map(val => 
                `<option value="${val}">${val.toUpperCase()}</option>`
            ).join('');
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
function addChannelTag() {
    const select = document.getElementById('channelSelect');
    const channelId = select.value;
    const channelName = select.options[select.selectedIndex].dataset.name;
    
    if (!channelId || channelId === '') {
        return;
    }
    
    const channelIdInt = parseInt(channelId);
    
    // Check if already added
    if (selectedChannelIds.includes(channelIdInt)) {
        select.value = '';
        return;
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
    
    // Reset select
    select.value = '';
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
    return selectedChannelIds;
}

/**
 * Save sorting rule
 */
async function saveSortingRule() {
    const ruleId = document.getElementById('ruleId').value;
    const name = document.getElementById('ruleName').value.trim();
    const description = document.getElementById('ruleDescription').value.trim();
    const channelIds = collectSelectedChannels();
    const conditions = collectConditions();
    
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
        channel_group_ids: [],
        conditions: conditions
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
        
        const response = await fetch(`/api/sorting-rules/${ruleId}`);
        if (!response.ok) throw new Error('Error loading rule');
        
        const rule = await response.json();
        
        // Populate form
        currentRuleId = ruleId;
        selectedChannelIds = [];
        document.getElementById('sortingRuleModalTitle').textContent = 'Edit Sorting Rule';
        document.getElementById('ruleId').value = ruleId;
        document.getElementById('ruleName').value = rule.name;
        document.getElementById('ruleDescription').value = rule.description || '';
        
        // Clear tags container
        document.getElementById('selectedChannelTags').innerHTML = '';
        
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
        
        // Clear and add conditions
        document.getElementById('conditionsContainer').innerHTML = '';
        conditionCounter = 0;
        
        rule.conditions.forEach(condition => {
            addCondition(condition);
        });
        
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
let currentPreviewRuleId = null;

async function previewSortingRule(ruleId) {
    currentPreviewRuleId = ruleId;
    const modal = new bootstrap.Modal(document.getElementById('previewModal'));
    modal.show();
    
    // Set up event listener for channel change
    document.getElementById('previewChannelSelect').addEventListener('change', () => {
        loadPreview(ruleId);
    });
    
    // Set up event listener for apply button
    document.getElementById('applyFromPreviewBtn').onclick = () => {
        const channelId = document.getElementById('previewChannelSelect').value;
        executeRuleOnChannel(ruleId, parseInt(channelId));
        modal.hide();
    };
    
    // Load initial preview
    loadPreview(ruleId);
}

async function loadPreview(ruleId) {
    const channelId = document.getElementById('previewChannelSelect').value;
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
            html += `
                <div class="list-group-item">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>#${index + 1}</strong> - ${stream.name || 'Stream #' + stream.id}
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
    currentPreviewRuleId = ruleId;
    const modal = new bootstrap.Modal(document.getElementById('executeModal'));
    modal.show();
    
    // Set up event listener for execute button
    document.getElementById('confirmExecuteBtn').onclick = () => {
        const channelId = document.getElementById('executeChannelSelect').value;
        if (channelId) {
            executeRuleOnChannel(ruleId, parseInt(channelId));
            modal.hide();
        }
    };
}

async function executeRuleOnChannel(ruleId, channelId) {
    try {
        StreamPlus.showLoading();
        
        const response = await fetch(`/api/sorting-rules/${ruleId}/execute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ channel_id: channelId })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Error executing rule');
        }
        
        const result = await response.json();
        StreamPlus.showNotification(result.message, 'success');
        
    } catch (error) {
        console.error('Error executing rule:', error);
        StreamPlus.showNotification(error.message, 'error');
    } finally {
        StreamPlus.hideLoading();
    }
}

/**
 * Remove channel from rule
 */
async function removeChannelFromRule(ruleId, channelId) {
    try {
        // Get current rule
        const response = await fetch(`/api/sorting-rules/${ruleId}`);
        if (!response.ok) throw new Error('Error loading rule');
        
        const rule = await response.json();
        
        // Remove channel from list
        rule.channel_ids = rule.channel_ids.filter(id => id !== channelId);
        
        // Update rule
        const updateResponse = await fetch(`/api/sorting-rules/${ruleId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(rule)
        });
        
        if (!updateResponse.ok) throw new Error('Error updating rule');
        
        // Reload page to reflect changes
        location.reload();
        
    } catch (error) {
        console.error('Error removing channel:', error);
        StreamPlus.showNotification('Error removing channel', 'error');
    }
}

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    console.log('Stream Sorter page loaded');
    console.log('M3U Accounts:', m3uAccounts);
    console.log('Channels:', allChannels);
});
