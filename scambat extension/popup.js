const API_BASE = 'http://localhost:8000';

document.addEventListener('DOMContentLoaded', () => {
    checkAuthStatus();
    setupEventListeners();
});

function setupEventListeners() {
    const connectBtn = document.getElementById('connect-btn');
    const disconnectBtn = document.getElementById('disconnect-btn');
    const quickReportBtn = document.getElementById('quick-report-btn');
    const dashboardBtn = document.getElementById('dashboard-btn');
    const viewHistoryBtn = document.getElementById('view-history-btn');
    
    if (connectBtn) connectBtn.addEventListener('click', handleConnect);
    if (disconnectBtn) disconnectBtn.addEventListener('click', handleDisconnect);
    if (quickReportBtn) quickReportBtn.addEventListener('click', handleQuickReport);
    if (dashboardBtn) dashboardBtn.addEventListener('click', handleDashboard);
    if (viewHistoryBtn) viewHistoryBtn.addEventListener('click', handleViewHistory);
}

function showState(state) {
    ['loading', 'authenticated', 'not-authenticated'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.classList.toggle('hidden', id !== state);
        }
    });
}

async function checkAuthStatus() {
    showState('loading');
    
    try {
        const response = await browser.runtime.sendMessage({ action: "checkAuth" });
        
        if (response && response.authenticated) {
            showAuthenticated(response.user.username, response.cyberpoints || 0);
        } else {
            showState('not-authenticated');
        }
    } catch (error) {
        console.error('Auth check error:', error);
        showState('not-authenticated');
    }
}

function showAuthenticated(username, points) {
    const usernameEl = document.getElementById('username');
    const pointsEl = document.getElementById('cyberpoints');
    
    if (usernameEl) usernameEl.textContent = username;
    if (pointsEl) pointsEl.textContent = `${points} ⭐`;
    
    showState('authenticated');
}

async function handleConnect() {
    await browser.tabs.create({ url: `${API_BASE}/extension/auth/` });
    window.close();
}

async function handleDisconnect() {
    if (confirm('Disconnect your ScamBat account?')) {
        await browser.storage.local.clear();
        showState('not-authenticated');
    }
}

async function handleQuickReport() {
    try {
        const tabs = await browser.tabs.query({ active: true, currentWindow: true });
        const currentTab = tabs[0];
        
        // Ensure content script is loaded
        await browser.tabs.executeScript(currentTab.id, {
            file: 'content.js'
        });
        
        await browser.tabs.insertCSS(currentTab.id, {
            file: 'content.css'
        });
        
        setTimeout(() => {
            browser.tabs.sendMessage(currentTab.id, {
                action: "showReportDialog",
                pageUrl: currentTab.url,
                fullPage: true
            });
        }, 100);
        
        window.close();
    } catch (error) {
        console.error('Quick report error:', error);
        alert('Cannot report from this page');
    }
}

function handleDashboard() {
    browser.tabs.create({ url: `${API_BASE}/profile/` });
    window.close();
}

function handleViewHistory() {
    browser.tabs.create({ url: `${API_BASE}/reports/history/` });
    window.close();
}