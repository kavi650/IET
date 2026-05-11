/**
 * Teslead Equipments - Chatbot Page JavaScript
 * Handles: Full chat UI, message send/receive, suggestions
 */

document.addEventListener('DOMContentLoaded', () => {
    initChatbot();
});

function initChatbot() {
    const input = document.getElementById('chatInput');
    const sendBtn = document.getElementById('chatSend');
    const messages = document.getElementById('chatMessages');
    const clearBtn = document.getElementById('clearChat');
    const suggestions = document.getElementById('chatSuggestions');

    if (!input || !sendBtn || !messages) return;

    // Send button
    sendBtn.addEventListener('click', () => {
        const query = input.value.trim();
        if (query) sendMessage(query, messages, input);
    });

    // Enter key
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const query = input.value.trim();
            if (query) sendMessage(query, messages, input);
        }
    });

    // Suggestion chips
    document.querySelectorAll('#chatSuggestions .suggestion-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const query = chip.getAttribute('data-q');
            sendMessage(query, messages, input);
            // Hide suggestions after first use
            if (suggestions) suggestions.style.display = 'none';
        });
    });

    // Clear chat
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            messages.innerHTML = `
                <div class="chat-bubble ai">
                    <strong>🔄 Chat cleared!</strong><br><br>
                    Ask me anything about Testiny industrial equipment.
                </div>
            `;
            if (suggestions) {
                suggestions.style.display = 'flex';
                messages.appendChild(suggestions);
            }
        });
    }

    // Focus input
    input.focus();
}

/* ============================================
   SEND MESSAGE
   ============================================ */
async function sendMessage(query, messagesContainer, input) {
    // Add user message
    const userBubble = document.createElement('div');
    userBubble.className = 'chat-bubble user';
    userBubble.innerHTML = `
        <div>${escapeHtml(query)}</div>
        <div class="bubble-time">${getTimeString()}</div>
    `;
    messagesContainer.appendChild(userBubble);

    // Clear input
    input.value = '';
    input.focus();

    // Show typing indicator
    const typing = document.createElement('div');
    typing.className = 'typing-indicator';
    typing.innerHTML = '<span></span><span></span><span></span>';
    messagesContainer.appendChild(typing);

    // Scroll to bottom
    scrollToBottom(messagesContainer);

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });

        const data = await response.json();

        // Remove typing indicator
        typing.remove();

        // Add AI response
        const aiBubble = document.createElement('div');
        aiBubble.className = 'chat-bubble ai';
        aiBubble.innerHTML = `
            <div>${formatChatMessage(data.response)}</div>
            <div class="bubble-time">${getTimeString()} • ${data.source === 'ollama' ? '🤖 LLaMA' : '📚 Knowledge Base'}</div>
        `;
        messagesContainer.appendChild(aiBubble);

    } catch (error) {
        typing.remove();

        const errBubble = document.createElement('div');
        errBubble.className = 'chat-bubble ai';
        errBubble.innerHTML = `
            <div>⚠️ Sorry, I'm having trouble connecting to the server. Please make sure the Flask backend is running on <code>localhost:5000</code>.</div>
            <div class="bubble-time">${getTimeString()}</div>
        `;
        messagesContainer.appendChild(errBubble);
    }

    scrollToBottom(messagesContainer);
}

/* ============================================
   FORMAT CHAT MESSAGE
   ============================================ */
function formatChatMessage(text) {
    if (!text) return '';

    let html = text
        // Bold
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        // Italic
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        // Code inline
        .replace(/`(.*?)`/g, '<code style="background:rgba(0,0,0,0.08);padding:2px 6px;border-radius:4px;font-size:0.85em;">$1</code>')
        // Bullet points
        .replace(/^[•\-] (.+)/gm, '<div style="display:flex;gap:8px;margin:4px 0;"><span style="color:var(--accent);">▸</span><span>$1</span></div>')
        // Tables (simple markdown table)
        .replace(/\|(.+)\|\n\|[-| ]+\|\n([\s\S]*?\|.+\|)/g, (match, header, body) => {
            const headers = header.split('|').filter(h => h.trim());
            const rows = body.trim().split('\n').map(row =>
                row.split('|').filter(c => c.trim())
            );

            let table = '<table style="width:100%;border-collapse:collapse;margin:8px 0;font-size:0.85em;">';
            table += '<tr>' + headers.map(h => `<th style="padding:6px 10px;background:var(--primary);color:white;text-align:left;">${h.trim()}</th>`).join('') + '</tr>';
            rows.forEach(row => {
                table += '<tr>' + row.map(c => `<td style="padding:6px 10px;border-bottom:1px solid var(--border-light);">${c.trim()}</td>`).join('') + '</tr>';
            });
            table += '</table>';
            return table;
        })
        // Newlines
        .replace(/\n/g, '<br>');

    return html;
}

/* ============================================
   UTILITIES
   ============================================ */
function scrollToBottom(container) {
    setTimeout(() => {
        container.scrollTop = container.scrollHeight;
    }, 100);
}

function getTimeString() {
    const now = new Date();
    return now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
