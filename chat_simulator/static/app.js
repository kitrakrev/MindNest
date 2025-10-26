// API Base URL
const API_BASE = '';

// State
let personas = [];
let groups = [];
let selectedPersonas = [];
let selectedGroup = null;
let currentSimulation = null;
let messagePolling = null;
let currentTab = 'personas';
let lastMessageCount = 0; // Track message count to avoid re-rendering

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadPersonas();
    loadGroups();
    
    // Add listener for simulation type changes
    const simTypeSelect = document.getElementById('simType');
    if (simTypeSelect) {
        simTypeSelect.addEventListener('change', (e) => {
            const simType = e.target.value;
            // Switch view mode based on simulation type
            // But only if not currently running
            if (!currentSimulation || currentSimulation.status !== 'running') {
                switchViewMode(simType);
            }
        });
    }
});

// Utility Functions
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

function showModal(modalId) {
    document.getElementById(modalId).style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
}

// Tab Switching
function switchTab(tabName) {
    currentTab = tabName;
    
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(tabName + 'Tab').classList.add('active');
}

// Persona Functions
async function loadPersonas() {
    try {
        const response = await fetch(`${API_BASE}/api/personas/`);
        personas = await response.json();
        renderPersonas();
        updateActiveCount();
    } catch (error) {
        showNotification('Failed to load personas', 'error');
        console.error(error);
    }
}

function renderPersonas() {
    const container = document.getElementById('personasList');
    
    if (personas.length === 0) {
        container.innerHTML = '<p class="empty-state">No personas yet. Create one to get started!</p>';
        return;
    }
    
    container.innerHTML = personas.map(persona => `
        <div class="persona-card ${selectedPersonas.includes(persona.id) ? 'selected' : ''}" 
             onclick="togglePersona('${persona.id}')">
            <div class="persona-name">
                <span>${persona.name}</span>
                ${persona.is_active ? '🟢' : '🔴'}
            </div>
            <div class="persona-desc">${persona.description || 'No description'}</div>
            <div class="persona-prompt">${persona.system_prompt}</div>
            <div class="persona-actions">
                <button class="btn btn-sm btn-danger" onclick="deletePersona('${persona.id}', event)">Delete</button>
            </div>
        </div>
    `).join('');
}

function togglePersona(personaId) {
    const index = selectedPersonas.indexOf(personaId);
    if (index > -1) {
        selectedPersonas.splice(index, 1);
    } else {
        selectedPersonas.push(personaId);
    }
    renderPersonas();
    updateStartButton();
}

function updateActiveCount() {
    document.getElementById('activeCount').textContent = personas.filter(p => p.is_active).length;
}

function updateStartButton() {
    document.getElementById('startBtn').disabled = selectedPersonas.length < 1;
}

