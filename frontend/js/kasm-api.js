class KasmAPI {
    constructor(config = {}) {
        const isDevelopment = import.meta.env.DEV;
        this.baseUrl = isDevelopment ? '/kasm-proxy' : import.meta.env.VITE_KASM_HOST;
        this.authDomain = config.authDomain || import.meta.env.VITE_KASM_AUTH_DOMAIN;
        this.credentials = {
            apiKey: config.apiKey || import.meta.env.VITE_KASM_API_KEY,
            apiKeySecret: config.apiKeySecret || import.meta.env.VITE_KASM_API_KEY_SECRET
        };
        this.token = null;
        
        // Log configuration in development mode
        if (isDevelopment) {
            console.log('KasmAPI Configuration:', {
                baseUrl: this.baseUrl,
                authDomain: this.authDomain,
                apiKeyPresent: !!this.credentials.apiKey,
                apiKeySecretPresent: !!this.credentials.apiKeySecret
            });
        }
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
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Origin': window.location.origin,
                'Host': window.location.host
            };

            console.log('Authenticating with credentials:', {
                apiKeyPresent: !!this.credentials.apiKey,
                apiKeySecretPresent: !!this.credentials.apiKeySecret,
                authDomain: this.authDomain
            });

            const response = await fetch(`${this.baseUrl}/api/authenticate`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({
                    api_key: this.credentials.apiKey,
                    api_key_secret: this.credentials.apiKeySecret,
                    auth_domain: this.authDomain  // Add auth_domain to the request body
                }),
                credentials: 'include'  // Important: This ensures cookies are sent and stored
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({ message: response.statusText }));
                throw new Error(error.message || 'Authentication failed');
            }

            const data = await response.json();
            this.token = data.token;

            // Log cookies in development mode
            if (import.meta.env.DEV) {
                console.log('Authentication successful. Cookies:', document.cookie);
            }

            return data;
        } catch (error) {
            console.error('Authentication error:', error);
            throw error;
        }
    }

    _getAuthHeaders() {
        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Origin': window.location.origin
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        return headers;
    }

    async createSession(imageId = 'kasmweb/ubuntu-jammy-desktop:1.14.0') {
        if (!this.token && !this.credentials.apiKey) {
            throw new Error('Not authenticated');
        }

        try {
            const response = await fetch(`${this.baseUrl}/api/sessions`, {
                method: 'POST',
                headers: this._getAuthHeaders(),
                body: JSON.stringify({
                    image_id: imageId,
                    auth_domain: this.authDomain,
                    allow_origin: window.location.origin,
                    persistent: false, // Don't persist the container to save disk space
                    gpu_count: 0      // Don't request GPU to reduce resource usage
                }),
                credentials: 'include'
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({ message: response.statusText }));
                throw new Error(error.message || response.statusText);
            }

            const sessionData = await response.json();
            console.log('Session created:', sessionData);
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