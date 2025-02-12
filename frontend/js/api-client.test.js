/**
 * Tests for the Zigral API Client
 * Run with Jest
 */

describe('ZigralAPI', () => {
    let api;
    let mockFetch;
    let mockWebSocket;

    beforeEach(() => {
        // Mock fetch
        mockFetch = jest.fn();
        global.fetch = mockFetch;

        // Mock WebSocket
        mockWebSocket = {
            send: jest.fn(),
            close: jest.fn(),
        };
        global.WebSocket = jest.fn(() => mockWebSocket);

        // Create API instance
        api = new ZigralAPI({
            token: 'test-token',
            onUpdate: jest.fn(),
            onError: jest.fn()
        });
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    describe('initialization', () => {
        it('should successfully initialize with healthy backend', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({ status: 'healthy' })
            });

            const result = await api.initialize();
            expect(result).toBe(true);
            expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/health');
        });

        it('should fail initialization with unhealthy backend', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({ status: 'unhealthy' })
            });

            const result = await api.initialize();
            expect(result).toBe(false);
            expect(api.onError).toHaveBeenCalled();
        });
    });

    describe('WebSocket connection', () => {
        it('should establish WebSocket connection', async () => {
            const connectPromise = api.connectWebSocket();
            
            // Simulate successful connection
            mockWebSocket.onopen();
            
            await connectPromise;
            expect(global.WebSocket).toHaveBeenCalledWith(
                `ws://localhost:8000/ws/updates/${api.clientId}`
            );
        });

        it('should handle WebSocket messages', async () => {
            await api.connectWebSocket();
            
            // Simulate message
            const message = { type: 'test', data: {} };
            mockWebSocket.onmessage({ data: JSON.stringify(message) });
            
            expect(api.onUpdate).toHaveBeenCalledWith(message);
        });

        it('should attempt reconnection on close', async () => {
            jest.useFakeTimers();
            await api.connectWebSocket();
            
            // Simulate connection close
            mockWebSocket.onclose();
            
            // Fast-forward timers
            jest.runAllTimers();
            
            expect(global.WebSocket).toHaveBeenCalledTimes(2);
        });
    });

    describe('command handling', () => {
        it('should successfully send command', async () => {
            const command = 'test command';
            const response = { objective: 'test', steps: [] };
            
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(response)
            });

            const result = await api.sendCommand(command);
            
            expect(result).toEqual(response);
            expect(mockFetch).toHaveBeenCalledWith(
                'http://localhost:8000/command',
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer test-token'
                    },
                    body: JSON.stringify({ command, context: {} })
                }
            );
        });

        it('should handle command errors', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: false,
                json: () => Promise.resolve({ error: 'Test error' })
            });

            await expect(api.sendCommand('test')).rejects.toThrow('Test error');
            expect(api.onError).toHaveBeenCalled();
        });
    });

    describe('cleanup', () => {
        it('should properly disconnect', async () => {
            await api.connectWebSocket();
            api.disconnect();
            
            expect(mockWebSocket.close).toHaveBeenCalled();
            expect(api.ws).toBeNull();
        });
    });
}); 