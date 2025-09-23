// Dashboard JavaScript functionality

let statusUpdateInterval;
let isJobRunning = false;
let currentPollInterval = 15000; // Track current polling interval

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
    
    // Intelligent polling: faster when job is running, slower when idle
    const pollInterval = isJobRunning ? 5000 : 15000; // 5s when running, 15s when idle
    currentPollInterval = pollInterval;
    
    statusUpdateInterval = setInterval(function() {
        refreshStatus();
        if (isJobRunning) {
            loadLogs(); // Update logs when job is running
        }
    }, pollInterval);
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
    
    // Check if job status changed and adjust polling frequency
    const wasRunning = isJobRunning;
    isJobRunning = statusText === 'running';
    
    // Update button state
    if (isJobRunning) {
        startButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Running...';
        startButton.disabled = true;
        startButton.className = 'btn btn-warning w-100';
    } else {
        startButton.innerHTML = '<i class="fas fa-play me-2"></i>Start Data Fetch';
        startButton.disabled = false;
        startButton.className = 'btn btn-primary w-100';
    }
    
    // If job status changed, restart polling with appropriate frequency
    if (wasRunning !== isJobRunning) {
        console.log(`Job status changed: ${wasRunning ? 'running' : 'idle'} -> ${isJobRunning ? 'running' : 'idle'}`);
        const newPollInterval = isJobRunning ? 5000 : 15000;
        if (newPollInterval !== currentPollInterval) {
            startStatusUpdates(); // Restart with new frequency
        }
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
    const downloadBtn = document.getElementById('download-excel-btn');
    
    if (!data || !data.stocks || data.stocks.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="10" class="text-center text-muted py-4">
                    No stock data available. Run stock fetch job to populate data.
                </td>
            </tr>
        `;
        totalTickers.textContent = '0';
        // Hide download button when no data
        if (downloadBtn) {
            downloadBtn.style.display = 'none';
        }
        return;
    }
    
    totalTickers.textContent = data.stocks.length;
    
    // Show download button when data is available
    if (downloadBtn) {
        downloadBtn.style.display = 'inline-block';
    }
    
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
    const tickerInput = document.getElementById('ticker-input');
    const ticker = tickerInput.value.trim().toUpperCase();
    
    if (!ticker) {
        showError('Please enter a ticker symbol.');
        return;
    }
    
    try {
        const response = await fetch('/add-ticker', {
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
            const modal = document.getElementById('addTickerModal');
            if (modal) {
                // Try to use Bootstrap modal if available
                if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                    const bootstrapModal = bootstrap.Modal.getInstance(modal);
                    if (bootstrapModal) {
                        bootstrapModal.hide();
                    }
                } else {
                    // Fallback: hide modal manually
                    modal.style.display = 'none';
                    modal.classList.remove('show');
                    modal.setAttribute('aria-hidden', 'true');
                    
                    // Remove backdrop if exists
                    const backdrop = document.querySelector('.modal-backdrop');
                    if (backdrop) {
                        backdrop.remove();
                    }
                    
                    // Remove modal-open class from body
                    document.body.classList.remove('modal-open');
                    document.body.style.paddingRight = '';
                }
            }
            
            // Refresh data
            loadStockData();
        }
        
    } catch (error) {
        console.error('Error adding ticker:', error);
        showError('Failed to add ticker: ' + error.message);
    }
}

// Download Excel file
async function downloadExcel() {
    try {
        showSuccess('Downloading Excel file...');
        
        // Create a temporary link element and trigger download
        const link = document.createElement('a');
        link.href = '/download-excel';
        link.download = ''; // Let the server set the filename
        
        // Append to body, click, and remove
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
    } catch (error) {
        console.error('Error downloading Excel file:', error);
        showError('Failed to download Excel file: ' + error.message);
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

// AI Evaluation Functions

// Run AI evaluation using existing stock data
async function runAIEvaluation() {
    const loadingElement = document.getElementById('ai-evaluation-loading');
    const placeholderElement = document.getElementById('ai-evaluation-placeholder');
    const summarySection = document.getElementById('ai-summary-section');
    const rankingsContainer = document.getElementById('ai-rankings-container');
    
    try {
        // Show loading state
        loadingElement.style.display = 'block';
        placeholderElement.style.display = 'none';
        summarySection.style.display = 'none';
        rankingsContainer.style.display = 'none';
        
        showSuccess('Running AI analysis on current stock data...');
        
        const response = await fetch('/ai-evaluation');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Display results
        displayAIEvaluation(data);
        showSuccess('AI analysis completed successfully!');
        
    } catch (error) {
        console.error('Error running AI evaluation:', error);
        showError('AI evaluation failed: ' + error.message);
        
        // Hide loading and show placeholder
        loadingElement.style.display = 'none';
        placeholderElement.style.display = 'block';
        
    } finally {
        loadingElement.style.display = 'none';
    }
}

// Run quick AI evaluation with fresh data
async function runQuickEvaluation() {
    const loadingElement = document.getElementById('ai-evaluation-loading');
    const placeholderElement = document.getElementById('ai-evaluation-placeholder');
    const summarySection = document.getElementById('ai-summary-section');
    const rankingsContainer = document.getElementById('ai-rankings-container');
    
    try {
        // Show loading state
        loadingElement.style.display = 'block';
        placeholderElement.style.display = 'none';
        summarySection.style.display = 'none';
        rankingsContainer.style.display = 'none';
        
        showSuccess('Running quick AI evaluation with fresh data...');
        
        const response = await fetch('/quick-evaluation');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Display results
        displayAIEvaluation(data);
        showSuccess('Quick AI evaluation completed!');
        
    } catch (error) {
        console.error('Error running quick evaluation:', error);
        showError('Quick evaluation failed: ' + error.message);
        
        // Hide loading and show placeholder
        loadingElement.style.display = 'none';
        placeholderElement.style.display = 'block';
        
    } finally {
        loadingElement.style.display = 'none';
    }
}

// Display AI evaluation results
function displayAIEvaluation(data) {
    const summarySection = document.getElementById('ai-summary-section');
    const rankingsContainer = document.getElementById('ai-rankings-container');
    const placeholderElement = document.getElementById('ai-evaluation-placeholder');
    
    // Hide placeholder
    placeholderElement.style.display = 'none';
    
    // Update summary counts
    document.getElementById('strong-buys-count').textContent = data.summary.strong_buys || 0;
    document.getElementById('buys-count').textContent = data.summary.buys || 0;
    document.getElementById('holds-count').textContent = data.summary.holds || 0;
    document.getElementById('avoids-count').textContent = (data.summary.avoids || 0) + (data.summary.weak_holds || 0);
    
    // Update top pick
    const topPickInfo = document.getElementById('top-pick-info');
    if (data.summary.top_pick && data.ranked_stocks.length > 0) {
        const topStock = data.ranked_stocks[0];
        topPickInfo.innerHTML = `
            <strong>${topStock.ticker}</strong> with score ${topStock.total_score}/100 
            (${topStock.recommendation}) - ${topStock.commentary}
        `;
    } else {
        topPickInfo.textContent = 'No stocks available for evaluation';
    }
    
    // Show summary section
    summarySection.style.display = 'block';
    
    // Populate rankings table
    const tbody = document.getElementById('ai-rankings-tbody');
    if (data.ranked_stocks && data.ranked_stocks.length > 0) {
        tbody.innerHTML = data.ranked_stocks.map((stock, index) => `
            <tr class="${getRecommendationRowClass(stock.recommendation)}">
                <td class="fw-bold">${index + 1}</td>
                <td class="fw-bold">${stock.ticker}</td>
                <td>
                    <div class="d-flex align-items-center">
                        <span class="fw-bold me-2">${stock.total_score}</span>
                        <div class="progress flex-grow-1" style="height: 6px;">
                            <div class="progress-bar ${getScoreProgressClass(stock.total_score)}" 
                                 style="width: ${stock.total_score}%"></div>
                        </div>
                    </div>
                </td>
                <td>
                    <span class="badge ${getRecommendationBadgeClass(stock.recommendation)}">
                        ${stock.recommendation}
                    </span>
                </td>
                <td class="text-price">${formatPrice(stock.price)}</td>
                <td>${formatPERatio(stock.pe_ratio)}</td>
                <td>${formatRiskReward(stock.risk_reward_ratio)}</td>
                <td class="small">${stock.commentary}</td>
            </tr>
        `).join('');
        
        // Show rankings container
        rankingsContainer.style.display = 'block';
    } else {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-4">No stocks to display</td></tr>';
        rankingsContainer.style.display = 'block';
    }
}

// Helper functions for AI evaluation display
function getRecommendationRowClass(recommendation) {
    switch (recommendation) {
        case 'Strong Buy':
            return 'table-success';
        case 'Buy':
            return 'table-info';
        case 'Hold':
            return 'table-warning';
        case 'Weak Hold':
            return 'table-secondary';
        case 'Avoid':
            return 'table-danger';
        default:
            return '';
    }
}

function getRecommendationBadgeClass(recommendation) {
    switch (recommendation) {
        case 'Strong Buy':
            return 'bg-success';
        case 'Buy':
            return 'bg-primary';
        case 'Hold':
            return 'bg-warning text-dark';
        case 'Weak Hold':
            return 'bg-secondary';
        case 'Avoid':
            return 'bg-danger';
        default:
            return 'bg-secondary';
    }
}

function getScoreProgressClass(score) {
    if (score >= 75) return 'bg-success';
    if (score >= 60) return 'bg-primary';
    if (score >= 45) return 'bg-warning';
    if (score >= 30) return 'bg-secondary';
    return 'bg-danger';
}

function formatRiskReward(riskReward) {
    if (riskReward === null || riskReward === undefined || riskReward === 'N/A' || riskReward === '') {
        return 'N/A';
    }
    
    const numRR = typeof riskReward === 'string' ? parseFloat(riskReward) : riskReward;
    if (isNaN(numRR)) {
        return 'N/A';
    }
    
    return numRR.toFixed(2);
}