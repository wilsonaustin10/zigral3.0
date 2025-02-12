class KasmAPI {
    constructor(config = {}) {
        this.baseUrl = config.baseUrl || 'https://kasm.example.com'; // Update with your Kasm server URL
        this.authDomain = config.authDomain || 'example.com';
        this.credentials = {
            username: config.username || '',
            password: config.password || '',
            apiKey: config.apiKey || '',
            apiKeySecret: config.apiKeySecret || ''
        };
        this.token = null;
    }

    async initialize() {
        try {
            await this.authenticate();
            return true;
        } catch (error) {
            console.error('Failed to initialize Kasm API:', error);
            return false;
        }
    }

    async authenticate() {
        try {
            const headers = {
                'Content-Type': 'application/json'
            };

            // Add API key authentication if available
            if (this.credentials.apiKey && this.credentials.apiKeySecret) {
                headers['X-Api-Key'] = this.credentials.apiKey;
                headers['X-Api-Key-Secret'] = this.credentials.apiKeySecret;
            }

            const response = await fetch(`${this.baseUrl}/api/authenticate`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({
                    username: this.credentials.username,
                    password: this.credentials.password
                }),
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error(`Authentication failed: ${response.statusText}`);
            }

            const data = await response.json();
            this.token = data.token;
            return data;
        } catch (error) {
            console.error('Authentication error:', error);
            throw error;
        }
    }

    // Helper method to get headers with authentication
    _getAuthHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        if (this.credentials.apiKey && this.credentials.apiKeySecret) {
            headers['X-Api-Key'] = this.credentials.apiKey;
            headers['X-Api-Key-Secret'] = this.credentials.apiKeySecret;
        }

        return headers;
    }

    async createSession(imageId) {
        if (!this.token && !this.credentials.apiKey) {
            throw new Error('Not authenticated');
        }

        try {
            const response = await fetch(`${this.baseUrl}/api/sessions`, {
                method: 'POST',
                headers: this._getAuthHeaders(),
                body: JSON.stringify({
                    image_id: imageId,
                }),
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error(`Failed to create session: ${response.statusText}`);
            }

            const sessionData = await response.json();
            return sessionData;
        } catch (error) {
            console.error('Session creation error:', error);
            throw error;
        }
    }

    async getSession(sessionId) {
        if (!this.token && !this.credentials.apiKey) {
            throw new Error('Not authenticated');
        }

        try {
            const response = await fetch(`${this.baseUrl}/api/sessions/${sessionId}`, {
                headers: this._getAuthHeaders(),
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error(`Failed to get session: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Session retrieval error:', error);
            throw error;
        }
    }

    async destroySession(sessionId) {
        if (!this.token && !this.credentials.apiKey) {
            throw new Error('Not authenticated');
        }

        try {
            const response = await fetch(`${this.baseUrl}/api/sessions/${sessionId}`, {
                method: 'DELETE',
                headers: this._getAuthHeaders(),
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error(`Failed to destroy session: ${response.statusText}`);
            }

            return true;
        } catch (error) {
            console.error('Session destruction error:', error);
            throw error;
        }
    }
}

// Export the API class
window.KasmAPI = KasmAPI; 