const promptInput = document.getElementById('prompt-input');
const generateBtn = document.getElementById('generate-btn');
const chatHistory = document.getElementById('chat-history');
const welcomeMessage = document.querySelector('.welcome-message');

const debateLog = document.getElementById('full-debate-log');
const debateStatus = document.getElementById('debate-status');

const previewIframe = document.getElementById('preview-iframe');
const codeOutput = document.getElementById('code-output');

const tabBtns = document.querySelectorAll('.tab-btn');
const workspacePanes = document.querySelectorAll('.workspace-pane');
const newChatBtn = document.getElementById('new-chat-btn');

let eventSource = null;
let activeStatusPill = null;

// Tab Switching
tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        tabBtns.forEach(b => b.classList.remove('active'));
        workspacePanes.forEach(p => p.classList.remove('active'));
        
        btn.classList.add('active');
        document.getElementById(btn.dataset.target).classList.add('active');
    });
});

// Auto-resize textarea
promptInput.addEventListener('input', function() {
    this.style.height = '24px';
    if (this.scrollHeight > 24) {
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        this.style.overflowY = 'auto';
    } else {
        this.style.overflowY = 'hidden';
    }
});

// Submit on Enter
promptInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        generateBtn.click();
    }
});

generateBtn.addEventListener('click', () => {
    const prompt = promptInput.value.trim();
    if (!prompt) return;

    // Reset UI
    if (welcomeMessage) welcomeMessage.style.display = 'none';
    promptInput.value = '';
    promptInput.style.height = '24px';
    generateBtn.disabled = true;
    
    // Add user message to sidebar
    const userMsg = document.createElement('div');
    userMsg.className = 'sidebar-user-msg';
    userMsg.textContent = prompt;
    chatHistory.appendChild(userMsg);
    
    // Add status pill to sidebar
    activeStatusPill = document.createElement('div');
    activeStatusPill.className = 'sidebar-status-pill';
    activeStatusPill.innerHTML = `<div class="spinner"></div> <span>Council is debating... (Click to view)</span>`;
    
    // Clicking the status pill switches to Council Debate tab
    activeStatusPill.addEventListener('click', () => {
        tabBtns[0].click(); // Activate Debate tab
    });
    chatHistory.appendChild(activeStatusPill);
    chatHistory.scrollTop = chatHistory.scrollHeight;

    // Reset Debate Log in Main Pane
    debateLog.innerHTML = '';
    debateStatus.textContent = "Debate in Progress...";
    debateStatus.className = "status-badge active";
    
    // Automatically switch to Debate tab so user sees the discussion live!
    tabBtns[0].click();
    
    // Open Server-Sent Events stream
    const url = `/api/stream?prompt=${encodeURIComponent(prompt)}`;
    eventSource = new EventSource(url);

    eventSource.onmessage = (event) => {
        if (event.data === "[DONE]") {
            eventSource.close();
            generateBtn.disabled = false;
            debateStatus.textContent = "Finished";
            debateStatus.className = "status-badge";
            
            if (activeStatusPill) {
                activeStatusPill.className = 'sidebar-status-pill success';
                activeStatusPill.innerHTML = `<i data-lucide="check-circle-2"></i> <span>Generation Complete</span>`;
                lucide.createIcons();
            }
            return;
        }

        const data = JSON.parse(event.data);
        
function getAgentClass(agentName) {
    if (agentName.includes('Product Manager')) return 'pm';
    if (agentName.includes('Designer')) return 'designer';
    if (agentName.includes('Security')) return 'security';
    if (agentName.includes('Interviewer')) return 'interviewer';
    if (agentName.includes('Implementation Plan')) return 'plan';
    if (agentName.includes('Coding')) return 'coder';
    return '';
}

        if (data.status === 'typing') {
            const typingEl = document.getElementById('typing-indicator-msg');
            if (typingEl) typingEl.remove();

            const agentClass = getAgentClass(data.agent);
            const msg = document.createElement('div');
            msg.className = `debate-message ${agentClass}`;
            msg.id = 'typing-indicator-msg';
            msg.innerHTML = `
                <div class="agent-badge"><div class="spinner"></div> ${data.agent}</div>
                <div class="message-body"><em>Debating & analyzing proposals...</em></div>
            `;
            debateLog.appendChild(msg);
            debateLog.scrollTop = debateLog.scrollHeight;
        } 
        else if (data.message) {
            const typingEl = document.getElementById('typing-indicator-msg');
            if (typingEl) typingEl.remove();

            const agentClass = getAgentClass(data.agent);
            const msg = document.createElement('div');
            msg.className = `debate-message ${agentClass}`;
            
            const formatted = data.message
                .replace(/\n/g, '<br>')
                .replace(/### (.*?)(<br>|$)/g, '<h4>$1</h4>')
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                
            msg.innerHTML = `
                <div class="agent-badge"><i data-lucide="bot"></i> ${data.agent}</div>
                <div class="message-body">${formatted}</div>
            `;
            debateLog.appendChild(msg);
            lucide.createIcons();
            debateLog.scrollTop = debateLog.scrollHeight;
        }
        else if (data.code) {
            const typingEl = document.getElementById('typing-indicator-msg');
            if (typingEl) typingEl.remove();

            codeOutput.value = data.code;
            
            // Inject into iframe
            previewIframe.classList.remove('hidden');
            const emptyState = document.querySelector('#preview-pane .empty-state');
            if (emptyState) emptyState.classList.add('hidden');
            
            const iframeDoc = previewIframe.contentDocument || previewIframe.contentWindow.document;
            iframeDoc.open();
            iframeDoc.write(data.code);
            iframeDoc.close();
            
            // Auto switch to Preview tab when code is complete!
            tabBtns[1].click();
            
            eventSource.close();
            generateBtn.disabled = false;
            
            if (activeStatusPill) {
                activeStatusPill.className = 'sidebar-status-pill success';
                activeStatusPill.innerHTML = `<i data-lucide="check-circle-2"></i> <span>App Built! View Preview</span>`;
                lucide.createIcons();
            }
        }
    };

    eventSource.onerror = (error) => {
        console.error("SSE Error:", error);
        eventSource.close();
        generateBtn.disabled = false;
        debateStatus.textContent = "Error";
        debateStatus.className = "status-badge";
        
        if (activeStatusPill) {
            activeStatusPill.className = 'sidebar-status-pill error';
            activeStatusPill.innerHTML = `<i data-lucide="alert-circle"></i> <span>Error occurred during debate</span>`;
            lucide.createIcons();
        }
    };
});

newChatBtn.addEventListener('click', () => {
    window.location.reload();
});
