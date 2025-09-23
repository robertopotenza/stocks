#!/usr/bin/env python3
"""
Main entry point for the Stock Data Fetcher application.

This module serves as the entry point for deployment platforms like Railway
that expect a main.py file in the project root. It supports both web server
mode and worker mode based on environment variables.
"""

import os
import subprocess
import sys
from logging_config import get_logger

# Get logger instance
logger = get_logger('stocks_app.main')

def main():
    """Main entry point that decides between web server and worker mode."""
    # Check if we should run in web mode (default for deployment platforms)
    web_mode = os.environ.get('WEB_MODE', 'true').lower() == 'true'
    
    if web_mode:
        # Check if we're in production (has PORT env var) or development
        port = int(os.environ.get('PORT', 5000))
        is_production = 'PORT' in os.environ
        
        if is_production:
            # Use gunicorn for production
            logger.info(f"🌐 Starting Stock Data Fetcher Web Server (Production) on port {port}")
            logger.info("📡 Health check available at: /")
            logger.info("🚀 Trigger job at: /run")
            logger.info("📊 Check status at: /status")
            logger.info("📝 View logs at: /logs")
            
            # Run gunicorn
            cmd = [
                'gunicorn',
                '--bind', f'0.0.0.0:{port}',
                '--workers', '1',
                '--timeout', '300',
                '--keep-alive', '60',
                '--access-logfile', '-',
                '--error-logfile', '-',
                'wsgi:app'
            ]
            subprocess.run(cmd)
        else:
            # Use Flask development server
            from web_server import app
            
            logger.info(f"🌐 Starting Stock Data Fetcher Web Server (Development) on port {port}")
            logger.info("📡 Health check available at: /")
            logger.info("🚀 Trigger job at: /run")
            logger.info("📊 Check status at: /status")
            logger.info("📝 View logs at: /logs")
            
            app.run(host='0.0.0.0', port=port, debug=True)
    else:
        # Run the original worker script
        from stock_prices import main as run_stock_fetcher
        logger.info("🔄 Running in worker mode...")
        run_stock_fetcher()

if __name__ == "__main__":
    main()