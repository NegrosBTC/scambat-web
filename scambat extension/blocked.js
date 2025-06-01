document.addEventListener('DOMContentLoaded', () => {
    // Parse URL parameters
    const params = new URLSearchParams(window.location.search);
    const blockedUrl = params.get('url');
    const reason = params.get('reason');
    const reportDate = params.get('date');
    const attempts = params.get('attempts');
    
    // Display information
    document.getElementById('blocked-url').textContent = blockedUrl || 'Unknown';
    document.getElementById('block-reason').textContent = reason || 'No reason provided';
    document.getElementById('report-date').textContent = 
        reportDate ? new Date(reportDate).toLocaleDateString() : 'Unknown';
    
    if (attempts && parseInt(attempts) > 0) {
        document.getElementById('attempt-count').textContent = 
            `⚠️ You've tried to visit this site ${attempts} time${attempts > 1 ? 's' : ''} since reporting it`;
    }
    
    // Button handlers
    document.getElementById('go-back').addEventListener('click', () => {
        window.history.back();
    });
    
    document.getElementById('view-history').addEventListener('click', () => {
        browser.tabs.create({ url: 'http://localhost:8000/reports/history/' });
    });
    
    document.getElementById('history-link').addEventListener('click', (e) => {
        e.preventDefault();
        browser.tabs.create({ url: 'http://localhost:8000/reports/history/' });
    });
});