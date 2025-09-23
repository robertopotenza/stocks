#!/usr/bin/env python3
"""
Web server wrapper for the Stock Data Fetcher application.

This module provides a simple Flask web server that can run the stock fetching
process on demand via HTTP endpoints. This allows the application to be deployed
as a web service while maintaining its core batch processing functionality.
"""

import os
import sys
import threading
import time
from datetime import datetime
from flask import Flask, jsonify, request, render_template, send_file
import pandas as pd
from stock_prices import main as run_stock_fetcher, fetch_stock_data, load_tickers_from_excel
from ai_evaluation import evaluate_stock_portfolio
from logging_config import setup_logging, get_web_logs, clear_web_logs, get_logger

# Setup logging with web capture enabled
logger = setup_logging('stocks_app.web_server', enable_web_capture=True)

app = Flask(__name__)

# Configuration
TICKERS_FILE = os.getenv("TICKERS_FILE", "tickers.xlsx")

# Global state to track job status
job_status = {
    'status': 'ready',  # ready, running, completed, error
    'last_run': None,
    'last_error': None,
    'run_count': 0
}

def run_stock_fetcher_async():
    """Run the stock fetcher in a background thread."""
    try:
        job_status['status'] = 'running'
        job_status['last_error'] = None
        
        logger.info("Starting stock fetcher job")
        
        # Clear previous logs for this run
        clear_web_logs()
        
        # Run the stock fetcher (logs will be captured automatically)
        run_stock_fetcher()
        
        # Get captured output
        output = get_web_logs()
        
        job_status['status'] = 'completed'
        job_status['last_run'] = datetime.now().isoformat()
        job_status['run_count'] += 1
        job_status['last_output'] = output
        
        logger.info("Stock fetcher job completed successfully")
        
    except Exception as e:
        job_status['status'] = 'error'
        job_status['last_error'] = str(e)
        logger.error(f"Stock fetcher job failed: {e}")

@app.route('/')
def health_check():
    """Health check endpoint for load balancers."""
    logger.debug("Health check endpoint accessed")
    
    # Check if request accepts HTML (browser request)
    if request.headers.get('Accept', '').find('text/html') != -1:
        # Browser request - redirect to dashboard
        from flask import redirect, url_for
        return redirect(url_for('dashboard'))
    
    # API request - return JSON
    return jsonify({
        'status': 'healthy',
        'service': 'Stock Data Fetcher',
        'timestamp': datetime.now().isoformat(),
        'job_status': job_status
    })

@app.route('/favicon.ico')
def favicon():
    """Handle favicon requests."""
    return '', 204

@app.route('/run')
def run_job():
    """Trigger the stock fetching job."""
    if job_status['status'] == 'running':
        logger.warning("Job start requested but job is already running")
        return jsonify({
            'error': 'Job is already running',
            'status': job_status
        }), 409
    
    logger.info("Starting stock fetching job via web endpoint")
    
    # Start the job in a background thread
    thread = threading.Thread(target=run_stock_fetcher_async)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'message': 'Stock fetching job started',
        'status': job_status
    })

@app.route('/status')
def get_status():
    """Get the current job status."""
    logger.debug("Status endpoint accessed")
    return jsonify(job_status)

@app.route('/logs')
def get_logs():
    """Get the last job output with rotating logs."""
    logger.debug("Logs endpoint accessed")
    
    # Get logs from our rotating log handler
    captured_logs = get_web_logs()
    
    if captured_logs or 'last_output' in job_status:
        return jsonify({
            'status': job_status['status'],
            'last_run': job_status['last_run'],
            'output': captured_logs or job_status.get('last_output', ''),
            'log_source': 'rotating_logs' if captured_logs else 'legacy_output'
        })
    else:
        return jsonify({
            'message': 'No logs available yet',
            'status': job_status['status']
        })

@app.route('/dashboard')
def dashboard():
    """Serve the main dashboard HTML page."""
    logger.debug("Dashboard page accessed")
    return render_template('dashboard.html')

