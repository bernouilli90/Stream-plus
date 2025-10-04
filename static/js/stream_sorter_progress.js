/**
 * Stream Sorter - SSE Progress Functions
 * Handles real-time execution progress via Server-Sent Events
 */

let currentEventSource = null;
let totalStreamsToTest = 0;
let currentStreamsTested = 0;
let totalChannels = 0;
let currentChannel = 0;

/**
 * Show execution progress modal and connect to SSE
 */
function showExecutionProgressModal(ruleId, executionId) {
    // Reset state
    totalStreamsToTest = 0;
    currentStreamsTested = 0;
    totalChannels = 0;
    currentChannel = 0;
    
    // Reset UI
    document.getElementById('executionLog').innerHTML = '';
    document.getElementById('executionSummary').style.display = 'none';
    document.getElementById('progressLabel').textContent = 'Connecting...';
    document.getElementById('progressPercent').textContent = '0%';
    document.getElementById('executionProgressBar').style.width = '0%';
    document.getElementById('closeProgressBtn').disabled = true;
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('executionProgressModal'));
    modal.show();
    
    // Connect to SSE
    connectToExecutionStream(ruleId, executionId);
}

/**
 * Connect to Server-Sent Events stream
 */
function connectToExecutionStream(ruleId, executionId) {
    // Close any existing connection
    if (currentEventSource) {
        currentEventSource.close();
    }
    
    // Create new EventSource
    const url = `/api/sorting-rules/${ruleId}/execute-stream?execution_id=${executionId}`;
    currentEventSource = new EventSource(url);
    
    currentEventSource.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            handleExecutionMessage(data);
        } catch (e) {
            console.error('Error parsing SSE message:', e);
        }
    };
    
    currentEventSource.onerror = function(error) {
        console.error('SSE error:', error);
        addLogLine('Connection error. Retrying...', 'error');
        
        // Close connection
        if (currentEventSource) {
            currentEventSource.close();
            currentEventSource = null;
        }
    };
}

/**
 * Handle execution progress message
 */
function handleExecutionMessage(data) {
    switch (data.type) {
        case 'start':
            totalChannels = data.total_channels || 1;
            currentChannel = 0;
            addLogLine(data.message, 'info');
            updateProgress(0, data.message);
            break;
            
        case 'channel_start':
            currentChannel = data.channel_index || 1;
            addLogLine(`\n📺 ${data.message}`, 'channel');
            updateProgress(
                ((currentChannel - 1) / totalChannels) * 100,
                `Channel ${currentChannel}/${totalChannels}`
            );
            break;
            
        case 'info':
            addLogLine(data.message, 'info');
            break;
            
        case 'test_start':
            totalStreamsToTest = data.total_streams || 0;
            currentStreamsTested = 0;
            addLogLine(`\n🔍 ${data.message}`, 'test');
            break;
            
        case 'test_progress':
            currentStreamsTested = data.current || 0;
            addLogLine(data.message, 'test');
            
            // Calculate progress within channel
            const channelProgress = (currentChannel - 1) / totalChannels;
            const testProgress = (currentStreamsTested / totalStreamsToTest) / totalChannels;
            const totalProgress = (channelProgress + testProgress) * 100;
            
            updateProgress(
                totalProgress,
                `Testing ${currentStreamsTested}/${totalStreamsToTest}`
            );
            break;
            
        case 'test_success':
            addLogLine(data.message, 'success');
            break;
            
        case 'test_fail':
            addLogLine(data.message, 'error');
            break;
            
        case 'sorting':
            addLogLine(`\n🔄 ${data.message}`, 'info');
            break;
            
        case 'updating':
            addLogLine(`💾 ${data.message}`, 'info');
            break;
            
        case 'channel_complete':
            addLogLine(data.message, 'success');
            updateProgress(
                (currentChannel / totalChannels) * 100,
                `Channel ${currentChannel}/${totalChannels} complete`
            );
            break;
            
        case 'error':
            addLogLine(`❌ ${data.message}`, 'error');
            break;
            
        case 'complete':
            handleExecutionComplete(data);
            break;
            
        case 'keepalive':
            // Just a keepalive, ignore
            break;
            
        default:
            console.log('Unknown message type:', data.type, data);
    }
}

/**
 * Handle execution completion
 */
