// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', async () => {
    // Get elements
    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');
    const platformInfo = document.getElementById('platform-info');
    const backendStatus = document.getElementById('backend-status');
    const checkHealthBtn = document.getElementById('check-health');
    
    // Display platform information
    platformInfo.textContent = `Platform: ${window.electronAPI.platform}`;
    
    // Function to check backend connection
    async function checkBackendConnection() {
        try {
            const response = await window.electronAPI.apiRequest('/', 'GET');
            if (response.status === 'running') {
                statusIndicator.classList.add('connected');
                statusIndicator.classList.remove('disconnected');
                statusText.textContent = 'Connected';
                backendStatus.textContent = `Backend: ${response.message}`;
                return true;
            }
        } catch (error) {
            console.error('Failed to connect to backend:', error);
            statusIndicator.classList.add('disconnected');
            statusIndicator.classList.remove('connected');
            statusText.textContent = 'Disconnected';
            backendStatus.textContent = 'Backend: Connection failed';
            return false;
        }
    }
    
    // Function to check system health
    async function checkSystemHealth() {
        try {
            checkHealthBtn.disabled = true;
            checkHealthBtn.textContent = 'Checking...';
            
            const health = await window.electronAPI.apiRequest('/health', 'GET');
            
            // Display health status
            alert(`System Health:\n\nStatus: ${health.status}\nBackend: ${health.backend}\nDatabase: ${health.database}`);
            
        } catch (error) {
            alert('Failed to check system health. Please ensure the backend is running.');
        } finally {
            checkHealthBtn.disabled = false;
            checkHealthBtn.textContent = 'Check System Health';
        }
    }
    
    // Event listeners
    checkHealthBtn.addEventListener('click', checkSystemHealth);
    
    // Initial connection check
    await checkBackendConnection();
    
    // Periodically check connection
    setInterval(checkBackendConnection, 5000);
});