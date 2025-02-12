document.addEventListener('DOMContentLoaded', async () => {
    const chatWindow = document.getElementById('chat-window');
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    const statusIndicator = document.createElement('div');
    statusIndicator.className = 'status-indicator';
    document.querySelector('.sidebar-header').appendChild(statusIndicator);

    // Initialize API client
    const api = new ZigralAPI({
        token: localStorage.getItem('auth_token'),
        onUpdate: handleUpdate,
        onError: handleError
    });

    // Initialize connection
    try {
        const initialized = await api.initialize();
        if (initialized) {
            updateStatus('connected');
        } else {
            updateStatus('error');
        }
    } catch (error) {
        updateStatus('error');
        addMessage('Failed to connect to backend. Please try again later.', false);
    }

    // Function to update connection status indicator
    function updateStatus(status) {
        statusIndicator.className = `status-indicator ${status}`;
        statusIndicator.title = `Status: ${status}`;
    }

    // Function to add a message to the chat window
    function addMessage(message, isUser = true, type = 'message') {
        const messageElement = document.createElement('div');
        messageElement.classList.add('chat-message');
        messageElement.classList.add(isUser ? 'user-message' : 'assistant-message');
        if (type === 'error') {
            messageElement.classList.add('error-message');
        } else if (type === 'update') {
            messageElement.classList.add('update-message');
        }
        messageElement.textContent = message;
        chatWindow.appendChild(messageElement);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    // Function to handle WebSocket updates
    function handleUpdate(update) {
        switch (update.type) {
            case 'command_received':
                addMessage('Command received...', false, 'update');
                break;
            case 'action_sequence_generated':
                addMessage('Planning actions...', false, 'update');
                break;
            case 'execution_complete':
                addMessage(`Completed: ${update.data.objective}`, false);
                // Add detailed results
                update.data.steps.forEach(step => {
                    if (step.result.status === 'success') {
                        addMessage(`✓ ${step.step.action}: ${step.result.message || 'Success'}`, false);
                    } else {
                        addMessage(`✗ ${step.step.action}: ${step.result.error || 'Failed'}`, false, 'error');
                    }
                });
                break;
            case 'error':
                addMessage(`Error: ${update.data.error}`, false, 'error');
                break;
            case 'pong':
                // Handle pong response (connection check)
                break;
        }
    }

    // Function to handle errors
    function handleError(message, error) {
        console.error(message, error);
        addMessage(`Error: ${message}`, false, 'error');
        updateStatus('error');
    }

    // Function to handle sending messages
    async function sendMessage() {
        const message = chatInput.value.trim();
        if (message) {
            addMessage(message, true);
            sendButton.disabled = true;
            updateStatus('processing');
            
            try {
                await api.sendCommand(message);
                chatInput.value = '';
            } catch (error) {
                addMessage(`Failed to send command: ${error.message}`, false, 'error');
            } finally {
                sendButton.disabled = false;
                updateStatus('connected');
            }
        }
    }

    // Event listeners
    sendButton.addEventListener('click', sendMessage);

    chatInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    });

    // Disable/enable send button based on input
    chatInput.addEventListener('input', () => {
        sendButton.disabled = chatInput.value.trim() === '';
    });

    // Initial state
    sendButton.disabled = true;

    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        api.disconnect();
    });
}); 