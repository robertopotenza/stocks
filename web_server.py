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
from flask import Flask, jsonify, request
from stock_prices import main as run_stock_fetcher
from logging_config import setup_logging, get_web_logs, clear_web_logs, get_logger

# Setup logging with web capture enabled
logger = setup_logging('stocks_app.web_server', enable_web_capture=True)

app = Flask(__name__)

# Global state to track job status
job_status = {
    'status': 'ready',  # ready, running, completed, error
    'last_run': None,
    'last_error': None,
    'run_count': 0
}

# HTML template for browser users
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stock Data Fetcher</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; line-height: 1.6; }
        .header { background: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .status { background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .endpoints { background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .button { display: inline-block; background: #007bff; color: white; padding: 10px 20px; 
                  text-decoration: none; border-radius: 3px; margin: 5px 0; }
        .button:hover { background: #0056b3; }
        .timestamp { color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Stock Data Fetcher</h1>
        <p>Web interface for the Robinhood stock data fetching service</p>
    </div>
    
    <div class="status">
        <h2>Service Status</h2>
        <p><strong>Status:</strong> SERVICE_STATUS_PLACEHOLDER</p>
        <p><strong>Service:</strong> SERVICE_NAME_PLACEHOLDER</p>
        <p><strong>Job Status:</strong> JOB_STATUS_PLACEHOLDER</p>
        <p><strong>Run Count:</strong> RUN_COUNT_PLACEHOLDER</p>
        LAST_RUN_PLACEHOLDER
        LAST_ERROR_PLACEHOLDER
        <p class="timestamp">Last updated: TIMESTAMP_PLACEHOLDER</p>
    </div>
    
    <div class="endpoints">
        <h2>Available Actions</h2>
        <p><a href="/run" class="button">🚀 Start Stock Fetching Job</a></p>
        <p><a href="/status" class="button">📊 View Job Status</a></p>
        <p><a href="/logs" class="button">📝 View Logs</a></p>
    </div>
    
    <div class="endpoints">
        <h2>API Endpoints</h2>
        <ul>
            <li><strong>GET /</strong> - Health check (this page for browsers, JSON for API clients)</li>
            <li><strong>GET /run</strong> - Trigger stock data fetching job</li>
            <li><strong>GET /status</strong> - Get current job status</li>
            <li><strong>GET /logs</strong> - View last job output</li>
            <li><strong>GET /favicon.ico</strong> - Favicon handler</li>
        </ul>
    </div>
</body>
</html>'''

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
    """Health check endpoint - serves HTML for browsers, JSON for API clients."""
    logger.debug("Health check endpoint accessed")
    
    # Prepare the data
    data = {
        'status': 'healthy',
        'service': 'Stock Data Fetcher',
        'timestamp': datetime.now().isoformat(),
        'job_status': job_status
    }
    
    # Check if the request wants HTML (browser) or JSON (API client)
    accept_header = request.headers.get('Accept', '')
    if 'text/html' in accept_header and 'application/json' not in accept_header:
        # Browser request - serve HTML with simple string replacement
        html = HTML_TEMPLATE.replace('SERVICE_STATUS_PLACEHOLDER', data['status'])
        html = html.replace('SERVICE_NAME_PLACEHOLDER', data['service'])
        html = html.replace('TIMESTAMP_PLACEHOLDER', data['timestamp'])
        html = html.replace('JOB_STATUS_PLACEHOLDER', data['job_status']['status'])
        html = html.replace('RUN_COUNT_PLACEHOLDER', str(data['job_status']['run_count']))
        
        # Handle optional fields
        if data['job_status']['last_run']:
            html = html.replace('LAST_RUN_PLACEHOLDER', f'<p><strong>Last Run:</strong> {data["job_status"]["last_run"]}</p>')
        else:
            html = html.replace('LAST_RUN_PLACEHOLDER', '')
        
        if data['job_status']['last_error']:
            html = html.replace('LAST_ERROR_PLACEHOLDER', f'<p><strong>Last Error:</strong> {data["job_status"]["last_error"]}</p>')
        else:
            html = html.replace('LAST_ERROR_PLACEHOLDER', '')
            
        return html, 200, {'Content-Type': 'text/html'}
    else:
        # API request - serve JSON
        return jsonify(data)

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