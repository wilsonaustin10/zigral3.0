/**
 * VNC Client Integration
 * Handles the connection to the noVNC server and manages the VNC viewer iframe.
 */

document.addEventListener('DOMContentLoaded', () => {
    const vncIframe = document.getElementById('vnc-iframe');
    const refreshButton = document.getElementById('refresh-vnc');
    const fullscreenButton = document.getElementById('fullscreen-vnc');

    // Get configuration from environment
    const vncHost = import.meta.env.VNC_HOST;
    const vncPort = import.meta.env.VNC_PORT;
    const vncPath = import.meta.env.VNC_PATH;

    // Construct the VNC URL
    const vncUrl = `${vncHost}:${vncPort}${vncPath}`;

    function showError(message, details = '') {
        console.error('VNC Error:', message, details);
        const errorDiv = document.createElement('div');
        errorDiv.className = 'vnc-error';
        errorDiv.innerHTML = `
            <h3>Failed to connect to VNC workspace</h3>
            <p>${message}</p>
            ${details ? `<pre>${details}</pre>` : ''}
            <button onclick="window.location.reload()">Retry Connection</button>
        `;
        
        // Remove any existing error message
        const existingError = document.querySelector('.vnc-error');
        if (existingError) {
            existingError.remove();
        }
        
        vncIframe.parentNode.appendChild(errorDiv);
    }

    function initializeVncViewer() {
        try {
            // Set the iframe source to the VNC viewer URL
            vncIframe.src = vncUrl;
            
            // Add necessary permissions for VNC viewer
            vncIframe.allow = 'clipboard-read; clipboard-write';
            
            // Set sandbox attributes for security
            vncIframe.sandbox = 'allow-scripts allow-same-origin allow-forms allow-popups';
            
            console.log('VNC URL:', vncUrl);
        } catch (error) {
            showError('Failed to initialize VNC viewer', error.message);
        }
    }

    // Initialize VNC viewer
    initializeVncViewer();

    // Add refresh button handler
    refreshButton.addEventListener('click', () => {
        vncIframe.src = vncUrl;
    });

    // Add fullscreen button handler
    fullscreenButton.addEventListener('click', () => {
        if (vncIframe.requestFullscreen) {
            vncIframe.requestFullscreen();
        }
    });

    // Handle iframe load errors
    vncIframe.addEventListener('error', (event) => {
        showError('Failed to load VNC viewer', event.message);
    });
}); 