@app.route('/data')
def get_stock_data():
    """Get current stock data from Excel file."""
    logger.debug("Stock data endpoint accessed")
    
    try:
        if not os.path.exists(TICKERS_FILE):
            return jsonify({
                'error': 'Tickers file not found',
                'stocks': []
            })
        
        # Read Excel file
        df = pd.read_excel(TICKERS_FILE)
        
        # Convert to list of dictionaries
        stocks = df.to_dict(orient='records')
        
        return jsonify({
            'stocks': stocks,
            'count': len(stocks),
            'file': TICKERS_FILE
        })
        
    except Exception as e:
        logger.error(f"Error reading stock data: {e}")
        return jsonify({
            'error': f'Failed to read stock data: {str(e)}',
            'stocks': []
        }), 500

@app.route('/add-ticker', methods=['POST'])
def add_ticker():
    """Add a new ticker to the Excel file."""
    logger.debug("Add ticker endpoint accessed")
    
    try:
        data = request.get_json()
        if not data or 'ticker' not in data:
            return jsonify({'error': 'Ticker symbol is required'}), 400
        
        ticker = data['ticker'].strip().upper()
        if not ticker:
            return jsonify({'error': 'Invalid ticker symbol'}), 400
        
        # Read existing Excel file or create new DataFrame
        if os.path.exists(TICKERS_FILE):
            df = pd.read_excel(TICKERS_FILE)
        else:
            df = pd.DataFrame(columns=['Ticker'])
        
        # Check if ticker already exists
        if 'Ticker' in df.columns and ticker in df['Ticker'].values:
            return jsonify({'error': f'Ticker {ticker} already exists'}), 400
        
        # Add new ticker
        new_row = pd.DataFrame([{'Ticker': ticker}])
        df = pd.concat([df, new_row], ignore_index=True)
        
        # Save to Excel file
        df.to_excel(TICKERS_FILE, index=False)
        
        logger.info(f"Added ticker {ticker} to {TICKERS_FILE}")
        return jsonify({
            'message': f'Ticker {ticker} added successfully',
            'ticker': ticker
        })
        
    except Exception as e:
        logger.error(f"Error adding ticker: {e}")
        return jsonify({'error': f'Failed to add ticker: {str(e)}'}), 500

