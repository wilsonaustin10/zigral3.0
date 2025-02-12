/**
 * API Client for Zigral Backend
 * Handles both REST and WebSocket communication with the backend
 */

class ZigralAPI {
    constructor(config = {}) {
        this.baseUrl = config.baseUrl || 'http://localhost:8000';
        this.wsUrl = config.wsUrl || 'ws://localhost:8000';
        this.token = config.token;
        this.onUpdate = config.onUpdate || (() => {});
        this.onError = config.onError || console.error;
        this.clientId = `client-${Math.random().toString(36).substr(2, 9)}`;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
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
            this.ws = new WebSocket(`${this.wsUrl}/ws/updates/${this.clientId}`);

            this.ws.onmessage = (event) => {
                const update = JSON.parse(event.data);
                this.onUpdate(update);
            };

            this.ws.onclose = () => {
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    setTimeout(() => {
                        this.reconnectAttempts++;
                        this.connectWebSocket();
                    }, 1000 * Math.pow(2, this.reconnectAttempts)); // Exponential backoff
                } else {
                    this.onError('WebSocket connection failed after max attempts');
                }
            };

            this.ws.onerror = (error) => {
                this.onError('WebSocket error:', error);
            };

            // Wait for connection to be established
            await new Promise((resolve, reject) => {
                this.ws.onopen = () => {
                    this.reconnectAttempts = 0;
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
                throw new Error(data.error || 'Failed to send command');
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