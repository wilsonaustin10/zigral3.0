document.addEventListener('DOMContentLoaded', () => {
    const kasmIframe = document.getElementById('kasm-iframe');
    const refreshButton = document.getElementById('refresh-kasm');
    const fullscreenButton = document.getElementById('fullscreen-kasm');

    // Function to refresh the Kasm iframe
    refreshButton.addEventListener('click', () => {
        kasmIframe.src = kasmIframe.src;
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
    });

    // Handle iframe errors
    kasmIframe.addEventListener('error', () => {
        console.error('Error loading Kasm iframe');
        // TODO: Implement error handling UI
    });
}); 