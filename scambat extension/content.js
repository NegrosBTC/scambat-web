console.log('ScamBat content script loaded at:', window.location.href);

// Respond to ping messages
browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "ping") {
        sendResponse({ pong: true });
        return;
    }
});

// Auth page handler
if (window.location.href.includes('localhost:8000/extension/auth')) {
    window.addEventListener('message', async (event) => {
        if (event.data.type === 'SCAMBAT_AUTH_SUCCESS') {
            console.log('Auth success received');
            
            try {
                // Store auth data via background script
                const response = await browser.runtime.sendMessage({
                    action: 'storeAuth',
                    token: event.data.token,
                    user: event.data.user
                });
                
                if (response.success) {
                    showNotification('✅ Extension connected successfully!', 'success');
                }
            } catch (error) {
                console.error('Failed to store auth:', error);
                showNotification('❌ Failed to connect extension', 'error');
            }
        }
    });
}

// Listen for report dialog messages
browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log('Content received:', message.action);
    
    if (message.action === "showReportDialog") {
        showReportDialog(message);
        sendResponse({ received: true });
    }
    
    return true;
});

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        border-radius: 8px;
        font-family: system-ui, -apple-system, sans-serif;
        font-size: 14px;
        z-index: 999999;
        animation: slideIn 0.3s ease-out;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    `;
    
    if (type === 'success') {
        notification.style.backgroundColor = '#10b981';
        notification.style.color = 'white';
    } else if (type === 'error') {
        notification.style.backgroundColor = '#ef4444';
        notification.style.color = 'white';
    }
    
    notification.textContent = message;
    document.body.appendChild(notification);
    
    // Add animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
    `;
    document.head.appendChild(style);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-in forwards';
        setTimeout(() => {
            notification.remove();
            style.remove();
        }, 300);
    }, 3000);
}

function showReportDialog(messageData) {
    console.log('Showing report dialog');
    
    // Remove existing dialog
    const existing = document.getElementById('scambat-dialog');
    if (existing) existing.remove();

    // Create dialog
    const dialog = document.createElement('div');
    dialog.id = 'scambat-dialog';
    
    const content = document.createElement('div');
    content.id = 'scambat-dialog-content';
    
    content.innerHTML = `
        <div class="scambat-header">
            <h2 style="font-size: 1.25rem; font-weight: bold; display: flex; align-items: center; gap: 0.5rem;">
                <span style="font-size: 1.5rem;">🛡️</span> Report Scam
            </h2>
            <p style="font-size: 0.875rem; opacity: 0.9; margin-top: 0.25rem;">
                Help protect others from this content
            </p>
        </div>
        
        <div class="scambat-body" style="display: flex; flex-direction: column; gap: 1rem;">
            ${messageData.selectedText ? `
                <div>
                    <label class="scambat-label">Selected Content:</label>
                    <div class="scambat-info-box">
                        ${escapeHtml(messageData.selectedText.substring(0, 500))}${messageData.selectedText.length > 500 ? '...' : ''}
                    </div>
                </div>
            ` : ''}
            
            <div>
                <label class="scambat-label">Current Page:</label>
                <div class="scambat-info-box">
                    ${escapeHtml(messageData.pageUrl || window.location.href)}
                </div>
            </div>

            <div>
                <label class="scambat-label">
                    Why is this a scam? <span style="color: #ef4444;">*</span>
                </label>
                <textarea 
                    id="scambat-reason" 
                    class="scambat-textarea"
                    rows="3"
                    placeholder="E.g., Asks for personal information, suspicious link, fake urgency..."
                    required
                ></textarea>
            </div>

            <div style="display: flex; gap: 0.75rem; padding-top: 1rem;">
                <button 
                    id="scambat-cancel" 
                    class="scambat-button scambat-button-secondary"
                    style="flex: 1;"
                >
                    Cancel
                </button>
                <button 
                    id="scambat-submit" 
                    class="scambat-button scambat-button-primary"
                    style="flex: 1;"
                >
                    🚨 Report Scam
                </button>
            </div>
        </div>
    `;
    
    dialog.appendChild(content);
    document.body.appendChild(dialog);
    
    // Store data
    dialog.dataset.messageData = JSON.stringify(messageData);

    // Event listeners
    document.getElementById('scambat-cancel').addEventListener('click', () => {
        dialog.remove();
    });
    
    document.getElementById('scambat-submit').addEventListener('click', () => {
        submitReport(dialog);
    });
    
    // Close on outside click
    dialog.addEventListener('click', (e) => {
        if (e.target === dialog) {
            dialog.remove();
        }
    });

    // Focus textarea
    setTimeout(() => {
        document.getElementById('scambat-reason')?.focus();
    }, 100);
}

async function submitReport(dialog) {
    const reason = document.getElementById('scambat-reason').value.trim();
    const submitBtn = document.getElementById('scambat-submit');
    const messageData = JSON.parse(dialog.dataset.messageData);

    if (!reason) {
        const textarea = document.getElementById('scambat-reason');
        textarea.style.borderColor = '#ef4444';
        textarea.placeholder = 'This field is required!';
        return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = 'Submitting...';
    submitBtn.style.opacity = '0.6';

    const reportData = {
        url: messageData.pageUrl || window.location.href,
        element_text: messageData.selectedText || '',
        element_html: '',
        user_reason: reason,
        context: {
            page_title: document.title,
            timestamp: new Date().toISOString()
        }
    };

    try {
        const response = await browser.runtime.sendMessage({
            action: "submitReport",
            data: reportData
        });
        
        if (response && response.success) {
            showSuccess(response, dialog);
        } else if (response && response.needsAuth) {
            alert('Please connect your ScamBat account first.');
            browser.runtime.sendMessage({ action: "openAuthPage" });
            dialog.remove();
        } else {
            const errorMsg = response?.error || 'Failed to submit report';
            showError(errorMsg, dialog);
            submitBtn.disabled = false;
            submitBtn.textContent = '🚨 Report Scam';
            submitBtn.style.opacity = '1';
        }
    } catch (error) {
        console.error('Submit error:', error);
        showError('Connection error: ' + error.message, dialog);
        submitBtn.disabled = false;
        submitBtn.textContent = '🚨 Report Scam';
        submitBtn.style.opacity = '1';
    }
}

function showSuccess(response, dialog) {
    const content = dialog.querySelector('#scambat-dialog-content');
    content.innerHTML = `
        <div style="padding: 3rem; text-align: center;">
            <div style="font-size: 4rem; margin-bottom: 1rem;">🎉</div>
            <h2 style="font-size: 1.5rem; font-weight: bold; color: #10b981; margin-bottom: 0.5rem;">
                Report Submitted!
            </h2>
            <p style="font-size: 1.125rem; font-weight: 600; margin-bottom: 0.5rem;">
                +${response.points || 0} Cyberpoints earned!
            </p>
            <p style="color: #4b5563; margin-bottom: 1.5rem;">
                ${escapeHtml(response.analysis || 'Thank you for helping protect others!')}
            </p>
            <button 
                onclick="document.getElementById('scambat-dialog').remove()"
                class="scambat-button scambat-button-primary"
            >
                Close
            </button>
        </div>
    `;
    
    setTimeout(() => dialog.remove(), 5000);
}

function showError(errorMessage, dialog) {
    let errorDiv = dialog.querySelector('#error-message');
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.id = 'error-message';
        errorDiv.className = 'scambat-error';
        const reasonDiv = dialog.querySelector('#scambat-reason').parentElement;
        reasonDiv.appendChild(errorDiv);
    }
    errorDiv.textContent = '❌ ' + errorMessage;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}