async function createPersona(event) {
    event.preventDefault();
    
    const data = {
        name: document.getElementById('personaName').value,
        description: document.getElementById('personaDesc').value || null,
        system_prompt: document.getElementById('personaPrompt').value,
        persona_type: document.getElementById('personaType').value
    };
    
    console.log('Creating persona with data:', data);
    
    try {
        const response = await fetch(`${API_BASE}/api/personas/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showNotification('Persona created successfully!', 'success');
            closeModal('createPersonaModal');
            loadPersonas();
            event.target.reset();
        } else {
            const errorData = await response.json();
            console.error('Validation error:', errorData);
            let errorMsg = 'Failed to create persona';
            if (errorData.detail) {
                if (Array.isArray(errorData.detail)) {
                    errorMsg = errorData.detail.map(e => `${e.loc.join('.')}: ${e.msg}`).join(', ');
                } else {
                    errorMsg = errorData.detail;
                }
            }
            throw new Error(errorMsg);
        }
    } catch (error) {
        showNotification(error.message || 'Failed to create persona', 'error');
        console.error(error);
    }
}

async function deletePersona(personaId, event) {
    event.stopPropagation();
    
    if (!confirm('Are you sure you want to delete this persona?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/personas/${personaId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('Persona deleted', 'success');
            selectedPersonas = selectedPersonas.filter(id => id !== personaId);
            loadPersonas();
        }
    } catch (error) {
        showNotification('Failed to delete persona', 'error');
        console.error(error);
    }
}

async function generateFromConversation(event) {
    event.preventDefault();
    
    const data = {
        conversation_text: document.getElementById('conversationText').value,
        persona_type: 'user',
        auto_create: true
    };
    
    try {
        const response = await fetch(`${API_BASE}/api/personas/generate/from-conversation`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            const result = await response.json();
            showNotification(`Generated ${result.count} persona(s)!`, 'success');
            closeModal('generatePersonaModal');
            loadPersonas();
            event.target.reset();
        } else {
            throw new Error('Failed to generate personas');
        }
    } catch (error) {
        showNotification('Failed to generate personas', 'error');
        console.error(error);
    }
}

async function uploadConversationFile(event) {
    event.preventDefault();
    
    const fileInput = document.getElementById('conversationFile');
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    
    try {
        const response = await fetch(`${API_BASE}/api/personas/generate/from-file?auto_create=true`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            showNotification(`Generated ${result.count} persona(s) from file!`, 'success');
            closeModal('uploadFileModal');
            loadPersonas();
            event.target.reset();
        } else {
            throw new Error('Failed to upload file');
        }
    } catch (error) {
        showNotification('Failed to upload file', 'error');
        console.error(error);
    }
}

// Simulation Functions
async function startOrContinueSimulation() {
    if (selectedPersonas.length === 0) {
        showNotification('Please select at least one persona', 'error');
        return;
    }
    
    const simType = document.getElementById('simType').value;
    
    // Handle Views simulation type differently
    if (simType === 'views') {
        await startViewsSimulation();
        return;
    }
    
    try {
        // Check if simulation exists and has messages
        let hasMessages = false;
        let conversationTopic = null;
        
        if (currentSimulation) {
            // Check existing messages
            const messagesResponse = await fetch(`${API_BASE}/api/chat/messages/${currentSimulation.id}?limit=1`);
            if (messagesResponse.ok) {
                const messages = await messagesResponse.json();
                hasMessages = messages.length > 0;
            }
        }
        
        // If no messages, ask for a topic
        if (!hasMessages) {
            conversationTopic = prompt('What topic should they discuss?\n\n(Leave empty for general conversation)', '');
            
            // User cancelled
            if (conversationTopic === null) {
                return;
            }
            
        // Clear chat first
            document.getElementById('chatMessages').innerHTML = '<p class="empty-state">Starting conversation...</p>';
        } else {
            document.getElementById('chatMessages').innerHTML = '<p class="empty-state">Continuing conversation...</p>';
        }
        
        // Create simulation if it doesn't exist
        if (!currentSimulation) {
        const simData = {
            name: `Simulation ${new Date().toLocaleTimeString()}`,
                description: conversationTopic || 'Interactive simulation',
            persona_ids: selectedPersonas,
            config: {
                simulation_type: document.getElementById('simType').value,
                max_turns: parseInt(document.getElementById('maxTurns').value),
                turn_delay: parseFloat(document.getElementById('turnDelay').value),
                allow_user_interruption: true
            }
        };
        
        const createResponse = await fetch(`${API_BASE}/api/simulation/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(simData)
        });
        
            if (!createResponse.ok) {
                const errorData = await createResponse.json().catch(() => ({}));
                const errorMsg = errorData.detail || 'Failed to create simulation';
                throw new Error(errorMsg);
            }
        
        currentSimulation = await createResponse.json();
            
            // If we have a topic, seed the conversation with it
            if (conversationTopic && conversationTopic.trim()) {
                await fetch(`${API_BASE}/api/chat/message?session_id=${currentSimulation.id}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        content: `Let's discuss: ${conversationTopic}`,
                        role: 'user'
                    })
                });
            }
        }
        
        // Start or restart simulation
        const startResponse = await fetch(`${API_BASE}/api/simulation/${currentSimulation.id}/start`, {
            method: 'POST'
        });
        
        if (!startResponse.ok) throw new Error('Failed to start simulation');
        
        const message = hasMessages ? 
            'Conversation continuing...' : 
            (conversationTopic ? `Starting discussion on: ${conversationTopic}` : 'Simulation started!');
        
        showNotification(message, 'success');
        updateSimulationStatus('running');
        updateButtons(true);
        
        // Reset message counter if starting fresh
        if (!hasMessages) {
        lastMessageCount = 0;
        }
        
        // Load messages immediately and start polling
        await loadMessages();
        startMessagePolling();
        
    } catch (error) {
        const errorMsg = error.message || 'Failed to start simulation';
        
        // Check if it's a persona not found error
        if (errorMsg.includes('Persona') && errorMsg.includes('not found')) {
            showNotification('⚠️ Selected personas are outdated. Please refresh the page and re-select personas.', 'error');
        } else {
            showNotification(`Error: ${errorMsg}`, 'error');
        }
        
        console.error(error);
        document.getElementById('chatMessages').innerHTML = '<p class="empty-state">Error starting simulation. Please refresh the page and try again.</p>';
    }
}