function handleExecutionComplete(data) {
    // Close SSE connection
    if (currentEventSource) {
        currentEventSource.close();
        currentEventSource = null;
    }
    
    // Update progress bar to 100%
    updateProgress(100, 'Complete');
    
    // Add final log message
    addLogLine(`\n${'='.repeat(60)}`, 'info');
    addLogLine(data.message, data.success ? 'success' : 'error');
    
    // Show summary
    const summaryDiv = document.getElementById('executionSummary');
    const resultDiv = document.getElementById('executionResult');
    
    summaryDiv.style.display = 'block';
    resultDiv.className = data.success ? 'alert alert-success' : 'alert alert-danger';
    
    let summaryHTML = `<h6>${data.message}</h6>`;
    
    if (data.processed_channels && data.processed_channels.length > 0) {
        summaryHTML += '<ul class="mb-0 mt-2">';
        data.processed_channels.forEach(ch => {
            summaryHTML += `<li><strong>${ch.channel_name}</strong>: ${ch.sorted_count} streams sorted`;
            if (ch.tested_count > 0) {
                summaryHTML += ` (tested: ${ch.tested_count}, failed: ${ch.failed_tests})`;
            }
            summaryHTML += '</li>';
        });
        summaryHTML += '</ul>';
    }
    
    if (data.errors && data.errors.length > 0) {
        summaryHTML += '<div class="mt-2"><strong>Errors:</strong><ul class="mb-0">';
        data.errors.forEach(err => {
            summaryHTML += `<li>${err}</li>`;
        });
        summaryHTML += '</ul></div>';
    }
    
    resultDiv.innerHTML = summaryHTML;
    
    // Enable close button
    document.getElementById('closeProgressBtn').disabled = false;
    
    // Change modal title
    document.querySelector('#executionProgressModal .modal-title').innerHTML = 
        '<i class="fas fa-check-circle text-success"></i> Execution Complete';
}

/**
 * Add line to execution log
 */
function addLogLine(message, type = 'info') {
    const logDiv = document.getElementById('executionLog');
    const timestamp = new Date().toLocaleTimeString();
    
    let color = 'text-light';
    let icon = '';
    
    switch (type) {
        case 'error':
            color = 'text-danger';
            icon = '❌';
            break;
        case 'success':
            color = 'text-success';
            icon = '✓';
            break;
        case 'warning':
            color = 'text-warning';
            icon = '⚠️';
            break;
        case 'channel':
            color = 'text-info fw-bold';
            icon = '📺';
            break;
        case 'test':
            color = 'text-primary';
            icon = '🔍';
            break;
        default:
            color = 'text-light';
    }
    
    const line = document.createElement('div');
    line.className = `log-line ${color}`;
    line.innerHTML = `<span class="text-muted">[${timestamp}]</span> ${message}`;
    
    logDiv.appendChild(line);
    
    // Auto-scroll to bottom
    logDiv.parentElement.scrollTop = logDiv.parentElement.scrollHeight;
}

/**
 * Update progress bar
 */
function updateProgress(percent, label) {
    const progressBar = document.getElementById('executionProgressBar');
    const progressLabel = document.getElementById('progressLabel');
    const progressPercent = document.getElementById('progressPercent');
    
    const roundedPercent = Math.round(percent);
    
    progressBar.style.width = `${roundedPercent}%`;
    progressBar.setAttribute('aria-valuenow', roundedPercent);
    
    if (label) {
        progressLabel.textContent = label;
    }
    
    progressPercent.textContent = `${roundedPercent}%`;
    
    // Change color based on progress
    progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated';
    if (roundedPercent >= 100) {
        progressBar.classList.add('bg-success');
    } else if (roundedPercent >= 50) {
        progressBar.classList.add('bg-info');
    }
}

/**
 * Clear execution log
 */
function clearExecutionLog() {
    document.getElementById('executionLog').innerHTML = '';
}

// Close SSE connection when modal is closed
document.addEventListener('DOMContentLoaded', function() {
    const progressModal = document.getElementById('executionProgressModal');
    if (progressModal) {
        progressModal.addEventListener('hidden.bs.modal', function() {
            if (currentEventSource) {
                currentEventSource.close();
                currentEventSource = null;
            }
        });
    }
});
