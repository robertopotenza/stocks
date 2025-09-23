// Dashboard JavaScript functionality

let statusUpdateInterval;
let isJobRunning = false;
let currentPollInterval = 15000; // Track current polling interval

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initializing...');
    refreshStatus();
    loadTickerCount();
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

// Load ticker count for summary display
async function loadTickerCount() {
    try {
        const response = await fetch('/data');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        const totalTickers = document.getElementById('total-tickers');
        
        if (data && data.stocks) {
            totalTickers.textContent = data.stocks.length;
        } else {
            totalTickers.textContent = '0';
        }
        
    } catch (error) {
        console.error('Error loading ticker count:', error);
        const totalTickers = document.getElementById('total-tickers');
        totalTickers.textContent = '-';
    }
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
            
            // Refresh ticker count
            loadTickerCount();
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

// Run demo AI evaluation with sample data
async function runDemoEvaluation() {
    const loadingElement = document.getElementById('ai-evaluation-loading');
    const placeholderElement = document.getElementById('ai-evaluation-placeholder');
    const summarySection = document.getElementById('ai-summary-section');
    const rankingsContainer = document.getElementById('ai-rankings-container');
    
    try {
        // Show loading state
        if (loadingElement) loadingElement.style.display = 'block';
        if (placeholderElement) placeholderElement.style.display = 'none';
        if (summarySection) summarySection.style.display = 'none';
        if (rankingsContainer) rankingsContainer.style.display = 'none';
        
        showSuccess('Running demo AI evaluation with sample data...');
        
        const response = await fetch('/demo-evaluation');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Display results
        displayAIEvaluation(data);
        showSuccess('Demo AI evaluation completed! This shows how the AI analyzes real stock data.');
        
    } catch (error) {
        console.error('Error running demo evaluation:', error);
        showError('Demo evaluation failed: ' + error.message);
        
        // Hide loading and show placeholder
        if (loadingElement) loadingElement.style.display = 'none';
        if (placeholderElement) placeholderElement.style.display = 'block';
        
    } finally {
        if (loadingElement) loadingElement.style.display = 'none';
    }
}

// Display AI evaluation results
function displayAIEvaluation(data) {
    const summarySection = document.getElementById('ai-summary-section');
    const rankingsContainer = document.getElementById('ai-rankings-container');
    const placeholderElement = document.getElementById('ai-evaluation-placeholder');
    
    // Hide placeholder
    if (placeholderElement) {
        placeholderElement.style.display = 'none';
    }
    
    // Update summary counts
    const strongBuysCount = document.getElementById('strong-buys-count');
    const buysCount = document.getElementById('buys-count');
    const holdsCount = document.getElementById('holds-count');
    const avoidsCount = document.getElementById('avoids-count');
    
    if (strongBuysCount) strongBuysCount.textContent = data.summary.strong_buys || 0;
    if (buysCount) buysCount.textContent = data.summary.buys || 0;
    if (holdsCount) holdsCount.textContent = data.summary.holds || 0;
    if (avoidsCount) avoidsCount.textContent = (data.summary.avoids || 0) + (data.summary.weak_holds || 0);
    
    // Update top pick
    const topPickInfo = document.getElementById('top-pick-info');
    if (topPickInfo) {
        if (data.summary.top_pick && data.ranked_stocks.length > 0) {
            const topStock = data.ranked_stocks[0];
            topPickInfo.innerHTML = `
                <strong>${topStock.ticker}</strong> with score ${topStock.total_score}/100 
                (${topStock.recommendation}) - ${topStock.commentary}
            `;
        } else {
            topPickInfo.textContent = 'No stocks available for evaluation';
        }
    }
    
    // Show summary section
    if (summarySection) {
        summarySection.style.display = 'block';
    }
    
    // Populate rankings table
    const tbody = document.getElementById('ai-rankings-tbody');
    if (tbody && data.ranked_stocks && data.ranked_stocks.length > 0) {
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
                <td>${formatSentiment(stock.sentiment_data)}</td>
                <td class="small">${stock.commentary}</td>
            </tr>
        `).join('');
        
        // Show rankings container
        if (rankingsContainer) rankingsContainer.style.display = 'block';
    } else if (tbody) {
        tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted py-4">No stocks to display</td></tr>';
        if (rankingsContainer) rankingsContainer.style.display = 'block';
    }
    
    // Display sentiment summary if available
    if (data.sentiment_summary) {
        displaySentimentSummary(data.sentiment_summary);
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

// Sentiment Analysis Functions

// Run sentiment analysis for current tickers
async function runSentimentAnalysis() {
    const loadingElement = document.getElementById('sentiment-analysis-loading');
    const placeholderElement = document.getElementById('sentiment-analysis-placeholder');
    const sentimentSection = document.getElementById('standalone-sentiment-section');
    
    try {
        // Show loading state
        loadingElement.style.display = 'block';
        placeholderElement.style.display = 'none';
        sentimentSection.style.display = 'none';
        
        showSuccess('Analyzing social media sentiment...');
        
        const response = await fetch('/sentiment-analysis');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Display results
        displayStandaloneSentiment(data);
        showSuccess('Sentiment analysis completed successfully!');
        
    } catch (error) {
        console.error('Error running sentiment analysis:', error);
        showError('Sentiment analysis failed: ' + error.message);
        
        // Hide loading and show placeholder
        loadingElement.style.display = 'none';
        placeholderElement.style.display = 'block';
        
    } finally {
        loadingElement.style.display = 'none';
    }
}

// Display standalone sentiment analysis results
function displayStandaloneSentiment(data) {
    const sentimentSection = document.getElementById('standalone-sentiment-section');
    const placeholderElement = document.getElementById('sentiment-analysis-placeholder');
    
    // Hide placeholder
    if (placeholderElement) {
        placeholderElement.style.display = 'none';
    }
    
    // Update summary metrics
    const totalMentions = document.getElementById('standalone-total-mentions');
    const mostPositive = document.getElementById('standalone-most-positive');
    const mostNegative = document.getElementById('standalone-most-negative');
    const avgSentiment = document.getElementById('standalone-average-sentiment');
    
    if (data.portfolio_summary) {
        const summary = data.portfolio_summary;
        if (totalMentions) totalMentions.textContent = summary.total_mentions_across_all_tickers || 0;
        if (mostPositive) mostPositive.textContent = summary.most_positive_ticker || '-';
        if (mostNegative) mostNegative.textContent = summary.most_negative_ticker || '-';
        if (avgSentiment) avgSentiment.textContent = summary.average_sentiment_score || '0.0';
    }
    
    // Populate sentiment table
    const tbody = document.getElementById('standalone-sentiment-tbody');
    if (tbody && data.sentiment_data) {
        const sentimentArray = Object.entries(data.sentiment_data)
            .map(([ticker, sentimentData]) => ({ ticker, ...sentimentData }))
            .sort((a, b) => (b.overall_sentiment_score || 0) - (a.overall_sentiment_score || 0));
        
        tbody.innerHTML = sentimentArray.map((item, index) => `
            <tr class="${getSentimentRowClass(item.overall_sentiment_score)}">
                <td class="fw-bold">${index + 1}</td>
                <td class="fw-bold">${item.ticker}</td>
                <td class="text-center">${item.total_mentions || 0}</td>
                <td class="text-center">${item.sentiment_percentages?.positive || 0}%</td>
                <td class="text-center">${item.sentiment_percentages?.neutral || 0}%</td>
                <td class="text-center">${item.sentiment_percentages?.negative || 0}%</td>
                <td class="text-center">
                    <span class="badge ${getSentimentBadgeClass(item.overall_sentiment_score)}">
                        ${(item.overall_sentiment_score || 0).toFixed(3)}
                    </span>
                </td>
                <td class="text-center">
                    <span class="badge ${getTrendBadgeClass(item.trend_direction)}">
                        ${getTrendIcon(item.trend_direction)} ${item.trend_direction || 'stable'}
                    </span>
                </td>
            </tr>
        `).join('');
    } else if (tbody) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-4">No sentiment data available</td></tr>';
    }
    
    // Show sentiment section
    if (sentimentSection) {
        sentimentSection.style.display = 'block';
    }
}

// Display sentiment summary (when integrated with AI evaluation)
function displaySentimentSummary(sentimentSummary) {
    const sentimentSection = document.getElementById('sentiment-summary-section');
    
    if (!sentimentSection || !sentimentSummary) return;
    
    // Update summary metrics
    const totalMentions = document.getElementById('total-mentions');
    const mostPositive = document.getElementById('most-positive-ticker');
    const mostNegative = document.getElementById('most-negative-ticker');
    const avgSentiment = document.getElementById('average-sentiment');
    
    if (totalMentions) totalMentions.textContent = sentimentSummary.total_mentions_across_portfolio || 0;
    if (mostPositive) mostPositive.textContent = sentimentSummary.most_positive_ticker || '-';
    if (mostNegative) mostNegative.textContent = sentimentSummary.most_negative_ticker || '-';
    if (avgSentiment) avgSentiment.textContent = sentimentSummary.average_sentiment_score || '0.0';
    
    // Populate sentiment table
    const tbody = document.getElementById('sentiment-rankings-tbody');
    if (tbody && sentimentSummary.sentiment_data) {
        const sentimentArray = Object.entries(sentimentSummary.sentiment_data)
            .map(([ticker, sentimentData]) => ({ ticker, ...sentimentData }))
            .sort((a, b) => (b.overall_sentiment_score || 0) - (a.overall_sentiment_score || 0));
        
        tbody.innerHTML = sentimentArray.map(item => `
            <tr class="${getSentimentRowClass(item.overall_sentiment_score)}">
                <td class="fw-bold">${item.ticker}</td>
                <td class="text-center">${item.total_mentions || 0}</td>
                <td class="text-center">${item.sentiment_percentages?.positive || 0}%</td>
                <td class="text-center">${item.sentiment_percentages?.neutral || 0}%</td>
                <td class="text-center">${item.sentiment_percentages?.negative || 0}%</td>
                <td class="text-center">
                    <span class="badge ${getSentimentBadgeClass(item.overall_sentiment_score)}">
                        ${(item.overall_sentiment_score || 0).toFixed(3)}
                    </span>
                </td>
                <td class="text-center">
                    <span class="badge ${getTrendBadgeClass(item.trend_direction)}">
                        ${getTrendIcon(item.trend_direction)} ${item.trend_direction || 'stable'}
                    </span>
                </td>
            </tr>
        `).join('');
    }
    
    // Show sentiment section
    sentimentSection.style.display = 'block';
}

// Format sentiment data for AI evaluation table
function formatSentiment(sentimentData) {
    if (!sentimentData || sentimentData.total_mentions === 0) {
        return '<small class="text-muted">No data</small>';
    }
    
    const score = sentimentData.overall_sentiment_score || 0;
    const mentions = sentimentData.total_mentions || 0;
    const badgeClass = getSentimentBadgeClass(score);
    
    return `
        <div class="text-center">
            <span class="badge ${badgeClass} mb-1">${score.toFixed(2)}</span>
            <br>
            <small class="text-muted">${mentions} mentions</small>
        </div>
    `;
}

// Helper functions for sentiment display
function getSentimentRowClass(score) {
    if (score > 0.2) return 'table-success';
    if (score > 0.05) return 'table-info';
    if (score < -0.2) return 'table-danger';
    if (score < -0.05) return 'table-warning';
    return '';
}

function getSentimentBadgeClass(score) {
    if (score > 0.2) return 'bg-success';
    if (score > 0.05) return 'bg-primary';
    if (score < -0.2) return 'bg-danger';
    if (score < -0.05) return 'bg-warning text-dark';
    return 'bg-secondary';
}

function getTrendBadgeClass(trend) {
    switch (trend) {
        case 'improving':
            return 'bg-success';
        case 'declining':
            return 'bg-danger';
        case 'stable':
        default:
            return 'bg-secondary';
    }
}

function getTrendIcon(trend) {
    switch (trend) {
        case 'improving':
            return '↗';
        case 'declining':
            return '↘';
        case 'stable':
        default:
            return '→';
    }
}