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
from typing import List, Dict, Any
from flask import Flask, jsonify, request, render_template, send_file
import pandas as pd
from stock_prices import main as run_stock_fetcher, fetch_stock_data, load_tickers_from_excel
from ai_evaluation import evaluate_stock_portfolio, evaluate_stock_portfolio_with_sentiment
from sentiment_analysis import analyze_portfolio_sentiment
from combined_analysis import analyze_combined_portfolio
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
    'run_count': 0,
    'last_sentiment': None,  # Cache sentiment data for current job run
    'sentiment_timestamp': None  # When sentiment was last fetched
}

def get_cached_sentiment_for_tickers(tickers: List[str], ttl_minutes: int = 5) -> Dict[str, Any]:
    """
    Get cached sentiment analysis or fetch fresh data if needed.
    
    Args:
        tickers: List of stock ticker symbols
        ttl_minutes: Cache time-to-live in minutes
        
    Returns:
        Dictionary containing sentiment analysis results
    """
    now = datetime.now()
    
    # Check if we have cached sentiment data that's still valid
    if (job_status['last_sentiment'] is not None and 
        job_status['sentiment_timestamp'] is not None):
        
        try:
            cached_time = datetime.fromisoformat(job_status['sentiment_timestamp'])
            age_minutes = (now - cached_time).total_seconds() / 60
            
            # Check if cache is still valid and has the same tickers
            cached_tickers = set(job_status['last_sentiment'].get('tickers_analyzed', []))
            requested_tickers = set(tickers)
            
            if age_minutes < ttl_minutes and cached_tickers >= requested_tickers:
                logger.info(f"Using cached sentiment data (age: {age_minutes:.1f} minutes)")
                return job_status['last_sentiment']
        except Exception as e:
            logger.warning(f"Error checking cached sentiment: {e}")
    
    # Cache miss or expired - fetch fresh sentiment data
    logger.info(f"Fetching fresh sentiment data for {len(tickers)} tickers")
    sentiment_data = analyze_portfolio_sentiment(tickers, days=5)
    
    # Cache the results
    job_status['last_sentiment'] = sentiment_data
    job_status['sentiment_timestamp'] = now.isoformat()
    
    return sentiment_data

def parse_ticker_limit(limit_param: str, default_limit: int = 10) -> int:
    """
    Parse and validate the ticker limit parameter.
    
    Args:
        limit_param: The limit parameter value from request.args.get('limit')
        default_limit: Default limit to use if invalid or missing
        
    Returns:
        The validated limit as an integer, or None for 'all'
    """
    if not limit_param:
        return default_limit
    
    # Handle 'all' case (case-insensitive)
    if limit_param.lower() == 'all':
        return None  # None means no limit
    
    # Try to parse as integer
    try:
        limit = int(limit_param)
        if limit <= 0:
            logger.warning(f"Invalid negative limit received: {limit_param}, using default: {default_limit}")
            return default_limit
        return limit
    except ValueError:
        logger.warning(f"Invalid non-integer limit received: {limit_param}, using default: {default_limit}")
        return default_limit

def apply_ticker_limit(tickers: list, limit: int = None) -> list:
    """
    Apply ticker limit to a list of tickers.
    
    Args:
        tickers: List of ticker symbols
        limit: Maximum number of tickers to return, None for no limit
        
    Returns:
        Limited list of tickers
    """
    if limit is None:
        return tickers
    return tickers[:limit]

def run_stock_fetcher_async():
    """Run the stock fetcher in a background thread."""
    try:
        job_status['status'] = 'running'
        job_status['last_error'] = None
        
        logger.info("Starting stock fetcher job")
        
        # Clear previous logs for this run
        clear_web_logs()
        
        # Pre-fetch sentiment analysis for current tickers to cache it
        try:
            tickers = load_tickers_from_excel(TICKERS_FILE)
            if tickers:
                limited_tickers = tickers[:10]  # Limit to prevent API overuse
                logger.info(f"Pre-fetching sentiment analysis for {len(limited_tickers)} tickers")
                sentiment_data = analyze_portfolio_sentiment(limited_tickers, days=5)
                job_status['last_sentiment'] = sentiment_data
                job_status['sentiment_timestamp'] = datetime.now().isoformat()
                logger.info("Sentiment analysis cached for job run")
        except Exception as e:
            logger.warning(f"Failed to pre-fetch sentiment data: {e}")
        
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
        
        # Run enhanced AI evaluation with sentiment analysis
        logger.info(f"Running enhanced AI evaluation with sentiment analysis on {len(stock_data)} stocks")
        evaluation_result = evaluate_stock_portfolio_with_sentiment(stock_data, include_sentiment=True)
        
        logger.info(f"Enhanced AI evaluation completed. Top pick: {evaluation_result['summary'].get('top_pick', 'None')}")
        
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
        
        # Parse and apply ticker limit from request parameter
        limit_param = request.args.get('limit')
        limit = parse_ticker_limit(limit_param, default_limit=10)
        limited_tickers = apply_ticker_limit(tickers, limit)
        
        logger.info(f"Running quick evaluation on {len(limited_tickers)} tickers (limit: {limit_param or 'default'})")
        
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