async function stopSimulation() {
    if (!currentSimulation) return;
    
    try {
        await fetch(`${API_BASE}/api/simulation/${currentSimulation.id}/stop`, {
            method: 'POST'
        });
        showNotification('Simulation stopped', 'info');
        updateSimulationStatus('idle');
        updateButtons(false);
        stopMessagePolling();
        lastMessageCount = 0;
        currentSimulation = null;
        
        // Reset graph view if active
        if (graphView) {
            graphView.reset();
        }
    } catch (error) {
        showNotification('Failed to stop simulation', 'error');
    }
}

async function startViewsSimulation() {
    try {
        // Get selected personas data
        const personasResponse = await fetch(`${API_BASE}/api/personas/`);
        const allPersonas = await personasResponse.json();
        const selectedPersonasData = allPersonas.filter(p => selectedPersonas.includes(p.id));
        
        if (selectedPersonasData.length < 2) {
            showNotification('Please select at least 2 personas for Views simulation', 'error');
            return;
        }
        
        // Switch to graph view
        switchViewMode('views');
        
        // Initialize graph
        initializeGraphView(selectedPersonasData);
        
        // Ask for message to propagate
        const message = prompt('What message should propagate through the network?\n\n(This will be the topic/rumor that spreads)', '');
        
        if (!message || message.trim() === '') {
            showNotification('Message cancelled', 'info');
            switchViewMode('chat');
            return;
        }
        
        // Update status
        updateSimulationStatus('running');
        updateButtons(true);
        
        // Start propagation
        showNotification(`Starting propagation: "${message}"`, 'success');
        
        // Run the propagation simulation
        await graphView.startPropagation(message);
        
        updateSimulationStatus('completed');
        updateButtons(false);
        
    } catch (error) {
        showNotification('Failed to start Views simulation', 'error');
        console.error(error);
        switchViewMode('chat');
    }
}

function updateSimulationStatus(status) {
    const statusEl = document.getElementById('simStatus');
    statusEl.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    statusEl.className = `status-badge status-${status}`;
}

function updateButtons(isRunning) {
    // Start/Continue button is always enabled if personas are selected
    document.getElementById('startBtn').disabled = false;
    document.getElementById('stopBtn').disabled = !isRunning;
}

// Message Functions
function startMessagePolling() {
    if (messagePolling) return;
    
    // Poll more frequently (every 1 second) for better responsiveness
    messagePolling = setInterval(async () => {
        if (currentSimulation) {
            await loadMessages();
        }
    }, 1000);
}

function stopMessagePolling() {
    if (messagePolling) {
        clearInterval(messagePolling);
        messagePolling = null;
    }
}