@app.route('/download-excel')
def download_excel():
    """Download the current stock data Excel file."""
    logger.debug("Excel download endpoint accessed")
    
    try:
        if not os.path.exists(TICKERS_FILE):
            return jsonify({
                'error': 'No stock data file available for download'
            }), 404
        
        # Generate a filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        download_filename = f"stock_data_{timestamp}.xlsx"
        
        logger.info(f"Serving Excel file download: {TICKERS_FILE} as {download_filename}")
        
        return send_file(
            TICKERS_FILE,
            as_attachment=True,
            download_name=download_filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        logger.error(f"Error downloading Excel file: {e}")
        return jsonify({'error': f'Failed to download Excel file: {str(e)}'}), 500

@app.route('/ai-evaluation')
def get_ai_evaluation():
    """Get AI-powered stock evaluation and rankings."""
    logger.debug("AI evaluation endpoint accessed")
    
    try:
        # Load current stock data from Excel file
        if not os.path.exists(TICKERS_FILE):
            return jsonify({
                'error': 'No stock data available for evaluation. Run stock fetch job first.'
            }), 404
        
        # Read the Excel file to get stock data
        df = pd.read_excel(TICKERS_FILE)
        
        # Check if we have the required columns for evaluation
        required_columns = ['Ticker', 'Price', 'PE_Ratio']
        if not all(col in df.columns for col in required_columns):
            return jsonify({
                'error': 'Stock data is incomplete. Run stock fetch job to get latest data.'
            }), 400
        
        # Convert DataFrame to the format expected by AI evaluation
        stock_data = {}
        for _, row in df.iterrows():
            ticker = row['Ticker']
            # Convert row to dictionary, handling NaN values
            data = {}
            for col in df.columns:
                value = row[col]
                if pd.isna(value):
                    data[col] = 'N/A'
                else:
                    data[col] = value
            stock_data[ticker] = data
        
        # Run AI evaluation
        logger.info(f"Running AI evaluation on {len(stock_data)} stocks")
        evaluation_result = evaluate_stock_portfolio(stock_data)
        
        logger.info(f"AI evaluation completed. Top pick: {evaluation_result['summary'].get('top_pick', 'None')}")
        
        return jsonify(evaluation_result)
        
    except Exception as e:
        logger.error(f"Error in AI evaluation: {e}")
        return jsonify({'error': f'Failed to perform AI evaluation: {str(e)}'}), 500

@app.route('/quick-evaluation')
def get_quick_evaluation():
    """Get a quick AI evaluation using live data (without full stock fetch)."""
    logger.debug("Quick evaluation endpoint accessed")
    
    try:
        # Load tickers from Excel file
        if not os.path.exists(TICKERS_FILE):
            return jsonify({
                'error': 'No tickers file found. Please add some tickers first.'
            }), 404
        
        # Check if credentials are available for quick fetch
        username = os.getenv("ROBINHOOD_USERNAME", "your_email")
        password = os.getenv("ROBINHOOD_PASSWORD", "your_password") 
        
        if username == "your_email" or password == "your_password":
            return jsonify({
                'error': 'Robinhood credentials not configured for quick evaluation.'
            }), 400
        
        # Load tickers
        tickers = load_tickers_from_excel(TICKERS_FILE)
        if not tickers:
            return jsonify({
                'error': 'No valid tickers found in file.'
            }), 400
        
        # Limit to first 10 tickers for quick evaluation
        limited_tickers = tickers[:10]
        logger.info(f"Running quick evaluation on {len(limited_tickers)} tickers")
        
        # Fetch fresh stock data
        stock_data = fetch_stock_data(limited_tickers)
        
        if not stock_data:
            return jsonify({
                'error': 'Failed to fetch stock data for evaluation.'
            }), 500
        
        # Run AI evaluation
        evaluation_result = evaluate_stock_portfolio(stock_data)
        
        logger.info(f"Quick AI evaluation completed. Top pick: {evaluation_result['summary'].get('top_pick', 'None')}")
        
        return jsonify(evaluation_result)
        
    except Exception as e:
        logger.error(f"Error in quick evaluation: {e}")
        return jsonify({'error': f'Failed to perform quick evaluation: {str(e)}'}), 500

@app.route('/demo-evaluation')
def get_demo_evaluation():
    """Get a demo AI evaluation using sample data for testing."""
    logger.debug("Demo evaluation endpoint accessed")
    
    try:
        # Create sample stock data for demonstration
        sample_data = {
            'AAPL': {
                'Price': 175.25,
                '52w_High': 199.62,
                '52w_Low': 124.17,
                'MarketCap': 2750000000000,
                'PE_Ratio': 28.5,
                'Pivot_Support_1': 172.50,
                'Pivot_Support_2': 168.75,
                'Pivot_Resistance_1': 178.40,
                'Pivot_Resistance_2': 182.15,
                'Recent_Support': 170.25,
                'Recent_Resistance': 180.60,
                'Risk_Reward_Ratio': 2.3,
                'Distance_from_52w_High_Pct': 12.2,
                'Distance_from_52w_Low_Pct': 41.1,
                'Upside_Potential_Pct': 18.5,
                'Downside_Risk_Pct': 8.2,
                'Valuation_Flag': 'Fair Value',
                'Entry_Opportunity_Flag': 'Favorable',
                'Price_Level_Flag': 'Mid Range'
            },
            'GOOGL': {
                'Price': 2785.50,
                '52w_High': 3030.93,
                '52w_Low': 2193.62,
                'MarketCap': 1850000000000,
                'PE_Ratio': 24.8,
                'Pivot_Support_1': 2750.25,
                'Pivot_Support_2': 2690.80,
                'Pivot_Resistance_1': 2820.75,
                'Pivot_Resistance_2': 2880.40,
                'Recent_Support': 2765.30,
                'Recent_Resistance': 2810.90,
                'Risk_Reward_Ratio': 1.8,
                'Distance_from_52w_High_Pct': 8.1,
                'Distance_from_52w_Low_Pct': 27.0,
                'Upside_Potential_Pct': 12.8,
                'Downside_Risk_Pct': 7.1,
                'Valuation_Flag': 'Fair Value',
                'Entry_Opportunity_Flag': 'Neutral',
                'Price_Level_Flag': 'Mid Range'
            },
            'TSLA': {
                'Price': 245.80,
                '52w_High': 299.29,
                '52w_Low': 138.80,
                'MarketCap': 780000000000,
                'PE_Ratio': 65.2,
                'Pivot_Support_1': 235.60,
                'Pivot_Support_2': 220.45,
                'Pivot_Resistance_1': 260.25,
                'Pivot_Resistance_2': 275.80,
                'Recent_Support': 240.15,
                'Recent_Resistance': 255.70,
                'Risk_Reward_Ratio': 1.2,
                'Distance_from_52w_High_Pct': 17.9,
                'Distance_from_52w_Low_Pct': 77.1,
                'Upside_Potential_Pct': 9.5,
                'Downside_Risk_Pct': 8.1,
                'Valuation_Flag': 'Overvalued',
                'Entry_Opportunity_Flag': 'Unfavorable',
                'Price_Level_Flag': 'Mid Range'
            },
            'NVDA': {
                'Price': 118.75,
                '52w_High': 140.76,
                '52w_Low': 39.23,
                'MarketCap': 2920000000000,
                'PE_Ratio': 32.8,
                'Pivot_Support_1': 115.20,
                'Pivot_Support_2': 108.45,
                'Pivot_Resistance_1': 125.30,
                'Pivot_Resistance_2': 132.85,
                'Recent_Support': 112.60,
                'Recent_Resistance': 128.90,
                'Risk_Reward_Ratio': 3.1,
                'Distance_from_52w_High_Pct': 15.6,
                'Distance_from_52w_Low_Pct': 202.6,
                'Upside_Potential_Pct': 22.4,
                'Downside_Risk_Pct': 7.2,
                'Valuation_Flag': 'Overvalued',
                'Entry_Opportunity_Flag': 'Favorable',
                'Price_Level_Flag': 'Mid Range'
            },
            'MSFT': {
                'Price': 415.30,
                '52w_High': 468.35,
                '52w_Low': 309.45,
                'MarketCap': 3080000000000,
                'PE_Ratio': 34.2,
                'Pivot_Support_1': 405.85,
                'Pivot_Support_2': 395.20,
                'Pivot_Resistance_1': 425.75,
                'Pivot_Resistance_2': 435.80,
                'Recent_Support': 408.90,
                'Recent_Resistance': 422.15,
                'Risk_Reward_Ratio': 1.6,
                'Distance_from_52w_High_Pct': 11.3,
                'Distance_from_52w_Low_Pct': 34.2,
                'Upside_Potential_Pct': 8.5,
                'Downside_Risk_Pct': 5.3,
                'Valuation_Flag': 'Overvalued',
                'Entry_Opportunity_Flag': 'Neutral',
                'Price_Level_Flag': 'Mid Range'
            },
            'META': {
                'Price': 485.20,
                '52w_High': 542.81,
                '52w_Low': 279.70,
                'MarketCap': 1240000000000,
                'PE_Ratio': 22.1,
                'Pivot_Support_1': 475.40,
                'Pivot_Support_2': 465.85,
                'Pivot_Resistance_1': 495.60,
                'Pivot_Resistance_2': 510.25,
                'Recent_Support': 478.30,
                'Recent_Resistance': 492.80,
                'Risk_Reward_Ratio': 2.8,
                'Distance_from_52w_High_Pct': 10.6,
                'Distance_from_52w_Low_Pct': 73.5,
                'Upside_Potential_Pct': 16.2,
                'Downside_Risk_Pct': 5.8,
                'Valuation_Flag': 'Fair Value',
                'Entry_Opportunity_Flag': 'Favorable',
                'Price_Level_Flag': 'Mid Range'
            }
        }
        
        logger.info("Running demo AI evaluation with sample data")
        
        # Run AI evaluation on sample data
        evaluation_result = evaluate_stock_portfolio(sample_data)
        
        logger.info(f"Demo AI evaluation completed. Top pick: {evaluation_result['summary'].get('top_pick', 'None')}")
        
        return jsonify(evaluation_result)
        
    except Exception as e:
        logger.error(f"Error in demo evaluation: {e}")
        return jsonify({'error': f'Failed to perform demo evaluation: {str(e)}'}), 500

if __name__ == '__main__':
    # Get port from environment (Railway, Heroku, etc.)
    port = int(os.environ.get('PORT', 5000))
    
    # Check if we should run in web mode
    web_mode = os.environ.get('WEB_MODE', 'true').lower() == 'true'
    
    if web_mode:
        logger.info(f"🌐 Starting Stock Data Fetcher Web Server on port {port}")
        logger.info("📡 Health check available at: /")
        logger.info("🚀 Trigger job at: /run")
        logger.info("📊 Check status at: /status")
        logger.info("📝 View logs at: /logs")
        
        app.run(host='0.0.0.0', port=port)
    else:
        # Fall back to running the original script
        logger.info("🔄 Running in worker mode...")
        run_stock_fetcher()