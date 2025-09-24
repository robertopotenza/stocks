// Simple Stock Tracker Dashboard JavaScript

let statusUpdateInterval;
let isJobRunning = false;

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initializing...');
    refreshStatus();
    loadTickerCount();
    loadLogs();
    loadStockData();
    
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
            loadLogs();
        }
    }, 10000); // Update every 10 seconds
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
        const data = await response.json();
        
        // Update status displays
        document.getElementById('status-badge').textContent = data.status;
        document.getElementById('job-status').textContent = data.status;
        document.getElementById('last-run').textContent = data.last_run || 'Never';
        document.getElementById('run-count').textContent = data.run_count || 0;
        document.getElementById('last-error').textContent = data.last_error || 'None';
        document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
        
        // Update running state
        const wasRunning = isJobRunning;
        isJobRunning = data.status === 'running';
        
        // If job finished, reload stock data
        if (wasRunning && !isJobRunning && data.status === 'completed') {
            loadStockData();
        }
        
        // Update button states
        const startBtn = document.getElementById('start-job-btn');
        if (isJobRunning) {
            startBtn.disabled = true;
            startBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Running...';
        } else {
            startBtn.disabled = false;
            startBtn.innerHTML = '<i class="fas fa-play me-2"></i>Fetch Stock Data';
        }
        
    } catch (error) {
        console.error('Error refreshing status:', error);
    }
}

// Start job
async function startJob() {
    try {
        const response = await fetch('/run', { method: 'POST' });
        const data = await response.json();
        
        if (data.status === 'started') {
            showSuccess('Stock data fetch started successfully!');
            refreshStatus();
        } else {
            showError(data.message || 'Failed to start job');
        }
    } catch (error) {
        console.error('Error starting job:', error);
        showError('Error starting job: ' + error.message);
    }
}

// Load ticker count
async function loadTickerCount() {
    try {
        const response = await fetch('/data');
        const data = await response.json();
        
        if (Array.isArray(data)) {
            document.getElementById('total-tickers').textContent = data.length;
        } else {
            document.getElementById('total-tickers').textContent = '0';
        }
    } catch (error) {
        console.error('Error loading ticker count:', error);
        document.getElementById('total-tickers').textContent = 'Error';
    }
}

// Load stock data
async function loadStockData() {
    try {
        const response = await fetch('/data');
        const data = await response.json();
        
        const tbody = document.getElementById('stock-data-tbody');
        
        if (Array.isArray(data) && data.length > 0) {
            tbody.innerHTML = '';
            
            data.forEach(stock => {
                const row = document.createElement('tr');
                const price = typeof stock.Price === 'number' ? `$${stock.Price.toFixed(2)}` : stock.Price;
                
                row.innerHTML = `
                    <td><strong>${stock.Ticker}</strong></td>
                    <td>${price}</td>
                `;
                
                tbody.appendChild(row);
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="2" class="text-center text-muted py-4">No stock data available</td></tr>';
        }
        
    } catch (error) {
        console.error('Error loading stock data:', error);
        const tbody = document.getElementById('stock-data-tbody');
        tbody.innerHTML = '<tr><td colspan="2" class="text-center text-danger py-4">Error loading data</td></tr>';
    }
}

// Load logs
async function loadLogs() {
    try {
        const response = await fetch('/logs');
        const data = await response.json();
        
        const logContainer = document.getElementById('log-container');
        if (data.logs && Array.isArray(data.logs)) {
            logContainer.innerHTML = data.logs.join('\n');
            logContainer.scrollTop = logContainer.scrollHeight;
        }
    } catch (error) {
        console.error('Error loading logs:', error);
    }
}

// Clear logs
async function clearLogs() {
    try {
        const response = await fetch('/logs', { method: 'DELETE' });
        if (response.ok) {
            document.getElementById('log-container').innerHTML = '<div class="text-muted">Logs cleared</div>';
            showSuccess('Logs cleared successfully');
        }
    } catch (error) {
        console.error('Error clearing logs:', error);
        showError('Error clearing logs');
    }
}

// Add new ticker
async function addTicker() {
    const tickerInput = document.getElementById('ticker-input');
    const ticker = tickerInput.value.trim().toUpperCase();
    
    if (!ticker) {
        showError('Please enter a ticker symbol');
        return;
    }
    
    try {
        const response = await fetch('/add-ticker', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ ticker: ticker })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showSuccess(`Ticker ${ticker} added successfully!`);
            tickerInput.value = '';
            loadTickerCount();
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('addTickerModal'));
            if (modal) {
                modal.hide();
            }
        } else {
            showError(data.error || 'Failed to add ticker');
        }
    } catch (error) {
        console.error('Error adding ticker:', error);
        showError('Error adding ticker: ' + error.message);
    }
}

// Download Excel file
function downloadExcel() {
    window.location.href = '/download-excel';
}

// Utility functions
function showSuccess(message) {
    showAlert(message, 'success');
}

function showError(message) {
    showAlert(message, 'danger');
}

function showAlert(message, type) {
    // Create alert element
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alert);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.parentNode.removeChild(alert);
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
    const tickerInput = document.getElementById('ticker-input');
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