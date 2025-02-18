document.addEventListener('DOMContentLoaded', async () => {
    const kasmIframe = document.getElementById('kasm-iframe');
    const refreshButton = document.getElementById('refresh-kasm');
    const fullscreenButton = document.getElementById('fullscreen-kasm');

    // Use the proxy URL in development
    const isDevelopment = window.location.hostname === 'localhost';
    const kasmBaseUrl = isDevelopment ? '/kasm-proxy' : 'https://34.136.51.93:443';
    const developmentPort = '5173';  // Always use 5173 for development

    // Initialize Kasm API with API key authentication
    const kasmApi = new KasmAPI({
        baseUrl: kasmBaseUrl,
        authDomain: isDevelopment ? `localhost:${developmentPort}` : '34.136.51.93',
        apiKey: 'j2dGkSDC9ROG',
        apiKeySecret: 'ZwGqyAOODC9W9nIrPuCLWoB3dvMROEu4'
    });

    let currentSessionId = null;

    function showError(message, details = '') {
        console.error('Kasm Error:', message, details);
        const errorDiv = document.createElement('div');
        errorDiv.className = 'kasm-error';
        errorDiv.innerHTML = `
            <h3>Failed to connect to Kasm workspace</h3>
            <p>${message}</p>
            ${details ? `<pre>${details}</pre>` : ''}
            <p>Please ensure:</p>
            <ul>
                <li>The Kasm server is running at ${isDevelopment ? 'the proxy' : '34.136.51.93'}</li>
                <li>You can access <a href="https://34.136.51.93" target="_blank">the Kasm dashboard</a></li>
                <li>The development proxy is properly configured</li>
            </ul>
            <button onclick="window.location.reload()">Retry Connection</button>
        `;
        
        // Remove any existing error message
        const existingError = document.querySelector('.kasm-error');
        if (existingError) {
            existingError.remove();
        }
        
        kasmIframe.parentNode.appendChild(errorDiv);
    }

    async function initializeKasmSession() {
        try {
            // Show connecting status
            showError('Connecting to Kasm server...');

            // Initialize API and authenticate
            const initialized = await kasmApi.initialize();
            if (!initialized) {
                throw new Error('Failed to initialize Kasm API');
            }

            // Create a new session with the Ubuntu workspace
            const sessionData = await kasmApi.createSession('ubuntu-focal-dind');
            currentSessionId = sessionData.session_id;

            // Update iframe source with session URL
            kasmIframe.src = sessionData.session_url;
            
            // Set required permissions and sandbox attributes
            kasmIframe.allow = [
                'autoplay',
                'clipboard-read',
                'clipboard-write',
                'camera',
                'microphone'
            ].join('; ');

            // Set sandbox attributes - only allow necessary features
            kasmIframe.sandbox = [
                'allow-scripts',
                'allow-forms',
                'allow-popups',
                'allow-modals',
                'allow-downloads',
                'allow-same-origin',  // Required for Kasm functionality
                'allow-top-navigation-by-user-activation'  // More secure top navigation
            ].join(' ');
            
            // Log the session URL for debugging
            console.log('Session URL:', sessionData.session_url);
            
            // Remove connecting message
            const errorDiv = document.querySelector('.kasm-error');
            if (errorDiv) {
                errorDiv.remove();
            }
            
        } catch (error) {
            let errorMessage = 'Connection failed';
            if (error.message.includes('Failed to fetch')) {
                errorMessage = 'Cannot reach Kasm server';
            } else if (error.message.includes('timeout')) {
                errorMessage = 'Connection timed out';
            }
            showError(errorMessage, error.message);
        }
    }

    // Initialize session when page loads
    await initializeKasmSession();

    // Function to refresh the Kasm iframe
    refreshButton.addEventListener('click', async () => {
        const errorDiv = document.querySelector('.kasm-error');
        if (errorDiv) {
            errorDiv.remove();
        }
        
        if (currentSessionId) {
            try {
                await kasmApi.destroySession(currentSessionId);
            } catch (error) {
                console.error('Error destroying old session:', error);
            }
        }
        await initializeKasmSession();
    });

    // Function to toggle fullscreen
    fullscreenButton.addEventListener('click', () => {
        if (!document.fullscreenElement) {
            kasmIframe.requestFullscreen().catch(err => {
                console.error(`Error attempting to enable fullscreen: ${err.message}`);
            });
        } else {
            document.exitFullscreen();
        }
    });

    // Update fullscreen button text based on fullscreen state
    document.addEventListener('fullscreenchange', () => {
        fullscreenButton.textContent = document.fullscreenElement ? 'Exit Fullscreen' : 'Fullscreen';
    });

    // Handle iframe load events
    kasmIframe.addEventListener('load', () => {
        console.log('Kasm iframe loaded');
        // Only remove error if we have a valid src
        if (kasmIframe.src !== 'about:blank') {
            const errorDiv = document.querySelector('.kasm-error');
            if (errorDiv) {
                errorDiv.remove();
            }
        }
    });

    // Clean up session when page is unloaded
    window.addEventListener('beforeunload', async () => {
        if (currentSessionId) {
            try {
                await kasmApi.destroySession(currentSessionId);
            } catch (error) {
                console.error('Error destroying session during cleanup:', error);
            }
        }
    });
}); 