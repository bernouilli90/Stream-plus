/**
 * Auto Assignment - SSE Progress Functions
 * Handles real-time execution progress via Server-Sent Events
 */

var currentEventSource = null;
var totalStreamsToTest = 0;
var currentStreamsTested = 0;

/**
 * Show execution progress modal and connect to SSE
 */
function showExecutionProgressModal(ruleId, executionId) {
    // Reset state
    totalStreamsToTest = 0;
    currentStreamsTested = 0;
    
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
    const url = `/api/auto-assign-rules/${ruleId}/execute-stream?execution_id=${executionId}`;
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
            addLogLine(data.message, 'info');
            updateProgress(0, data.message);
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
            
            // Calculate progress (0-100% based only on testing)
            const testProgress = totalStreamsToTest > 0 
                ? (currentStreamsTested / totalStreamsToTest) * 100 
                : 0;
            updateProgress(
                testProgress,
                `Tested ${currentStreamsTested}/${totalStreamsToTest} streams`
            );
            break;
            
        case 'test_success':
            // Show stream statistics if available
            let message = data.message;
            if (data.statistics) {
                const stats = data.statistics;
                const bitrate = stats.ffmpeg_output_bitrate;
                const resolution = stats.resolution || 'Unknown';
                const codec = stats.video_codec || 'Unknown';
                const fps = stats.source_fps ? `${stats.source_fps.toFixed(1)}fps` : 'Unknown';
                const pixelFormat = stats.pixel_format || 'Unknown';
                
                if (bitrate) {
                    message += `\n    📊 Stats: ${resolution} | ${codec} | ${bitrate.toFixed(0)}kbps | ${fps} | ${pixelFormat}`;
                }
            }
            addLogLine(message, 'success');
            break;
            
        case 'test_fail':
            addLogLine(data.message, 'error');
            break;
            
        case 'matching':
            addLogLine(`\n🔍 ${data.message}`, 'info');
            // Don't update progress bar, just log
            break;
            
        case 'assigning':
            addLogLine(`\n💾 ${data.message}`, 'info');
            // Don't update progress bar, just log
            break;
            
        case 'error':
            addLogLine(`❌ ${data.message}`, 'error');
            break;
            
        case 'complete':
            handleExecutionComplete(data);
            break;
            
        case 'debug':
            addLogLine(`🔧 ${data.message}`, 'debug');
            break;
            
        case 'disabling':
            addLogLine(`\n🚫 ${data.message}`, 'warning');
            break;
            
        case 'profile_disabled':
            addLogLine(data.message, 'warning');
            break;
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
    
    // Update progress bar to 100% only if there were streams to test
    if (totalStreamsToTest > 0) {
        updateProgress(100, 'Complete');
    } else {
        // No testing was done, set to 100% anyway to show completion
        updateProgress(100, 'Complete (no testing required)');
    }
    
    // Add final log message
    addLogLine(`\n${'='.repeat(60)}`, 'info');
    addLogLine(data.message, data.success ? 'success' : 'error');
    
    // Show summary
    const summaryDiv = document.getElementById('executionSummary');
    const resultDiv = document.getElementById('executionResult');
    
    summaryDiv.style.display = 'block';
    resultDiv.className = data.success ? 'alert alert-success' : 'alert alert-danger';
    
    let summaryHTML = `<h6>${data.message}</h6>`;
    
    if (data.matches_found !== undefined && data.streams_added !== undefined) {
        summaryHTML += '<ul class="mb-0 mt-2">';
        summaryHTML += `<li><strong>Matches found:</strong> ${data.matches_found}</li>`;
        summaryHTML += `<li><strong>Streams added:</strong> ${data.streams_added}</li>`;
        if (data.tested_count !== undefined) {
            summaryHTML += `<li><strong>Streams tested:</strong> ${data.tested_count}</li>`;
        }
        if (data.failed_tests !== undefined && data.failed_tests > 0) {
            summaryHTML += `<li><strong>Failed tests:</strong> ${data.failed_tests}</li>`;
        }
        if (data.skipped_count !== undefined && data.skipped_count > 0) {
            summaryHTML += `<li><strong>Skipped (recent stats):</strong> ${data.skipped_count}</li>`;
        }
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
        case 'debug':
            color = 'text-info';
            icon = '�';
            break;
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
