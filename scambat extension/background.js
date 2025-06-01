console.log('Background script loaded');

const CONFIG = {
    API_BASE: 'http://localhost:8000/api/extension',
    LOGIN_URL: 'http://localhost:8000/extension/auth'
};

// Initialize on install
browser.runtime.onInstalled.addListener(() => {
    createContextMenu();
});

// Create context menu
function createContextMenu() {
    browser.contextMenus.removeAll(() => {
        browser.contextMenus.create({
            id: "report-scam",
            title: "🛡️ Report as Scam",
            contexts: ["selection", "link", "page"]
        });
        console.log('Context menu created');
    });
}

// Check URLs when tabs are updated
browser.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
    if (changeInfo.status === 'loading' && changeInfo.url) {
        await checkAndBlockURL(tabId, changeInfo.url);
    }
});

// Check URLs when tabs are activated
browser.tabs.onActivated.addListener(async (activeInfo) => {
    const tab = await browser.tabs.get(activeInfo.tabId);
    if (tab.url) {
        await checkAndBlockURL(activeInfo.tabId, tab.url);
    }
});

async function checkAndBlockURL(tabId, url) {
    // Skip checking for internal pages
    if (url.startsWith('chrome://') || 
        url.startsWith('about:') || 
        url.startsWith('moz-extension://') ||
        url.includes('localhost:8000')) {
        return;
    }
    
    try {
        const storage = await browser.storage.local.get(['authToken']);
        if (!storage.authToken) return;
        
        const response = await fetch(`${CONFIG.API_BASE}/check-url/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${storage.authToken}`
            },
            body: JSON.stringify({ url })
        });
        
        if (response.ok) {
            const data = await response.json();
            
            if (data.should_block) {
                // Redirect to block page
                const blockPageUrl = browser.runtime.getURL('blocked.html') + 
                    '?url=' + encodeURIComponent(url) +
                    '&reason=' + encodeURIComponent(data.reason) +
                    '&date=' + encodeURIComponent(data.reported_date) +
                    '&attempts=' + data.visit_attempts;
                
                browser.tabs.update(tabId, { url: blockPageUrl });
                
                // Show notification
                browser.notifications.create({
                    type: 'basic',
                    iconUrl: 'icons/icon-48.png',
                    title: 'ScamBat - Site Blocked',
                    message: `This site was blocked because you reported it as a scam.`
                });
            }
        }
    } catch (error) {
        console.error('Error checking URL:', error);
    }
}

// Ensure content script is injected
async function ensureContentScript(tabId) {
    try {
        // Try to ping the content script
        await browser.tabs.sendMessage(tabId, { action: "ping" });
        return true;
    } catch (error) {
        // Content script not loaded, inject it
        try {
            await browser.tabs.executeScript(tabId, {
                file: 'content.js',
                runAt: 'document_idle'
            });
            
            await browser.tabs.insertCSS(tabId, {
                file: 'content.css'
            });
            
            // Wait for content script to initialize
            await new Promise(resolve => setTimeout(resolve, 100));
            return true;
        } catch (e) {
            console.error('Failed to inject content script:', e);
            return false;
        }
    }
}

// Handle context menu clicks
browser.contextMenus.onClicked.addListener(async (info, tab) => {
    console.log('Context menu clicked:', info.menuItemId);
    
    if (info.menuItemId === "report-scam") {
        try {
            const storage = await browser.storage.local.get(['authToken']);
            
            if (!storage.authToken) {
                browser.tabs.create({ url: CONFIG.LOGIN_URL });
                return;
            }
            
            // Ensure content script is loaded
            const injected = await ensureContentScript(tab.id);
            if (!injected) {
                browser.notifications.create({
                    type: 'basic',
                    iconUrl: 'icons/icon-48.png',
                    title: 'ScamBat Error',
                    message: 'Cannot report from this page'
                });
                return;
            }
            
            const contextData = {
                selectedText: info.selectionText || '',
                linkUrl: info.linkUrl || '',
                pageUrl: info.pageUrl || tab.url,
            };
            
            // Send message with retry
            let retries = 3;
            while (retries > 0) {
                try {
                    await browser.tabs.sendMessage(tab.id, {
                        action: "showReportDialog",
                        ...contextData
                    });
                    break;
                } catch (error) {
                    retries--;
                    if (retries > 0) {
                        await new Promise(resolve => setTimeout(resolve, 200));
                    } else {
                        throw error;
                    }
                }
            }
            
        } catch (error) {
            console.error('Context menu error:', error);
            browser.notifications.create({
                type: 'basic',
                iconUrl: 'icons/icon-48.png',
                title: 'ScamBat Error',
                message: 'Failed to open report dialog'
            });
        }
    }
});

