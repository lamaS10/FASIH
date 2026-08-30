document.addEventListener('DOMContentLoaded', function () {
    const roomData = document.getElementById('room-data');
    if (!roomData) return;

    const roomId = roomData.dataset.roomId;
    const currentUserId = roomData.dataset.userId;
    const messageLog = document.getElementById('chat-messages');
    const messageInput = document.getElementById('chat-message-input');
    const sendButton = document.getElementById('chat-message-submit');
    const chatForm = document.getElementById('chat-form');

    if (messageLog) {
        messageLog.scrollTop = messageLog.scrollHeight;
    }

    const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
    const chatSocket = new WebSocket(
        `${wsScheme}://${window.location.host}/ws/chat/${roomId}/`
    );

    chatSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        const isMe = data.sender_id == currentUserId;
        const senderName = data.sender_name || (isMe ? 'أنت' : 'مستخدم');
        const timestamp = data.timestamp || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        const emptyChatNotice = document.getElementById('no-messages');
        if (emptyChatNotice) {
            emptyChatNotice.remove();
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `message-bubble ${isMe ? 'message-sent' : 'message-received'}`;

        messageDiv.innerHTML = `
            <div class="message-sender">${senderName}</div>
            <div>${data.message}</div>
            <div class="message-time">${timestamp}</div>
        `;

        if (messageLog) {
            messageLog.appendChild(messageDiv);
            messageLog.scrollTop = messageLog.scrollHeight;
        }
    };

    chatSocket.onclose = function(e) {
        console.error('Chat socket closed unexpectedly');
    };

    function sendMessage() {
        const message = messageInput.value.trim();
        if (message !== '') {
            if (chatSocket.readyState === WebSocket.OPEN) {
                chatSocket.send(JSON.stringify({
                    'message': message
                }));
                messageInput.value = '';
            } else {
                console.error('WebSocket connection is not open.');
            }
        }
    }

    if (sendButton) {
        sendButton.onclick = function(e) {
            e.preventDefault();
            sendMessage();
        };
    }

    if (messageInput) {
        messageInput.onkeyup = function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendMessage();
            }
        };
    }

    if (chatForm) {
        chatForm.onsubmit = function(e) {
            e.preventDefault();
            sendMessage();
        };
    }
});