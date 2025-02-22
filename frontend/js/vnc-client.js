/**
 * VNC Client Integration
 * Handles the connection to the noVNC server and manages the VNC viewer iframe.
 */

document.addEventListener('DOMContentLoaded', () => {
    const vncIframe = document.getElementById('vnc-iframe');
    const refreshButton = document.getElementById('refresh-vnc');
    const fullscreenButton = document.getElementById('fullscreen-vnc');
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');

    // VNC Configuration
    const vncUrl = "/vnc/vnc.html?autoconnect=1&resize=scale&quality=9&compression=0&view_only=0";
    const VNC_PORT = '6080';
    const VNC_PATH = '/vnc.html';
    
    // Construct the VNC URL with proper parameters
    const vncUrl = `${VNC_HOST}:${VNC_PORT}${VNC_PATH}?autoconnect=true&resize=remote&quality=8&compression=2&view_only=0`;

    // Track connection state
    let isConnected = false;
    let reconnectAttempts = 0;
    const MAX_RECONNECT_ATTEMPTS = 5;
    const RECONNECT_DELAY = 2000; // 2 seconds

    function showError(message, details = '') {
        console.error('VNC Error:', message, details);
        const errorDiv = document.createElement('div');
        errorDiv.className = 'vnc-error';
        errorDiv.innerHTML = `
            <h3>VNC Connection Error</h3>
            <p>${message}</p>
            ${details ? `<pre>${details}</pre>` : ''}
            <button onclick="retryConnection()">Retry Connection</button>
        `;
        
        // Remove any existing error message
        const existingError = document.querySelector('.vnc-error');
        if (existingError) {
            existingError.remove();
        }
        
        vncIframe.parentNode.appendChild(errorDiv);
    }

    function retryConnection() {
        if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            reconnectAttempts++;
            console.log(`Retrying VNC connection (attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})...`);
            setTimeout(initializeVncViewer, RECONNECT_DELAY);
        } else {
            showError('Maximum reconnection attempts reached. Please check if the VNC server is running.');
        }
    }

    function checkVncConnection() {
        return new Promise((resolve, reject) => {
            const checkUrl = `${VNC_HOST}:${VNC_PORT}`;
            fetch(checkUrl)
                .then(response => {
                    if (response.ok) {
                        resolve(true);
                    } else {
                        reject(new Error(`VNC server responded with status: ${response.status}`));
                    }
                })
                .catch(error => reject(error));
        });
    }

    async function initializeVncViewer() {
        try {
            // Check if VNC server is accessible
            await checkVncConnection();
            
            // Add loading state
            vncIframe.parentNode.classList.add('loading');
            
            // Set the iframe source to the VNC viewer URL
            vncIframe.src = vncUrl;
            
            // Add necessary permissions for VNC viewer
            vncIframe.allow = 'clipboard-read; clipboard-write';
            
            // Set sandbox attributes for security while allowing necessary features
            vncIframe.sandbox = 'allow-scripts allow-same-origin allow-forms allow-popups allow-modals';
            
            // Handle iframe load
            vncIframe.onload = () => {
                vncIframe.parentNode.classList.remove('loading');
                isConnected = true;
                reconnectAttempts = 0;
                console.log('VNC viewer initialized:', vncUrl);
            };
            
        } catch (error) {
            console.error('Failed to initialize VNC viewer:', error);
            showError('Failed to connect to VNC server', error.message);
            retryConnection();
        }
    }

    // Initialize VNC viewer when page loads
    initializeVncViewer();

    // Add refresh button handler
    refreshButton.addEventListener('click', () => {
        vncIframe.parentNode.classList.add('loading');
        reconnectAttempts = 0;
        initializeVncViewer();
    });

    // Add fullscreen button handler
    fullscreenButton.addEventListener('click', () => {
        if (vncIframe.requestFullscreen) {
            vncIframe.requestFullscreen();
        } else if (vncIframe.webkitRequestFullscreen) {
            vncIframe.webkitRequestFullscreen();
        } else if (vncIframe.mozRequestFullScreen) {
            vncIframe.mozRequestFullScreen();
        }
    });

    // Handle iframe load errors
    vncIframe.addEventListener('error', (event) => {
        showError('Failed to load VNC viewer', event.message);
        retryConnection();
    });

    // Handle window resize
    window.addEventListener('resize', () => {
        if (isConnected) {
            // Notify the VNC client about the size change
            try {
                const vncDoc = vncIframe.contentWindow.document;
                const event = new Event('resize');
                vncDoc.dispatchEvent(event);
            } catch (e) {
                console.warn('Could not propagate resize event to VNC iframe:', e);
            }
        }
    });

    // Prevent VNC viewer from capturing all keyboard input when chat is focused
    chatInput.addEventListener('focus', () => {
        vncIframe.style.pointerEvents = 'none';
    });

    chatInput.addEventListener('blur', () => {
        vncIframe.style.pointerEvents = 'auto';
    });
}); 