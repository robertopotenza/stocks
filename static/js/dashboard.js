// Dashboard JavaScript functionality

let statusUpdateInterval;
let isJobRunning = false;

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initializing...');
    refreshStatus();
    loadStockData();
    loadLogs();
    
    // Start periodic status updates
    startStatusUpdates();
});

// Start periodic status updates
function startStatusUpdates() {
    if (statusUpdateInterval) {
        clearInterval(statusUpdateInterval);
    }
    
    statusUpdateInterval = setInterval(function() {
        refreshStatus();
        if (isJobRunning) {
            loadLogs(); // Update logs more frequently when job is running
        }
    }, 3000); // Update every 3 seconds
}

// Stop periodic updates
function stopStatusUpdates() {
    if (statusUpdateInterval) {
        clearInterval(statusUpdateInterval);
        statusUpdateInterval = null;
    }
}

// Refresh job status
async function refreshStatus() {
    try {
        const response = await fetch('/status');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        updateStatusDisplay(data);
        
    } catch (error) {
        console.error('Error fetching status:', error);
        showError('Failed to fetch status: ' + error.message);
    }
}

// Update status display elements
function updateStatusDisplay(status) {
    const statusBadge = document.getElementById('status-badge');
    const jobStatus = document.getElementById('job-status');
    const lastRun = document.getElementById('last-run');
    const runCount = document.getElementById('run-count');
    const lastError = document.getElementById('last-error');
    const startButton = document.getElementById('start-job-btn');
    const lastUpdate = document.getElementById('last-update');
    
    // Update status badge and job status
    const statusText = status.status || 'unknown';
    statusBadge.textContent = statusText.charAt(0).toUpperCase() + statusText.slice(1);
    jobStatus.textContent = statusText.charAt(0).toUpperCase() + statusText.slice(1);
    
    // Update status badge class
    statusBadge.className = `badge bg-secondary me-2 status-${statusText}`;
    
    // Update last run
    if (status.last_run) {
        const lastRunDate = new Date(status.last_run);
        lastRun.textContent = lastRunDate.toLocaleString();
    } else {
        lastRun.textContent = 'Never';
    }
    
    // Update run count
    runCount.textContent = status.run_count || 0;
    
    // Update last error
    if (status.last_error) {
        lastError.textContent = status.last_error;
        lastError.className = 'fw-bold text-danger';
    } else {
        lastError.textContent = 'None';
        lastError.className = 'fw-bold text-success';
    }
    
    // Update button state
    isJobRunning = statusText === 'running';
    if (isJobRunning) {
        startButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Running...';
        startButton.disabled = true;
        startButton.className = 'btn btn-warning w-100';
    } else {
        startButton.innerHTML = '<i class="fas fa-play me-2"></i>Start Data Fetch';
        startButton.disabled = false;
        startButton.className = 'btn btn-primary w-100';
    }
    
    // Update last update time
    lastUpdate.textContent = 'Updated: ' + new Date().toLocaleTimeString();
}

// Start stock fetching job
async function startJob() {
    try {
        const response = await fetch('/run');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            showError(data.error);
        } else {
            showSuccess('Stock fetching job started successfully!');
            // Immediately refresh status and start checking more frequently
            setTimeout(refreshStatus, 1000);
        }
        
    } catch (error) {
        console.error('Error starting job:', error);
        showError('Failed to start job: ' + error.message);
    }
}

// Load stock data
async function loadStockData() {
    const loadingDiv = document.getElementById('stock-data-loading');
    const tableContainer = document.getElementById('stock-data-table-container');
    
    try {
        // Show loading state
        loadingDiv.style.display = 'block';
        tableContainer.style.opacity = '0.5';
        
        const response = await fetch('/data');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        updateStockDataTable(data);
        
    } catch (error) {
        console.error('Error loading stock data:', error);
        showError('Failed to load stock data: ' + error.message);
    } finally {
        // Hide loading state
        loadingDiv.style.display = 'none';
        tableContainer.style.opacity = '1';
    }
}

