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

app = Flask(__name__)

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
        
        # Capture stdout to log the output
        import io
        import contextlib
        
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            run_stock_fetcher()
        
        output = f.getvalue()
        
        job_status['status'] = 'completed'
        job_status['last_run'] = datetime.now().isoformat()
        job_status['run_count'] += 1
        job_status['last_output'] = output
        
    except Exception as e:
        job_status['status'] = 'error'
        job_status['last_error'] = str(e)

@app.route('/')
def health_check():
    """Health check endpoint for load balancers."""
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
        return jsonify({
            'error': 'Job is already running',
            'status': job_status
        }), 409
    
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
    return jsonify(job_status)

@app.route('/logs')
def get_logs():
    """Get the last job output."""
    if 'last_output' in job_status:
        return jsonify({
            'status': job_status['status'],
            'last_run': job_status['last_run'],
            'output': job_status['last_output']
        })
    else:
        return jsonify({
            'message': 'No logs available yet'
        })

if __name__ == '__main__':
    # Get port from environment (Railway, Heroku, etc.)
    port = int(os.environ.get('PORT', 5000))
    
    # Check if we should run in web mode
    web_mode = os.environ.get('WEB_MODE', 'true').lower() == 'true'
    
    if web_mode:
        print(f"🌐 Starting Stock Data Fetcher Web Server on port {port}")
        print("📡 Health check available at: /")
        print("🚀 Trigger job at: /run")
        print("📊 Check status at: /status")
        print("📝 View logs at: /logs")
        
        app.run(host='0.0.0.0', port=port)
    else:
        # Fall back to running the original script
        print("🔄 Running in worker mode...")
        run_stock_fetcher()