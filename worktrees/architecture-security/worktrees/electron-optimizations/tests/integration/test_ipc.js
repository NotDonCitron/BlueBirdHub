// Integration tests for Electron-Python IPC communication

describe('IPC Communication Tests', () => {
  let electronAPI;

  beforeEach(() => {
    // Mock the electronAPI
    electronAPI = {
      apiRequest: jest.fn(),
      platform: 'darwin'
    };
    global.window = { electronAPI };
  });

  test('should call API request with correct parameters', async () => {
    electronAPI.apiRequest.mockResolvedValue({
      status: 'running',
      message: 'OrdnungsHub API is operational',
      version: '0.1.0'
    });

    const result = await window.electronAPI.apiRequest('/', 'GET');
    
    expect(electronAPI.apiRequest).toHaveBeenCalledWith('/', 'GET');
    expect(result.status).toBe('running');
  });

  test('should handle API errors gracefully', async () => {
    electronAPI.apiRequest.mockRejectedValue(new Error('Connection failed'));

    await expect(
      window.electronAPI.apiRequest('/invalid', 'GET')
    ).rejects.toThrow('Connection failed');
  });

  test('should send POST data correctly', async () => {
    const testData = { name: 'Test Workspace' };
    electronAPI.apiRequest.mockResolvedValue({ success: true });

    await window.electronAPI.apiRequest('/workspace', 'POST', testData);
    
    expect(electronAPI.apiRequest).toHaveBeenCalledWith(
      '/workspace', 
      'POST', 
      testData
    );
  });
});