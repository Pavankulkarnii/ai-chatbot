// Configuration
const CONFIG = {
    apiBaseUrl: 'http://localhost:8000',
    wsUrl: 'ws://localhost:8000/ws/chat',
    defaultTemperature: 0.7,
    defaultMaxLength: 1000,
    useWebSocket: true
};

// State management
const state = {
    messages: [],
    isTyping: false,
    websocket: null,
    settings: {
        temperature: CONFIG.defaultTemperature,
        maxLength: CONFIG.defaultMaxLength,
        useWebSocket: CONFIG.useWebSocket
    },
    theme: 'dark'
};

// DOM elements
const elements = {
    chatContainer: document.getElementById('chatContainer'),
    messageInput: document.getElementById('messageInput'),
    sendBtn: document.getElementById('sendBtn'),
    typingIndicator: document.getElementById('typingIndicator'),
    themeToggle: document.getElementById('themeToggle'),
    resetBtn: document.getElementById('resetBtn'),
    settingsBtn: document.getElementById('settingsBtn'),
    settingsModal: document.getElementById('settingsModal'),
    closeSettings: document.getElementById('closeSettings'),
    temperature: document.getElementById('temperature'),
    tempValue: document.getElementById('tempValue'),
    maxLength: document.getElementById('maxLength'),
    lengthValue: document.getElementById('lengthValue'),
    useWebSocket: document.getElementById('useWebSocket'),
    charCount: document.getElementById('charCount'),
    connectionStatus: document.getElementById('connectionStatus')
};

// Initialize app
function init() {
    console.log('🚀 Initializing AI Chatbot...');
    
    // Load saved settings
    loadSettings();
    
    // Load saved theme
    loadTheme();
    
    // Setup event listeners
    setupEventListeners();
    
    // Connect WebSocket if enabled
    if (state.settings.useWebSocket) {
        connectWebSocket();
    }
    
    // Check API health
    checkApiHealth();
    
    console.log('✅ Chatbot initialized');
}

// Setup event listeners
function setupEventListeners() {
    // Send message
    elements.sendBtn.addEventListener('click', sendMessage);
    elements.messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Auto-resize textarea
    elements.messageInput.addEventListener('input', () => {
        elements.messageInput.style.height = 'auto';
        elements.messageInput.style.height = elements.messageInput.scrollHeight + 'px';
        
        // Update character count
        elements.charCount.textContent = elements.messageInput.value.length;
    });
    
    // Theme toggle
    elements.themeToggle.addEventListener('click', toggleTheme);
    
    // Reset conversation
    elements.resetBtn.addEventListener('click', resetConversation);
    
    // Settings modal
    elements.settingsBtn.addEventListener('click', () => {
        elements.settingsModal.classList.add('active');
    });
    
    elements.closeSettings.addEventListener('click', () => {
        elements.settingsModal.classList.remove('active');
    });
    
    elements.settingsModal.addEventListener('click', (e) => {
        if (e.target === elements.settingsModal) {
            elements.settingsModal.classList.remove('active');
        }
    });
    
    // Settings controls
    elements.temperature.addEventListener('input', (e) => {
        state.settings.temperature = parseFloat(e.target.value);
        elements.tempValue.textContent = e.target.value;
        saveSettings();
    });
    
    elements.maxLength.addEventListener('input', (e) => {
        state.settings.maxLength = parseInt(e.target.value);
        elements.lengthValue.textContent = e.target.value;
        saveSettings();
    });
    
    elements.useWebSocket.addEventListener('change', (e) => {
        state.settings.useWebSocket = e.target.checked;
        saveSettings();
        
        // Reconnect or disconnect WebSocket
        if (e.target.checked) {
            connectWebSocket();
        } else {
            disconnectWebSocket();
        }
    });
    
    // Example prompts
    document.querySelectorAll('.example-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const message = btn.getAttribute('data-message');
            elements.messageInput.value = message;
            sendMessage();
        });
    });
}

