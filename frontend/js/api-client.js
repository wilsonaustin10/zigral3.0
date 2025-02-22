/**
 * API Client for Zigral Backend
 * 
 * This client handles both REST and WebSocket communication with the Zigral backend.
 * It provides:
 * - Authentication using a dev token (zigral_dev_token_123)
 * - Real-time updates via WebSocket
 * - Command sending and response handling
 * - Automatic reconnection with exponential backoff
 * 
 * Usage:
 * ```javascript
 * const api = new ZigralAPI({
 *   token: 'zigral_dev_token_123',
 *   onUpdate: (update) => console.log('Update:', update),
 *   onError: (msg, err) => console.error(msg, err)
 * });
 * 
 * await api.initialize();
 * await api.sendCommand('find CTOs in Austin');
 * ```
 */

class ZigralAPI {
    constructor(config = {}) {
        // Use environment-based URLs
        this.baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        this.wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
        this.token = config.token || 'zigral_dev_token_123';  // Default to dev token
        this.onUpdate = config.onUpdate || (() => {});
        this.onError = config.onError || console.error;
        this.clientId = `client-${Math.random().toString(36).substr(2, 9)}`;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // Start with 1 second delay
    }

    /**
     * Initialize the API client and WebSocket connection
     */
    async initialize() {
        try {
            // Test the connection with a health check
            const health = await this.healthCheck();
            if (health.status !== 'healthy') {
                throw new Error('Backend is not healthy');
            }

            // Initialize WebSocket connection
            await this.connectWebSocket();
            return true;
        } catch (error) {
            this.onError('Failed to initialize API client:', error);
            return false;
        }
    }

    /**
     * Connect to the WebSocket endpoint
     */
    async connectWebSocket() {
        try {
            const wsEndpoint = `${this.wsUrl}/ws/updates/${this.clientId}`;
            console.log('Connecting to WebSocket:', wsEndpoint);
            
            this.ws = new WebSocket(wsEndpoint);

            this.ws.onmessage = (event) => {
                try {
                    const update = JSON.parse(event.data);
                    console.log('WebSocket message received:', update);
                    this.onUpdate(update);
                } catch (error) {
                    this.onError('Failed to parse WebSocket message:', error);
                }
            };

            this.ws.onclose = () => {
                console.log('WebSocket closed, attempt:', this.reconnectAttempts);
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    setTimeout(() => {
                        this.reconnectAttempts++;
                        this.reconnectDelay *= 2; // Exponential backoff
                        this.connectWebSocket();
                    }, this.reconnectDelay);
                } else {
                    this.onError('WebSocket connection failed after max attempts');
                }
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.onError('WebSocket error:', error);
            };

            // Wait for connection to be established
            await new Promise((resolve, reject) => {
                this.ws.onopen = () => {
                    console.log('WebSocket connected');
                    this.reconnectAttempts = 0;
                    this.reconnectDelay = 1000; // Reset delay on successful connection
                    resolve();
                };
                setTimeout(() => reject(new Error('WebSocket connection timeout')), 5000);
            });
        } catch (error) {
            this.onError('Failed to connect WebSocket:', error);
            throw error;
        }
    }

    /**
     * Send a command to the backend
     */
    async sendCommand(command, context = {}) {
        try {
            const response = await fetch(`${this.baseUrl}/command`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.token}`
                },
                body: JSON.stringify({ command, context })
            });

            const data = await response.json();
            
            if (!response.ok) {
                const error = new Error(data.detail || 'Failed to send command');
                error.status = response.status;
                error.type = data.error_type;
                throw error;
            }

            return data;
        } catch (error) {
            this.onError('Failed to send command:', error);
            throw error;
        }
    }

    /**
     * Check backend health
     */
    async healthCheck() {
        try {
            const response = await fetch(`${this.baseUrl}/health`);
            if (!response.ok) {
                throw new Error(`Health check failed with status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            this.onError('Health check failed:', error);
            throw error;
        }
    }

    /**
     * Close the WebSocket connection
     */
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

// Export the API client
window.ZigralAPI = ZigralAPI; 