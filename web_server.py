#!/usr/bin/env python3
"""
Web server wrapper for the Simple Stock Tracker application.
"""

import os
import sys
import threading
import time
from datetime import datetime
from typing import List, Dict, Any
from flask import Flask, jsonify, request, render_template, send_file
import pandas as pd
from stock_prices import main as run_stock_fetcher, fetch_stock_data, load_tickers_from_excel
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

def run_job():
    """Background job runner"""
    global job_status
    
    try:
        job_status['status'] = 'running'
        job_status['last_error'] = None
        logger.info("Starting stock data fetch job")
        
        # Clear previous logs
        clear_web_logs()
        
        # Run the stock fetcher (logs will be captured automatically)
        run_stock_fetcher()
        
        # Get captured output
        output = get_web_logs()
        
        job_status['status'] = 'completed'
        job_status['last_run'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        job_status['run_count'] += 1
        
        logger.info("Stock data fetch job completed successfully")
        
    except Exception as e:
        error_msg = str(e)
        job_status['status'] = 'error'
        job_status['last_error'] = error_msg  
        logger.error(f"Job failed: {error_msg}")

@app.route('/')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'Simple Stock Tracker',
        'timestamp': datetime.now().isoformat(),
        'job_status': job_status
    })

@app.route('/favicon.ico')
def favicon():
    """Handle favicon requests."""
    return '', 204

@app.route('/run', methods=['POST'])
def start_job():
    """Start the stock data fetching job."""
    if job_status['status'] == 'running':
        return jsonify({
            'status': 'already_running',
            'message': 'Job is already running'
        }), 409
    
    # Start job in background thread
    job_thread = threading.Thread(target=run_job)
    job_thread.daemon = True
    job_thread.start()
    
    return jsonify({
        'status': 'started',
        'message': 'Stock data fetch job started'
    })

@app.route('/status')
def get_status():
    """Get the current job status."""
    return jsonify(job_status)

@app.route('/logs')
def get_logs():
    """Get the last job output with rotating logs."""
    try:
        logs = get_web_logs()
        return jsonify({
            'logs': logs,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'error': f'Failed to get logs: {str(e)}'
        }), 500

@app.route('/logs', methods=['DELETE'])
def clear_logs():
    """Clear the captured logs."""
    try:
        clear_web_logs()
        return jsonify({
            'message': 'Logs cleared successfully'
        })
    except Exception as e:
        return jsonify({
            'error': f'Failed to clear logs: {str(e)}'
        }), 500

@app.route('/dashboard')
def dashboard():
    """Serve the main dashboard HTML page."""
    return render_template('dashboard.html')

@app.route('/data')
def get_stock_data():
    """Get current stock data from Excel file."""
    try:
        if not os.path.exists(TICKERS_FILE):
            return jsonify([])
        
        # Read Excel file
        df = pd.read_excel(TICKERS_FILE)
        
        # Convert to list of dictionaries
        data = []
        for _, row in df.iterrows():
            stock_data = {}
            for col in df.columns:
                value = row[col]
                if pd.isna(value):
                    stock_data[col] = 'N/A'
                else:
                    stock_data[col] = value
            data.append(stock_data)
        
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Error getting stock data: {e}")
        return jsonify({'error': f'Failed to get stock data: {str(e)}'}), 500

@app.route('/add-ticker', methods=['POST'])
def add_ticker():
    """Add a new ticker to the Excel file."""
    try:
        data = request.get_json()
        ticker = data.get('ticker', '').strip().upper()
        
        if not ticker:
            return jsonify({'error': 'Ticker symbol is required'}), 400
        
        # Load existing tickers
        existing_tickers = load_tickers_from_excel(TICKERS_FILE)
        
        if ticker in existing_tickers:
            return jsonify({'error': f'Ticker {ticker} already exists'}), 400
        
        # Add the new ticker
        existing_tickers.append(ticker)
        
        # Create DataFrame and save to Excel
        df = pd.DataFrame({'Ticker': existing_tickers})
        df.to_excel(TICKERS_FILE, index=False)
        
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
    try:
        if not os.path.exists(TICKERS_FILE):
            return jsonify({'error': 'No data file available'}), 404
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        download_filename = f'stock_data_{timestamp}.xlsx'
        
        return send_file(
            TICKERS_FILE,
            as_attachment=True,
            download_name=download_filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        logger.error(f"Error downloading Excel file: {e}")
        return jsonify({'error': f'Failed to download Excel file: {str(e)}'}), 500

if __name__ == '__main__':
    # Get port from environment (Railway, Heroku, etc.)
    port = int(os.environ.get('PORT', 5000))
    
    # Check if we should run in web mode
    web_mode = os.environ.get('WEB_MODE', 'true').lower() == 'true'
    
    if web_mode:
        logger.info(f"🌐 Starting Simple Stock Tracker Web Server on port {port}")
        logger.info("📡 Health check available at: /")
        logger.info("🚀 Trigger job at: /run")
        logger.info("📊 Check status at: /status")
        logger.info("📝 View logs at: /logs")
        
        app.run(host='0.0.0.0', port=port)
    else:
        # Fall back to running the original script
        logger.info("🔄 Running in worker mode...")
        run_stock_fetcher()