// Send message
async function sendMessage() {
    const message = elements.messageInput.value.trim();
    
    if (!message || state.isTyping) return;
    
    // Add user message to chat
    addMessage('user', message);
    
    // Clear input
    elements.messageInput.value = '';
    elements.messageInput.style.height = 'auto';
    elements.charCount.textContent = '0';
    
    // Hide welcome section
    const welcomeSection = document.querySelector('.welcome-section');
    if (welcomeSection) {
        welcomeSection.style.display = 'none';
    }
    
    // Send via WebSocket or REST API
    if (state.settings.useWebSocket && state.websocket?.readyState === WebSocket.OPEN) {
        sendViaWebSocket(message);
    } else {
        await sendViaRestAPI(message);
    }
}

// Send via WebSocket
function sendViaWebSocket(message) {
    try {
        state.websocket.send(JSON.stringify({
            message: message,
            temperature: state.settings.temperature,
            maxLength: state.settings.maxLength
        }));
    } catch (error) {
        console.error('WebSocket send error:', error);
        showError('Failed to send message via WebSocket. Trying REST API...');
        sendViaRestAPI(message);
    }
}

// Send via REST API
async function sendViaRestAPI(message) {
    setTyping(true);
    
    try {
        const response = await fetch(`${CONFIG.apiBaseUrl}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                temperature: state.settings.temperature,
                max_length: state.settings.maxLength
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        addMessage('bot', data.response);
    } catch (error) {
        console.error('API error:', error);
        showError('Failed to get response from the chatbot. Please try again.');
    } finally {
        setTyping(false);
    }
}

// WebSocket connection
function connectWebSocket() {
    if (state.websocket?.readyState === WebSocket.OPEN) return;
    
    console.log('Connecting to WebSocket...');
    
    try {
        state.websocket = new WebSocket(CONFIG.wsUrl);
        
        state.websocket.onopen = () => {
            console.log('✅ WebSocket connected');
            updateConnectionStatus(true);
        };
        
        state.websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'typing') {
                setTyping(data.isTyping);
            } else if (data.type === 'message') {
                setTyping(false);
                addMessage('bot', data.response);
            } else if (data.type === 'error') {
                showError(data.error);
                setTyping(false);
            }
        };
        
        state.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            updateConnectionStatus(false);
        };
        
        state.websocket.onclose = () => {
            console.log('WebSocket disconnected');
            updateConnectionStatus(false);
            
            // Attempt reconnection after 5 seconds
            if (state.settings.useWebSocket) {
                setTimeout(() => {
                    console.log('Attempting to reconnect...');
                    connectWebSocket();
                }, 5000);
            }
        };
    } catch (error) {
        console.error('Failed to create WebSocket:', error);
        updateConnectionStatus(false);
    }
}

// Disconnect WebSocket
function disconnectWebSocket() {
    if (state.websocket) {
        state.websocket.close();
        state.websocket = null;
        updateConnectionStatus(false);
    }
}

// Update connection status
function updateConnectionStatus(connected) {
    if (connected) {
        elements.connectionStatus.textContent = '● Connected (WebSocket)';
        elements.connectionStatus.className = 'connection-status connected';
    } else {
        elements.connectionStatus.textContent = '● Using REST API';
        elements.connectionStatus.className = 'connection-status disconnected';
    }
}

// Add message to chat
function addMessage(type, content) {
    const message = {
        type,
        content,
        timestamp: new Date().toISOString()
    };
    
    state.messages.push(message);
    
    const messageEl = createMessageElement(message);
    elements.chatContainer.appendChild(messageEl);
    
    // Scroll to bottom
    scrollToBottom();
}

// Create message element
function createMessageElement(message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${message.type}-message`;
    
    const avatar = document.createElement('div');
    avatar.className = `avatar ${message.type}-avatar`;
    avatar.textContent = message.type === 'user' ? '👤' : '🤖';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    content.textContent = message.content;
    
    const timestamp = document.createElement('span');
    timestamp.className = 'message-timestamp';
    timestamp.textContent = formatTimestamp(message.timestamp);
    content.appendChild(timestamp);
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    return messageDiv;
}

// Set typing indicator
function setTyping(isTyping) {
    state.isTyping = isTyping;
    elements.typingIndicator.style.display = isTyping ? 'block' : 'none';
    elements.sendBtn.disabled = isTyping;
    
    if (isTyping) {
        scrollToBottom();
    }
}

// Reset conversation
async function resetConversation() {
    if (!confirm('Are you sure you want to start a new conversation?')) return;
    
    try {
        const response = await fetch(`${CONFIG.apiBaseUrl}/api/reset`, {
            method: 'POST'
        });
        
        if (response.ok) {
            // Clear messages
            state.messages = [];
            elements.chatContainer.innerHTML = `
                <div class="welcome-section">
                    <div class="welcome-icon">💬</div>
                    <h2>Welcome to AI Chatbot</h2>
                    <p>Start a conversation below. I'm powered by DialoGPT and running on your MacBook Air M4!</p>
                    <div class="example-prompts">
                        <p class="prompts-title">Try asking:</p>
                        <button class="example-btn" data-message="Tell me a fun fact about artificial intelligence">Tell me a fun fact about AI</button>
                        <button class="example-btn" data-message="What's the weather like today?">What's the weather like?</button>
                        <button class="example-btn" data-message="Can you help me write a poem?">Write me a poem</button>
                        <button class="example-btn" data-message="Explain machine learning in simple terms">Explain machine learning</button>
                    </div>
                </div>
            `;
            
            // Re-attach event listeners to example buttons
            document.querySelectorAll('.example-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const message = btn.getAttribute('data-message');
                    elements.messageInput.value = message;
                    sendMessage();
                });
            });
            
            showSuccess('Conversation reset successfully!');
        }
    } catch (error) {
        console.error('Reset error:', error);
        showError('Failed to reset conversation');
    }
}