// Handle messages
browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log('Background received message:', message.action);
    
    if (message.action === "submitReport") {
        handleScamReport(message.data)
            .then(response => {
                sendResponse(response);
            })
            .catch(error => {
                console.error('Report error:', error);
                sendResponse({
                    success: false,
                    error: error.message
                });
            });
        return true;
        
    } else if (message.action === "checkAuth") {
        checkAuthentication()
            .then(sendResponse)
            .catch(() => sendResponse({ authenticated: false }));
        return true;
        
    } else if (message.action === "openAuthPage") {
        browser.tabs.create({ url: CONFIG.LOGIN_URL });
        sendResponse({ success: true });
        
    } else if (message.action === "storeAuth") {
        browser.storage.local.set({
            authToken: message.token,
            userId: message.user.id,
            username: message.user.username
        }).then(() => {
            sendResponse({ success: true });
        });
        return true;
        
    } else if (message.action === "checkURL") {
        checkURLStatus(message.url)
            .then(sendResponse)
            .catch(error => sendResponse({ error: error.message }));
        return true;
    }
});

async function handleScamReport(reportData) {
    try {
        const result = await browser.storage.local.get(['authToken']);
        
        if (!result.authToken) {
            return {
                success: false, 
                error: 'Not authenticated',
                needsAuth: true
            };
        }

        const response = await fetch(`${CONFIG.API_BASE}/report-scam/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${result.authToken}`
            },
            body: JSON.stringify(reportData)
        });

        const responseText = await response.text();
        
        if (!response.ok) {
            if (response.status === 401) {
                await browser.storage.local.remove(['authToken']);
                return {
                    success: false,
                    error: 'Authentication expired',
                    needsAuth: true
                };
            }
            throw new Error(`HTTP ${response.status}: ${responseText}`);
        }

        const data = JSON.parse(responseText);
        return {
            success: true,
            ...data
        };

    } catch (error) {
        console.error('Report error:', error);
        return {
            success: false,
            error: error.message || 'Network error occurred'
        };
    }
}

async function checkAuthentication() {
    try {
        const result = await browser.storage.local.get(['authToken', 'username']);
        
        if (!result.authToken) {
            return { authenticated: false };
        }

        const response = await fetch(`${CONFIG.API_BASE}/verify-auth/`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${result.authToken}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            return {
                authenticated: true,
                user: {
                    username: result.username || data.user.username,
                    id: data.user.id
                },
                cyberpoints: data.cyberpoints || 0
            };
        } else {
            await browser.storage.local.remove(['authToken']);
            return { authenticated: false };
        }

    } catch (error) {
        console.error('Auth check error:', error);
        return { authenticated: false };
    }
}

async function checkURLStatus(url) {
    const storage = await browser.storage.local.get(['authToken']);
    if (!storage.authToken) {
        return { should_block: false };
    }
    
    const response = await fetch(`${CONFIG.API_BASE}/check-url/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${storage.authToken}`
        },
        body: JSON.stringify({ url })
    });
    
    if (response.ok) {
        return await response.json();
    }
    
    return { should_block: false };
}

// Keep context menu available
browser.runtime.onStartup.addListener(() => {
    createContextMenu();
});