/**
 * VNC Client Integration with NoVNC WebSocket API
 * Enhanced with direct RFB connection and improved agent interaction
 */

// Import the noVNC RFB module if using as a module
// import RFB from './novnc/core/rfb.js';

document.addEventListener('DOMContentLoaded', async () => {
    const contentArea = document.querySelector('.content-area');
    const refreshButton = document.getElementById('refresh-vnc');
    const fullscreenButton = document.getElementById('fullscreen-vnc');
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    
    // Replace iframe with direct canvas approach
    const vncIframe = document.getElementById('vnc-iframe');
    vncIframe.style.display = 'none';
    
    // Create canvas container
    const vncContainer = document.createElement('div');
    vncContainer.id = 'vnc-display';
    vncContainer.className = 'vnc-container';
    contentArea.appendChild(vncContainer);
    
    // VNC Configuration
    const VNC_HOST = window.location.hostname || 'localhost';
    const VNC_PORT = '6082';  // Updated to our Docker container's websockify port
    const VNC_PASSWORD = 'zigral';  // Should be retrieved securely
    const WS_URL = `ws://${VNC_HOST}:${VNC_PORT}/websockify`;
    
    // RFB connection
    let rfb = null;
    let isConnected = false;
    let reconnectAttempts = 0;
    const MAX_RECONNECT_ATTEMPTS = 5;
    const RECONNECT_DELAY = 2000; // 2 seconds
    
    // Add status indicator
    const statusIndicator = document.createElement('div');
    statusIndicator.className = 'vnc-status';
    statusIndicator.textContent = 'Connecting...';
    contentArea.insertBefore(statusIndicator, vncContainer);
    
    function updateStatus(message, type = 'info') {
        statusIndicator.textContent = message;
        statusIndicator.className = `vnc-status vnc-status-${type}`;
    }
    
    function showError(message, details = '') {
        console.error('VNC Error:', message, details);
        updateStatus(message, 'error');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'vnc-error';
        errorDiv.innerHTML = `
            <h3>VNC Connection Error</h3>
            <p>${message}</p>
            ${details ? `<pre>${details}</pre>` : ''}
            <button id="retry-connection">Retry Connection</button>
        `;
        
        // Remove any existing error message
        const existingError = document.querySelector('.vnc-error');
        if (existingError) {
            existingError.remove();
        }
        
        vncContainer.appendChild(errorDiv);
        
        // Add retry handler
        document.getElementById('retry-connection').addEventListener('click', () => {
            errorDiv.remove();
            retryConnection();
        });
    }
    
    function retryConnection() {
        if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            reconnectAttempts++;
            updateStatus(`Reconnecting... (Attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`);
            console.log(`Retrying VNC connection (attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})...`);
            setTimeout(initializeVncViewer, RECONNECT_DELAY);
        } else {
            updateStatus('Connection failed', 'error');
            showError('Maximum reconnection attempts reached. Please check if the VNC server is running.');
        }
    }
    
    function disconnectVNC() {
        if (rfb) {
            console.log('Disconnecting VNC...');
            rfb.disconnect();
            rfb = null;
        }
    }
    
    async function checkVncConnection() {
        return new Promise((resolve, reject) => {
            const checkUrl = `http://${VNC_HOST}:${VNC_PORT}`;
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
    
    function initializeVncViewer() {
        try {
            updateStatus('Initializing connection...');
            
            // First disconnect if there's an existing connection
            disconnectVNC();
            
            // Add loading state
            vncContainer.classList.add('loading');
            
            // Create RFB connection
            rfb = new RFB(vncContainer, WS_URL, {
                credentials: { password: VNC_PASSWORD },
                wsProtocols: ['binary'],
                scaleViewport: true,
                resizeMode: 'remote',
                qualityLevel: 6,
                compressionLevel: 2,
                showDotCursor: true,
                clipViewport: false
            });
            
            // Connection event handlers
            rfb.addEventListener("connect", () => {
                console.log("Connected to VNC");
                updateStatus('Connected', 'success');
                vncContainer.classList.remove('loading');
                isConnected = true;
                reconnectAttempts = 0;
                
                // When connected, we create a global accessible object that Playwright can use
                window.zigralVNC = {
                    getDisplay: () => rfb._display,
                    sendKey: (keysym, code, down) => rfb.sendKey(keysym, code, down),
                    sendPointer: (x, y, mask) => rfb.sendPointer(x, y, mask),
                    getCanvasCoordinates: (x, y) => {
                        const rect = vncContainer.getBoundingClientRect();
                        return {
                            x: Math.floor((x - rect.left) * (rfb._fbWidth / rect.width)),
                            y: Math.floor((y - rect.top) * (rfb._fbHeight / rect.height))
                        };
                    },
                    focus: () => rfb.focus(),
                    getScreenResolution: () => ({ 
                        width: rfb._fbWidth, 
                        height: rfb._fbHeight 
                    })
                };
            });
            
            rfb.addEventListener("disconnect", (e) => {
                console.log("Disconnected from VNC", e);
                updateStatus('Disconnected', 'warning');
                isConnected = false;
                window.zigralVNC = null;
                
                if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                    retryConnection();
                }
            });
            
            rfb.addEventListener("credentialsrequired", () => {
                console.log("VNC credentials required");
                rfb.sendCredentials({ password: VNC_PASSWORD });
            });
            
            rfb.addEventListener("securityfailure", (e) => {
                console.error("Security failure:", e);
                showError('VNC security failure', e.detail.reason);
            });
            
            rfb.addEventListener("clipboard", (e) => {
                console.log("Clipboard event:", e.detail.text);
                // Optionally handle clipboard data
            });
            
            rfb.addEventListener("bell", () => {
                console.log("VNC Bell");
                // Optionally play a sound or show notification
            });
            
            rfb.addEventListener("desktopname", (e) => {
                console.log("Desktop name changed:", e.detail.name);
                // Update any UI showing the desktop name
            });
            
            rfb.addEventListener("capabilities", (e) => {
                console.log("VNC capabilities updated:", e.detail.capabilities);
            });
            
        } catch (error) {
            console.error('Failed to initialize VNC viewer:', error);
            showError('Failed to connect to VNC server', error.message);
            retryConnection();
        }
    }
    
    // Initialize VNC viewer when page loads
    try {
        // Check if noVNC library is loaded
        if (typeof RFB === 'undefined') {
            // First load all required noVNC scripts in the correct order
            const loadScript = (src) => {
                return new Promise((resolve, reject) => {
                    const script = document.createElement('script');
                    script.src = src;
                    script.onload = resolve;
                    script.onerror = (e) => reject(new Error(`Failed to load script: ${src}`));
                    document.head.appendChild(script);
                });
            };
            
            // Load pako from CDN (it might be missing in our installation)
            console.log('Loading noVNC dependencies...');
            // First make sure pako is available
            loadScript('https://cdn.jsdelivr.net/npm/pako@2.1.0/dist/pako.min.js')
            .then(() => {
                console.log('Pako loaded from CDN');
                // Then load core noVNC files
                return Promise.all([
                    loadScript('/novnc/core/util/logging.js'),
                    loadScript('/novnc/core/util/browser.js'),
                    loadScript('/novnc/core/util/events.js'),
                    loadScript('/novnc/core/util/eventtarget.js'),
                    loadScript('/novnc/core/util/util.js'),
                    loadScript('/novnc/core/util/element.js'),
                    loadScript('/novnc/core/display.js'),
                    loadScript('/novnc/core/input/keysym.js'),
                    loadScript('/novnc/core/input/keysymdef.js'),
                    loadScript('/novnc/core/input/keyboard.js'),
                    loadScript('/novnc/core/input/mouse.js'),
                    loadScript('/novnc/core/encodings.js'),
                    loadScript('/novnc/core/websock.js'),
                    loadScript('/novnc/core/rfb.js')
                ]);
            })
            .then(() => {
                console.log('All noVNC scripts loaded successfully');
                if (typeof RFB !== 'undefined') {
                    console.log('RFB class is available');
                    initializeVncViewer();
                } else {
                    console.error('RFB class still not defined after loading scripts');
                    showError('Failed to initialize noVNC: RFB class not available');
                }
            })
            .catch((error) => {
                console.error('Error loading noVNC scripts:', error);
                showError('Failed to load noVNC scripts', error.message);
            });
        } else {
            initializeVncViewer();
        }
    } catch (e) {
        console.error('Error during initialization:', e);
        showError('Failed to initialize VNC viewer', e.message);
    }
    
    // Add refresh button handler
    refreshButton.addEventListener('click', () => {
        vncContainer.classList.add('loading');
        reconnectAttempts = 0;
        initializeVncViewer();
    });
    
    // Add fullscreen button handler
    fullscreenButton.addEventListener('click', () => {
        if (vncContainer.requestFullscreen) {
            vncContainer.requestFullscreen();
        } else if (vncContainer.webkitRequestFullscreen) {
            vncContainer.webkitRequestFullscreen();
        } else if (vncContainer.mozRequestFullScreen) {
            vncContainer.mozRequestFullScreen();
        }
    });
    
    // Add chat input handler
    sendButton.addEventListener('click', () => {
        const message = chatInput.value.trim();
        if (message) {
            // Here would be the logic to send messages to the agent
            console.log('Sending message to agent:', message);
            chatInput.value = '';
        }
    });
    
    // Allow pressing Enter to send
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendButton.click();
        }
    });
}); 