// Update stock data table
function updateStockDataTable(data) {
    const tbody = document.getElementById('stock-data-tbody');
    const totalTickers = document.getElementById('total-tickers');
    
    if (!data || !data.stocks || data.stocks.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="10" class="text-center text-muted py-4">
                    No stock data available. Run stock fetch job to populate data.
                </td>
            </tr>
        `;
        totalTickers.textContent = '0';
        return;
    }
    
    totalTickers.textContent = data.stocks.length;
    
    tbody.innerHTML = data.stocks.map(stock => `
        <tr>
            <td class="fw-bold">${stock.Ticker || 'N/A'}</td>
            <td class="text-price">${formatPrice(stock.Price)}</td>
            <td class="text-price">${formatPrice(stock['52w_High'])}</td>
            <td class="text-price">${formatPrice(stock['52w_Low'])}</td>
            <td>${formatMarketCap(stock.MarketCap)}</td>
            <td>${formatPERatio(stock.PE_Ratio)}</td>
            <td class="text-price">${formatPrice(stock.Pivot_Support_1)}</td>
            <td class="text-price">${formatPrice(stock.Pivot_Resistance_1)}</td>
            <td class="text-price">${formatPrice(stock.Recent_Support)}</td>
            <td class="text-price">${formatPrice(stock.Recent_Resistance)}</td>
        </tr>
    `).join('');
}

// Load logs
async function loadLogs() {
    try {
        const response = await fetch('/logs');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        const logsContent = document.getElementById('logs-content');
        
        if (data.output) {
            logsContent.textContent = data.output;
            // Scroll to bottom
            logsContent.scrollTop = logsContent.scrollHeight;
        } else if (data.message) {
            logsContent.textContent = data.message;
        } else {
            logsContent.textContent = 'No logs available yet...';
        }
        
    } catch (error) {
        console.error('Error loading logs:', error);
        const logsContent = document.getElementById('logs-content');
        logsContent.textContent = 'Error loading logs: ' + error.message;
    }
}

// Add new ticker
async function addTicker() {
    const tickerInput = document.getElementById('tickerSymbol');
    const ticker = tickerInput.value.trim().toUpperCase();
    
    if (!ticker) {
        showError('Please enter a ticker symbol.');
        return;
    }
    
    try {
        const response = await fetch('/api/add_ticker', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ ticker: ticker })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            showError(data.error);
        } else {
            showSuccess(`Ticker ${ticker} added successfully!`);
            tickerInput.value = '';
            
            // Hide modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('addTickerModal'));
            if (modal) {
                modal.hide();
            }
            
            // Refresh data
            loadStockData();
        }
        
    } catch (error) {
        console.error('Error adding ticker:', error);
        showError('Failed to add ticker: ' + error.message);
    }
}

// Utility functions
function formatPrice(price) {
    if (price === null || price === undefined || price === 'N/A' || price === '') {
        return 'N/A';
    }
    
    const numPrice = typeof price === 'string' ? parseFloat(price) : price;
    if (isNaN(numPrice)) {
        return 'N/A';
    }
    
    return '$' + numPrice.toFixed(2);
}

function formatMarketCap(marketCap) {
    if (marketCap === null || marketCap === undefined || marketCap === 'N/A' || marketCap === '') {
        return 'N/A';
    }
    
    const numCap = typeof marketCap === 'string' ? parseFloat(marketCap) : marketCap;
    if (isNaN(numCap)) {
        return 'N/A';
    }
    
    if (numCap >= 1e12) {
        return '$' + (numCap / 1e12).toFixed(2) + 'T';
    } else if (numCap >= 1e9) {
        return '$' + (numCap / 1e9).toFixed(2) + 'B';
    } else if (numCap >= 1e6) {
        return '$' + (numCap / 1e6).toFixed(2) + 'M';
    } else {
        return '$' + numCap.toLocaleString();
    }
}

function formatPERatio(peRatio) {
    if (peRatio === null || peRatio === undefined || peRatio === 'N/A' || peRatio === '') {
        return 'N/A';
    }
    
    const numPE = typeof peRatio === 'string' ? parseFloat(peRatio) : peRatio;
    if (isNaN(numPE)) {
        return 'N/A';
    }
    
    return numPE.toFixed(2);
}

function showSuccess(message) {
    showAlert(message, 'success');
}

function showError(message) {
    showAlert(message, 'danger');
}

function showAlert(message, type) {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.alert');
    existingAlerts.forEach(alert => alert.remove());
    
    // Create new alert
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 5000);
}

// Handle form submission for adding ticker
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('add-ticker-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            addTicker();
        });
    }
    
    // Handle Enter key in ticker input
    const tickerInput = document.getElementById('tickerSymbol');
    if (tickerInput) {
        tickerInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                addTicker();
            }
        });
    }
});

// Clean up on page unload
window.addEventListener('beforeunload', function() {
    stopStatusUpdates();
});