async function loadMessages() {
    if (!currentSimulation) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/chat/messages/${currentSimulation.id}?limit=50`);
        const messages = await response.json();
        
        // Only render if message count changed
        if (messages.length !== lastMessageCount) {
            lastMessageCount = messages.length;
        renderMessages(messages);
        updateMessageCount(messages.length);
            
            // Check if simulation is completed
            const simResponse = await fetch(`${API_BASE}/api/simulation/${currentSimulation.id}`);
            const sim = await simResponse.json();
            if (sim.status === 'completed') {
                updateSimulationStatus('completed');
                stopMessagePolling();
                showNotification('Simulation completed. Click "Start/Continue" to keep talking!', 'info');
            }
        }
    } catch (error) {
        console.error('Failed to load messages:', error);
    }
}

function renderMessages(messages) {
    const container = document.getElementById('chatMessages');
    
    if (messages.length === 0) {
        container.innerHTML = '<p class="empty-state">🤖 AI is thinking and generating response...</p>';
        return;
    }
    
    container.innerHTML = messages.map(msg => {
        const persona = personas.find(p => p.id === msg.persona_id);
        const personaName = persona ? persona.name : 'Unknown';
        const isUser = msg.role === 'user';
        
        return `
            <div class="message ${isUser ? 'user' : 'persona'}">
                <div class="message-header">${isUser ? '👤 You' : '🤖 ' + personaName}</div>
                <div class="message-content">${msg.content}</div>
            </div>
        `;
    }).join('');
    
    // Scroll to bottom
    container.scrollTop = container.scrollHeight;
}

function updateMessageCount(count) {
    document.getElementById('msgCount').textContent = count;
}

async function sendUserMessage() {
    if (!currentSimulation) {
        showNotification('Start a simulation first', 'error');
        return;
    }
    
    const input = document.getElementById('userMessage');
    const content = input.value.trim();
    
    if (!content) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/chat/message?session_id=${currentSimulation.id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                content: content,
                role: 'user'
            })
        });
        
        if (response.ok) {
            input.value = '';
            await loadMessages();
            
            // Resume simulation if it was paused (for AI to respond)
            const sim = await fetch(`${API_BASE}/api/simulation/${currentSimulation.id}`).then(r => r.json());
            if (sim.status === 'paused') {
                console.log('Resuming simulation to get AI response');
                await fetch(`${API_BASE}/api/simulation/${currentSimulation.id}/start`, {
                    method: 'POST'
                });
                updateSimulationStatus('running');
                updateButtons(true);
                startMessagePolling();
            }
        }
    } catch (error) {
        showNotification('Failed to send message', 'error');
    }
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendUserMessage();
    }
}

async function getTLDR(format = 'text') {
    if (!currentSimulation) {
        showNotification('No active simulation', 'error');
        return;
    }
    
    showModal('tldrModal');
    document.getElementById('tldrContent').innerHTML = '<p>Generating summary...</p>';
    
    // Update modal title based on format
    const modalTitle = format === 'video' ? '🎥 Video-Style Summary' : '📝 Text Summary';
    document.querySelector('#tldrModal h2').textContent = modalTitle;
    
    try {
        const response = await fetch(`${API_BASE}/api/chat/tldr`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: currentSimulation.id,
                last_n_messages: 20,
                format: format  // 'text' or 'video'
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            
            if (format === 'video') {
                // Video-style format: bullet points, timestamps, key moments
                document.getElementById('tldrContent').innerHTML = `
                    <div style="font-family: monospace; background: #f5f5f5; padding: 15px; border-radius: 8px;">
                        <p><strong>🎬 VIDEO SUMMARY</strong></p>
                        <p>${result.summary}</p>
                        <hr style="margin: 15px 0; border-color: #ddd;">
                        <p><strong>📊 Stats:</strong></p>
                        <ul style="list-style: none; padding-left: 0;">
                            <li>💬 Messages: ${result.message_count}</li>
                            <li>⏱️ Duration: ${result.time_range}</li>
                            <li>🎯 Format: Video-Style Brief</li>
                        </ul>
                    </div>
                `;
            } else {
                // Text format: narrative summary (AI-generated)
                const formattedSummary = result.summary.replace(/\n/g, '<br><br>');
                document.getElementById('tldrContent').innerHTML = `
                    <div style="background: #f9f9f9; padding: 20px; border-radius: 8px; max-height: 500px; overflow-y: auto;">
                        <p><strong>📝 Conversation Summary</strong></p>
                        <hr style="margin: 15px 0; border-color: #ddd;">
                        <div style="font-size: 14px; line-height: 1.8; color: #333; text-align: justify;">
${formattedSummary}
                        </div>
                        <hr style="margin: 15px 0; border-color: #ddd;">
                        <p><strong>📊 Stats:</strong></p>
                        <ul style="list-style: none; padding-left: 0;">
                            <li>💬 Messages: ${result.message_count}</li>
                            <li>⏱️ Duration: ${result.time_range}</li>
                            <li>🎯 Format: Narrative Summary</li>
                        </ul>
                    </div>
                `;
            }
        } else {
            throw new Error('Failed to generate TLDR');
        }
    } catch (error) {
        document.getElementById('tldrContent').innerHTML = '<p style="color: red;">Failed to generate summary</p>';
        showNotification('Failed to generate TLDR', 'error');
    }
}

function clearChat() {
    document.getElementById('chatMessages').innerHTML = '<p class="empty-state">Chat cleared</p>';
    document.getElementById('msgCount').textContent = '0';
    lastMessageCount = 0;
}

// ============================================================================
// GLOBAL AGENT CHAT FUNCTIONS
// ============================================================================
// The Global Meta-Advisor provides strategic insights by analyzing
// conversations with its own memory system (short-term and long-term)

let globalAgentChatHistory = [];

/**
 * Toggle the global agent chat window visibility
 */
function toggleGlobalAgentChat() {
    const chatWindow = document.getElementById('globalAgentChatWindow');
    const isVisible = chatWindow.style.display !== 'none';
    
    if (isVisible) {
        chatWindow.style.display = 'none';
    } else {
        chatWindow.style.display = 'flex';
        loadMemoryStats();
        document.getElementById('globalAgentInput').focus();
    }
}

/**
 * Load and update global agent memory statistics
 */
async function loadMemoryStats() {
    try {
        const response = await fetch(`${API_BASE}/api/global-agent/memory/stats`);
        if (!response.ok) return;
        
        const stats = await response.json();
        
        // Update in left panel tab (if exists)
        const stElement = document.getElementById('shortTermCount');
        if (stElement) stElement.textContent = stats.short_term_memories;
        
        const ltElement = document.getElementById('longTermCount');
        if (ltElement) ltElement.textContent = stats.long_term_memories;
        
        const tqElement = document.getElementById('totalQueries');
        if (tqElement) tqElement.textContent = stats.total_queries;
        
        // Update in chat window
        document.getElementById('gaShortTermCount').textContent = stats.short_term_memories;
        document.getElementById('gaLongTermCount').textContent = stats.long_term_memories;
        document.getElementById('gaTotalQueries').textContent = stats.total_queries;
    } catch (error) {
        console.error('Failed to load memory stats:', error);
    }
}

/**
 * Handle key press in global agent input (Enter to send)
 */
function handleGlobalAgentKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendGlobalAgentMessage();
    }
}

/**
 * Send a message to the global agent and display response
 */
async function sendGlobalAgentMessage() {
    const input = document.getElementById('globalAgentInput');
    const question = input.value.trim();
    
    if (!question) return;
    
    input.value = '';
    addGlobalAgentMessage('user', question);
    document.getElementById('advisorStatus').textContent = 'Thinking...';
    
    const thinkingId = addGlobalAgentMessage('advisor', '🤔 Analyzing...', true);
    
    try {
        const response = await fetch(`${API_BASE}/api/global-agent/advice`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                question: question,
                session_id: currentSimulation ? currentSimulation.id : null
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            
            removeGlobalAgentMessage(thinkingId);
            addGlobalAgentMessage('advisor', result.advice);
            addGlobalAgentMessage('system', 
                `📊 Analyzed ${result.context_size} messages from current session`);
            
            await loadMemoryStats();
            document.getElementById('advisorStatus').textContent = 'Ready';
        } else {
            throw new Error('Failed to get advice');
        }
    } catch (error) {
        removeGlobalAgentMessage(thinkingId);
        addGlobalAgentMessage('error', '❌ Failed to get advice. Please try again.');
        document.getElementById('advisorStatus').textContent = 'Error';
        setTimeout(() => {
            document.getElementById('advisorStatus').textContent = 'Ready';
        }, 2000);
    }
}

/**
 * Add a message to the global agent chat window
 * @param {string} role - Message role (user, advisor, system, error)
 * @param {string} content - Message content
 * @param {boolean} isTemporary - If true, don't save to history
 * @returns {string} Message ID for later reference
 */
function addGlobalAgentMessage(role, content, isTemporary = false) {
    const messagesDiv = document.getElementById('globalAgentMessages');
    const messageId = `ga-msg-${Date.now()}-${Math.random()}`;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `ga-message ga-message-${role}`;
    messageDiv.id = messageId;
    
    const roleLabels = {
        'user': '<strong>You:</strong>',
        'advisor': '<strong>🧠 Advisor:</strong>',
        'system': '',
        'error': ''
    };
    
    const label = roleLabels[role] || '';
    const cssClass = role === 'system' ? 'ga-system-msg' : role === 'error' ? 'ga-error-msg' : '';
    
    messageDiv.innerHTML = `
        <div class="ga-message-content ${cssClass}">
            ${label} ${escapeHtml(content)}
        </div>
    `;
    
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    
    if (!isTemporary) {
        globalAgentChatHistory.push({ role, content, timestamp: new Date() });
    }
    
    return messageId;
}

/**
 * Remove a message from the global agent chat
 */
function removeGlobalAgentMessage(messageId) {
    const messageDiv = document.getElementById(messageId);
    if (messageDiv) messageDiv.remove();
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Load and display global agent memory content
 */
async function loadMemoryContent() {
    try {
        const response = await fetch(`${API_BASE}/api/global-agent/memory/content`);
        if (!response.ok) throw new Error('Failed to load');
        
        const memory = await response.json();
        
        // Render short-term memory
        const shortTermDiv = document.getElementById('shortTermMemory');
        shortTermDiv.innerHTML = memory.short_term.length > 0
            ? memory.short_term.map(m => `
                <div class="memory-item">
                    <div class="memory-content">${escapeHtml(m.content)}</div>
                    <div class="memory-meta">
                        <small>📅 ${new Date(m.timestamp).toLocaleString()}</small>
                        <small>⭐ ${(m.importance * 100).toFixed(0)}%</small>
                    </div>
                </div>
            `).join('')
            : '<p class="empty-state">No short-term memories yet</p>';
        
        // Render long-term memory
        const longTermDiv = document.getElementById('longTermMemory');
        longTermDiv.innerHTML = memory.long_term.length > 0
            ? memory.long_term.map(m => `
                <div class="memory-item">
                    <div class="memory-content">${escapeHtml(m.content)}</div>
                    <div class="memory-meta">
                        <small>📅 ${new Date(m.timestamp).toLocaleString()}</small>
                        <small>⭐ ${(m.importance * 100).toFixed(0)}%</small>
                    </div>
                </div>
            `).join('')
            : '<p class="empty-state">No long-term memories yet</p>';
            
    } catch (error) {
        console.error('Failed to load memory content:', error);
        showNotification('Failed to load memory content', 'error');
    }
}

// Override showModal to load memory content when opening memory modal
const originalShowModal = showModal;
window.showModal = function(modalId) {
    if (modalId === 'viewMemoryModal') {
        loadMemoryContent();
    }
    originalShowModal(modalId);
};

