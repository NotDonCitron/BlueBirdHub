// Connection monitoring with smart polling and non-blocking UI
document.addEventListener('DOMContentLoaded', async () => {
    // Get elements
    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');
    const platformInfo = document.getElementById('platform-info');
    const backendStatus = document.getElementById('backend-status');
    const checkHealthBtn = document.getElementById('check-health');
    
    // Display platform information
    platformInfo.textContent = `Platform: ${window.electronAPI.platform}`;
    
    // Connection state management
    let connectionAttempts = 0;
    let maxAttempts = 3;
    let pollingInterval = 5000; // Start with 5 seconds
    let connectionTimer = null;
    
    // Function to check backend connection with smart retry
    async function checkBackendConnection() {
        try {
            const response = await window.electronAPI.apiRequest('/', 'GET');
            if (response.status === 'running') {
                statusIndicator.classList.add('connected');
                statusIndicator.classList.remove('disconnected');
                statusText.textContent = 'Connected';
                backendStatus.textContent = `Backend: ${response.message}`;
                
                // Reset connection state on success
                connectionAttempts = 0;
                pollingInterval = 5000; // Reset to normal polling
                return true;
            }
        } catch (error) {
            console.error('Failed to connect to backend:', error);
            connectionAttempts++;
            
            statusIndicator.classList.add('disconnected');
            statusIndicator.classList.remove('connected');
            statusText.textContent = 'Disconnected';
            backendStatus.textContent = `Backend: Connection failed (attempt ${connectionAttempts})`;
            
            // Implement exponential backoff for polling
            if (connectionAttempts >= maxAttempts) {
                pollingInterval = Math.min(pollingInterval * 1.5, 30000); // Max 30 seconds
            }
            
            return false;
        }
    }
    
    // Function to create non-blocking notification (XSS-safe)
    function showNotification(title, message, type = 'info') {
        // Create notification element instead of blocking alert
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        // Create header
        const header = document.createElement('div');
        header.className = 'notification-header';
        
        const titleElement = document.createElement('strong');
        titleElement.textContent = title; // Safe from XSS
        
        const closeBtn = document.createElement('button');
        closeBtn.className = 'close-btn';
        closeBtn.textContent = '×';
        closeBtn.addEventListener('click', () => notification.remove());
        
        header.appendChild(titleElement);
        header.appendChild(closeBtn);
        
        // Create body
        const body = document.createElement('div');
        body.className = 'notification-body';
        body.textContent = message; // Safe from XSS
        
        notification.appendChild(header);
        notification.appendChild(body);
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
        
        // Add close button functionality
        notification.querySelector('.close-btn').addEventListener('click', () => {
            notification.remove();
        });
    }
    
    // Function to check system health with non-blocking UI
    async function checkSystemHealth() {
        try {
            checkHealthBtn.disabled = true;
            checkHealthBtn.textContent = 'Checking...';
            
            const health = await window.electronAPI.apiRequest('/health', 'GET');
            
            // Display health status using non-blocking notification
            const message = `Status: ${health.status}<br>Backend: ${health.backend}<br>Database: ${health.database}`;
            showNotification('System Health', message, 'success');
            
        } catch (error) {
            showNotification('Health Check Failed', 'Please ensure the backend is running.', 'error');
        } finally {
            checkHealthBtn.disabled = false;
            checkHealthBtn.textContent = 'Check System Health';
        }
    }
    
    // Smart polling function
    function scheduleNextCheck() {
        if (connectionTimer) {
            clearTimeout(connectionTimer);
        }
        
        connectionTimer = setTimeout(async () => {
            await checkBackendConnection();
            scheduleNextCheck(); // Schedule next check
        }, pollingInterval);
    }
    
    // Event listeners
    checkHealthBtn.addEventListener('click', checkSystemHealth);
    
    // Page visibility API to pause polling when tab is hidden
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            // Pause polling when tab is hidden
            if (connectionTimer) {
                clearTimeout(connectionTimer);
            }
        } else {
            // Resume polling when tab becomes visible
            scheduleNextCheck();
        }
    });
    
    // Initial connection check
    await checkBackendConnection();
    
    // Start smart polling
    scheduleNextCheck();
});