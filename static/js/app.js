// Stream Plus - JavaScript Functions

// Global alert function
function showAlert(message, type = 'info', duration = 5000) {
    console.log('showAlert called with:', message, type);
    // For now, just show a simple alert
    alert(message);
}

// Global configuration
const StreamPlus = {
    apiBaseUrl: '',
    refreshInterval: 30000, // 30 seconds
    autoRefreshEnabled: false,
    currentPage: '',
    
    // Initialize the application
    init: function() {
        this.currentPage = this.getCurrentPage();
        this.setupGlobalEventListeners();
        this.startAutoRefresh();
        console.log('Stream Plus initialized for page:', this.currentPage);
    },
    
    // Get current page from URL
    getCurrentPage: function() {
        const path = window.location.pathname;
        if (path.includes('channels')) return 'channels';
        if (path.includes('streams')) return 'streams';
        return 'index';
    },
    
    // Setup global event listeners
    setupGlobalEventListeners: function() {
        // Handle page visibility change for auto-refresh
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopAutoRefresh();
            } else {
                this.startAutoRefresh();
            }
        });
        
        // Handle online/offline status
        window.addEventListener('online', () => {
            this.showNotification('Connection restored', 'success');
            this.checkApiConnection();
        });
        
        window.addEventListener('offline', () => {
            this.showNotification('No internet connection', 'warning');
        });
    },
    
    // Auto-refresh functionality
    startAutoRefresh: function() {
        if (this.autoRefreshEnabled && !document.hidden) {
            this.refreshTimer = setInterval(() => {
                this.refreshCurrentPage();
            }, this.refreshInterval);
        }
    },
    
    stopAutoRefresh: function() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
    },
    
    refreshCurrentPage: function() {
        // Only refresh if not in a modal
        const openModals = document.querySelectorAll('.modal.show');
        if (openModals.length === 0) {
            this.showNotification('Updating data...', 'info', 2000);
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        }
    },
    
    // API Connection testing
    checkApiConnection: function() {
        return fetch('/api/channels')
            .then(response => {
                if (response.ok) {
                    this.updateConnectionStatus(true);
                    return true;
                } else {
                    this.updateConnectionStatus(false);
                    return false;
                }
            })
            .catch(error => {
                console.error('API connection error:', error);
                this.updateConnectionStatus(false);
                return false;
            });
    },
    
    updateConnectionStatus: function(isConnected) {
        const statusElement = document.querySelector('.badge');
        if (statusElement) {
            if (isConnected) {
                statusElement.className = 'badge bg-success fs-6';
                statusElement.innerHTML = '<i class="fas fa-circle"></i> Connected to Dispatcharr';
            } else {
                statusElement.className = 'badge bg-danger fs-6';
                statusElement.innerHTML = '<i class="fas fa-exclamation-circle"></i> Disconnected';
            }
        }
    },
    
    // Notification system
    showNotification: function(message, type = 'info', duration = 5000) {
        const alertTypes = {
            'info': 'alert-info',
            'success': 'alert-success', 
            'warning': 'alert-warning',
            'error': 'alert-danger',
            'danger': 'alert-danger'
        };
        
        const alertClass = alertTypes[type] || 'alert-info';
        
        const notification = document.createElement('div');
        notification.className = `alert ${alertClass} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 80px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto dismiss after duration
        if (duration > 0) {
            setTimeout(() => {
                if (notification.parentNode) {
                    const alert = new bootstrap.Alert(notification);
                    alert.close();
                }
            }, duration);
        }
    },
    showAlert: function(message, type = 'info', duration = 5000) {
        const alertTypes = {
            'info': 'alert-info',
            'success': 'alert-success', 
            'warning': 'alert-warning',
            'error': 'alert-danger',
            'danger': 'alert-danger'
        };
        
        const alertClass = alertTypes[type] || 'alert-info';
        
        // Create or find alert container
        let alertContainer = document.getElementById('alert-container');
        if (!alertContainer) {
            alertContainer = document.createElement('div');
            alertContainer.id = 'alert-container';
            alertContainer.className = 'container-fluid mt-3';
            
            // Insert at the beginning of the main content
            const mainContent = document.querySelector('main') || document.querySelector('.container') || document.body;
            mainContent.insertBefore(alertContainer, mainContent.firstChild);
        }
        
        const alert = document.createElement('div');
        alert.className = `alert ${alertClass} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        alertContainer.appendChild(alert);
        
        // Auto dismiss after duration
        if (duration > 0) {
            setTimeout(() => {
                if (alert.parentNode) {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                }
            }, duration);
        }
    },
    showLoading: function(element = null) {
        const target = element || document.getElementById('loading');
        if (target) {
            target.style.display = 'block';
        }
    },
    
    hideLoading: function(element = null) {
        const target = element || document.getElementById('loading');
        if (target) {
            target.style.display = 'none';
        }
    },
    
    // Form validation
    validateForm: function(formId) {
        const form = document.getElementById(formId);
        if (!form) return false;
        
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.classList.add('is-invalid');
                isValid = false;
            } else {
                field.classList.remove('is-invalid');
            }
        });
        
        return isValid;
    },
    
    // Utility functions
    formatDate: function(dateString) {
        if (!dateString) return 'Date not available';
        
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('es-ES', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (error) {
            return dateString;
        }
    },
    
    formatStatus: function(status) {
        const statusMap = {
            'active': 'Active',
            'inactive': 'Inactive',
            'running': 'Running',
            'stopped': 'Stopped',
            'error': 'Error',
            'pending': 'Pending'
        };
        
        return statusMap[status] || status;
    },
    
    // Export/Import functionality
    exportData: function(data, filename) {
        const blob = new Blob([JSON.stringify(data, null, 2)], {
            type: 'application/json'
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    },
    
    // Search and filter utilities
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // Local storage utilities
    saveToStorage: function(key, data) {
        try {
            localStorage.setItem(key, JSON.stringify(data));
            return true;
        } catch (error) {
            console.error('Error saving to localStorage:', error);
            return false;
        }
    },
    
    loadFromStorage: function(key) {
        try {
            const data = localStorage.getItem(key);
            return data ? JSON.parse(data) : null;
        } catch (error) {
            console.error('Error loading from localStorage:', error);
            return null;
        }
    }
};

// Global functions for backward compatibility and template use
function checkApiConnection() {
    StreamPlus.showLoading();
    StreamPlus.checkApiConnection()
        .then(isConnected => {
            if (isConnected) {
                StreamPlus.showNotification('Dispatcharr API connected successfully', 'success');
            } else {
                StreamPlus.showNotification('Error connecting to Dispatcharr API', 'error');
            }
        })
        .finally(() => {
            StreamPlus.hideLoading();
        });
}

function toggleAutoRefresh() {
    StreamPlus.autoRefreshEnabled = !StreamPlus.autoRefreshEnabled;
    
    if (StreamPlus.autoRefreshEnabled) {
        StreamPlus.startAutoRefresh();
        StreamPlus.showNotification('Auto-refresh enabled', 'success');
    } else {
        StreamPlus.stopAutoRefresh();
        StreamPlus.showNotification('Auto-refresh disabled', 'info');
    }
}

function exportCurrentData() {
    const currentPage = StreamPlus.currentPage;
    let endpoint = '';
    let filename = '';
    
    switch (currentPage) {
        case 'channels':
            endpoint = '/api/channels';
            filename = 'channels_export.json';
            break;
        case 'streams':
            endpoint = '/api/streams';
            filename = 'streams_export.json';
            break;
        default:
            StreamPlus.showNotification('No data to export on this page', 'warning');
            return;
    }
    
    fetch(endpoint)
        .then(response => response.json())
        .then(data => {
            StreamPlus.exportData(data, filename);
            StreamPlus.showNotification('Datos exportados correctamente', 'success');
        })
        .catch(error => {
            console.error('Error exporting data:', error);
            StreamPlus.showNotification('Error al exportar datos', 'error');
        });
}

// Keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Ctrl/Cmd + R: Refresh
    if ((event.ctrlKey || event.metaKey) && event.key === 'r') {
        event.preventDefault();
        StreamPlus.refreshCurrentPage();
    }
    
    // Ctrl/Cmd + E: Export data
    if ((event.ctrlKey || event.metaKey) && event.key === 'e') {
        event.preventDefault();
        exportCurrentData();
    }
    
    // Escape: Close modals
    if (event.key === 'Escape') {
        const openModals = document.querySelectorAll('.modal.show');
        openModals.forEach(modal => {
            bootstrap.Modal.getInstance(modal)?.hide();
        });
    }
});

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    StreamPlus.init();
    
    // Add tooltips to all elements with title attribute
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[title]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Add loading states to buttons
    document.addEventListener('click', function(event) {
        if (event.target.classList.contains('btn') && 
            !event.target.classList.contains('btn-close') &&
            !event.target.hasAttribute('data-bs-dismiss')) {
            
            const button = event.target;
            const originalContent = button.innerHTML;
            
            // Add loading state
            button.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Cargando...';
            button.disabled = true;
            
            // Restore after 2 seconds (if not redirected)
            setTimeout(() => {
                if (button.parentNode) {
                    button.innerHTML = originalContent;
                    button.disabled = false;
                }
            }, 2000);
        }
    });
});

// Error handling
window.addEventListener('error', function(event) {
    console.error('JavaScript Error:', event.error);
    StreamPlus.showNotification('An error occurred in the application', 'error');
});

window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled Promise Rejection:', event.reason);
    StreamPlus.showNotification('Error communicating with server', 'error');
});

// Export StreamPlus for use in other scripts
window.StreamPlus = StreamPlus;

// Global showAlert function for backward compatibility
window.showAlert = StreamPlus.showAlert;