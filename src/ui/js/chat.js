document.addEventListener('DOMContentLoaded', async () => {
    const chatWindow = document.getElementById('chat-window');
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    const statusIndicator = document.createElement('div');
    statusIndicator.className = 'status-indicator';
    document.querySelector('.sidebar-header').appendChild(statusIndicator);

    // Initialize API client with dev token
    const api = new ZigralAPI({
        token: 'zigral_dev_token_123',
        onUpdate: handleUpdate,
        onError: handleError
    });

    // Initialize connection
    try {
        const initialized = await api.initialize();
        if (initialized) {
            updateStatus('connected');
            addMessage('Connected to Zigral. Ready to help!', false);
        } else {
            updateStatus('error');
            addMessage('Failed to connect to Zigral. Please try refreshing the page.', false, 'error');
        }
    } catch (error) {
        updateStatus('error');
        addMessage('Failed to connect to backend. Please try again later.', false, 'error');
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
        
        // Format message based on type
        if (typeof message === 'string') {
            messageElement.textContent = message;
        } else {
            // Handle structured messages
            const formattedMessage = formatStructuredMessage(message);
            messageElement.innerHTML = formattedMessage;
        }
        
        chatWindow.appendChild(messageElement);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    // Function to format structured messages
    function formatStructuredMessage(message) {
        if (message.steps) {
            return message.steps.map(step => {
                const status = step.result.status === 'success' ? '✓' : '✗';
                const details = step.result.message || step.result.error || '';
                return `${status} ${step.step.action}: ${details}`;
            }).join('<br>');
        }
        return JSON.stringify(message, null, 2);
    }

    // Function to handle WebSocket updates
    function handleUpdate(update) {
        switch (update.type) {
            case 'command_received':
                addMessage('Processing your request...', false, 'update');
                break;
            case 'action_sequence_generated':
                addMessage('Planning the following actions:', false, 'update');
                update.data.steps.forEach(step => {
                    addMessage(`• ${step.agent} will ${step.action}`, false, 'update');
                });
                break;
            case 'execution_progress':
                addMessage(update.data.message, false, 'update');
                break;
            case 'execution_complete':
                addMessage('Task completed!', false);
                addMessage(update.data, false);  // This will use formatStructuredMessage
                break;
            case 'error':
                addMessage(`Error: ${update.data.detail}`, false, 'error');
                break;
            case 'pong':
                // Handle pong response (connection check)
                break;
        }
    }

    // Function to handle errors
    function handleError(message, error) {
        console.error(message, error);
        let errorMessage = message;
        if (error.type === 'openai_error') {
            errorMessage = 'The AI is currently busy. Please try again in a moment.';
        } else if (error.status === 429) {
            errorMessage = 'Too many requests. Please wait a minute before trying again.';
        }
        addMessage(errorMessage, false, 'error');
        updateStatus('error');
        
        // Automatically retry connection if it's a connection error
        if (message.includes('WebSocket')) {
            setTimeout(() => {
                api.initialize().then(initialized => {
                    if (initialized) {
                        updateStatus('connected');
                        addMessage('Reconnected!', false, 'update');
                    }
                });
            }, 5000);
        }
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
                if (error.status === 401) {
                    addMessage('Authentication failed. Please refresh the page.', false, 'error');
                } else {
                    addMessage(`Failed to send command: ${error.message}`, false, 'error');
                }
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