@app.route('/sentiment-analysis')
def get_sentiment_analysis():
    """Get social media sentiment analysis for current tickers."""
    logger.debug("Sentiment analysis endpoint accessed")
    
    try:
        # Load tickers from Excel file
        if not os.path.exists(TICKERS_FILE):
            return jsonify({
                'error': 'No ticker data available. Add some tickers first.'
            }), 404
        
        # Read the Excel file to get tickers
        df = pd.read_excel(TICKERS_FILE)
        
        if 'Ticker' not in df.columns:
            return jsonify({
                'error': 'Invalid ticker file format.'
            }), 400
        
        tickers = df['Ticker'].tolist()
        
        if not tickers:
            return jsonify({
                'error': 'No tickers found in the file.'
            }), 400
        
        # Parse and apply ticker limit from request parameter
        limit_param = request.args.get('limit')
        limit = parse_ticker_limit(limit_param, default_limit=10)
        limited_tickers = apply_ticker_limit(tickers, limit)
        
        logger.info(f"Getting sentiment analysis for {len(limited_tickers)} tickers (limit: {limit_param or 'default'})")
        
        # Use cached sentiment analysis
        sentiment_result = get_cached_sentiment_for_tickers(limited_tickers, ttl_minutes=5)
        
        logger.info(f"Sentiment analysis completed for {len(sentiment_result.get('tickers_analyzed', []))} tickers")
        
        return jsonify(sentiment_result)
        
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {e}")
        return jsonify({'error': f'Failed to perform sentiment analysis: {str(e)}'}), 500

@app.route('/ticker-sentiment/<ticker>')
def get_ticker_sentiment(ticker):
    """Get sentiment analysis for a specific ticker."""
    logger.debug(f"Ticker sentiment endpoint accessed for {ticker}")
    
    try:
        ticker = ticker.upper()
        
        logger.info(f"Getting sentiment analysis for {ticker}")
        
        # Use cached sentiment analysis for single ticker
        sentiment_result = get_cached_sentiment_for_tickers([ticker], ttl_minutes=5)
        
        # Extract data for the specific ticker
        ticker_data = sentiment_result.get('sentiment_data', {}).get(ticker, {})
        
        if not ticker_data:
            return jsonify({
                'error': f'No sentiment data found for {ticker}'
            }), 404
        
        logger.info(f"Sentiment analysis completed for {ticker}")
        
        return jsonify({
            'ticker': ticker,
            'sentiment_data': ticker_data,
            'portfolio_summary': sentiment_result.get('portfolio_summary', {})
        })
        
    except Exception as e:
        logger.error(f"Error in ticker sentiment analysis for {ticker}: {e}")
        return jsonify({'error': f'Failed to get sentiment for {ticker}: {str(e)}'}), 500

@app.route('/combined-analysis')
def get_combined_analysis():
    """Get combined AI evaluation and sentiment analysis for unified stock rankings."""
    logger.debug("Combined analysis endpoint accessed")
    
    try:
        # Load tickers from Excel file
        if not os.path.exists(TICKERS_FILE):
            return jsonify({
                'error': 'No ticker data available. Add some tickers first.'
            }), 404
        
        # Read the Excel file to get tickers and any existing stock data
        df = pd.read_excel(TICKERS_FILE)
        
        if 'Ticker' not in df.columns:
            return jsonify({
                'error': 'Invalid ticker file format.'
            }), 400
        
        tickers = df['Ticker'].tolist()
        
        if not tickers:
            return jsonify({
                'error': 'No tickers found in the file.'
            }), 400
        
        # Parse and apply ticker limit from request parameter
        limit_param = request.args.get('limit')
        limit = parse_ticker_limit(limit_param, default_limit=10)
        limited_tickers = apply_ticker_limit(tickers, limit)
        
        logger.info(f"Running combined analysis on {len(limited_tickers)} tickers (limit: {limit_param or 'default'})")
        
        # Get cached sentiment analysis data
        cached_sentiment = get_cached_sentiment_for_tickers(limited_tickers, ttl_minutes=5)
        
        # Check if we have recent stock data in the Excel file
        stock_data = None
        required_columns = ['Price', 'PE_Ratio', '52w_High', '52w_Low']
        
        if all(col in df.columns for col in required_columns):
            # Convert DataFrame to stock_data format
            stock_data = {}
            for _, row in df.iterrows():
                ticker = row['Ticker']
                if ticker in limited_tickers:
                    # Convert row to dictionary, handling NaN values
                    data = {}
                    for col in df.columns:
                        value = row[col]
                        if pd.isna(value):
                            data[col] = 'N/A'
                        else:
                            data[col] = value
                    stock_data[ticker] = data
            
            logger.info(f"Using existing stock data from Excel file for {len(stock_data)} tickers")
        else:
            logger.info("No recent stock data found in Excel file, will fetch fresh data")
        
        # Run combined analysis with cached sentiment
        combined_result = analyze_combined_portfolio(limited_tickers, stock_data, cached_sentiment)
        
        logger.info(f"Combined analysis completed. Top recommendation: {combined_result.get('summary', {}).get('top_recommendation', {}).get('ticker', 'N/A')}")
        
        return jsonify(combined_result)
        
    except Exception as e:
        logger.error(f"Error in combined analysis: {e}")
        return jsonify({'error': f'Failed to perform combined analysis: {str(e)}'}), 500

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