// Theme toggle
function toggleTheme() {
    state.theme = state.theme === 'dark' ? 'light' : 'dark';
    document.body.classList.toggle('light-theme');
    
    const icon = elements.themeToggle.querySelector('.theme-icon');
    icon.textContent = state.theme === 'dark' ? '🌙' : '☀️';
    
    // Save theme preference
    localStorage.setItem('theme', state.theme);
}

// Load theme
function loadTheme() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        state.theme = savedTheme;
        if (savedTheme === 'light') {
            document.body.classList.add('light-theme');
            const icon = elements.themeToggle.querySelector('.theme-icon');
            icon.textContent = '☀️';
        }
    }
}

// Save settings
function saveSettings() {
    localStorage.setItem('chatbot-settings', JSON.stringify(state.settings));
}

// Load settings
function loadSettings() {
    const saved = localStorage.getItem('chatbot-settings');
    if (saved) {
        state.settings = { ...state.settings, ...JSON.parse(saved) };
        
        // Update UI
        elements.temperature.value = state.settings.temperature;
        elements.tempValue.textContent = state.settings.temperature;
        elements.maxLength.value = state.settings.maxLength;
        elements.lengthValue.textContent = state.settings.maxLength;
        elements.useWebSocket.checked = state.settings.useWebSocket;
    }
}

// Check API health
async function checkApiHealth() {
    try {
        const response = await fetch(`${CONFIG.apiBaseUrl}/`);
        const data = await response.json();
        console.log('API Health:', data);
    } catch (error) {
        console.error('API health check failed:', error);
        showError('Failed to connect to the chatbot API. Make sure the backend server is running.');
    }
}

// Show error
function showError(message) {
    const errorEl = document.createElement('div');
    errorEl.className = 'error-message';
    errorEl.innerHTML = `<span>⚠️</span><span>${message}</span>`;
    elements.chatContainer.appendChild(errorEl);
    
    setTimeout(() => errorEl.remove(), 5000);
    scrollToBottom();
}

// Show success
function showSuccess(message) {
    const successEl = document.createElement('div');
    successEl.className = 'success-message';
    successEl.innerHTML = `<span>✅</span><span>${message}</span>`;
    elements.chatContainer.appendChild(successEl);
    
    setTimeout(() => successEl.remove(), 3000);
    scrollToBottom();
}

// Scroll to bottom
function scrollToBottom() {
    setTimeout(() => {
        elements.chatContainer.scrollTop = elements.chatContainer.scrollHeight;
    }, 100);
}

// Format timestamp
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}


