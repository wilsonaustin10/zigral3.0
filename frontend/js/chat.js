document.addEventListener('DOMContentLoaded', () => {
    const chatWindow = document.getElementById('chat-window');
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');

    // Function to add a message to the chat window
    function addMessage(message, isUser = true) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('chat-message');
        messageElement.classList.add(isUser ? 'user-message' : 'assistant-message');
        messageElement.textContent = message;
        chatWindow.appendChild(messageElement);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    // Function to handle sending messages
    function sendMessage() {
        const message = chatInput.value.trim();
        if (message) {
            addMessage(message, true);
            
            // TODO: Send message to backend
            // For now, simulate a response
            setTimeout(() => {
                addMessage('This is a simulated response from the assistant.', false);
            }, 1000);

            chatInput.value = '';
            chatInput.focus();
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
}); 