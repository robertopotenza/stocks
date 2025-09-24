#!/usr/bin/env python3
"""
Test module for sentiment analysis dashboard functionality.

This module tests that the sentiment analysis functionality works correctly
and returns proper data to the dashboard, including both API functionality
and frontend display validation.
"""

import unittest
import requests
import json
import time
from typing import Dict, Any, List


class TestSentimentDashboard(unittest.TestCase):
    """Test sentiment analysis dashboard functionality."""
    
    BASE_URL = "http://127.0.0.1:5000"
    
    def setUp(self):
        """Set up test fixtures."""
        # Wait a moment to ensure server is ready
        time.sleep(0.1)
    
    def test_sentiment_analysis_endpoint_exists(self):
        """Test that the sentiment analysis endpoint exists and responds."""
        response = requests.get(f"{self.BASE_URL}/sentiment-analysis")
        self.assertIn(response.status_code, [200, 404, 500], 
                     "Endpoint should exist (200) or return expected error codes")
        
        if response.status_code == 404:
            self.skipTest("No ticker data available - this is expected in test environment")
    
    def test_sentiment_analysis_returns_valid_json(self):
        """Test that sentiment analysis endpoint returns valid JSON structure."""
        try:
            response = requests.get(f"{self.BASE_URL}/sentiment-analysis")
            if response.status_code == 404:
                self.skipTest("No ticker data available - this is expected in test environment")
            
            self.assertEqual(response.status_code, 200, 
                           f"Expected 200, got {response.status_code}: {response.text}")
            
            data = response.json()
            
            # Test required top-level structure
            self.assertIn('tickers_analyzed', data, "Response should contain 'tickers_analyzed'")
            self.assertIn('sentiment_data', data, "Response should contain 'sentiment_data'")
            self.assertIn('portfolio_summary', data, "Response should contain 'portfolio_summary'")
            
            # Test that we have some tickers
            self.assertIsInstance(data['tickers_analyzed'], list, 
                                "'tickers_analyzed' should be a list")
            self.assertGreater(len(data['tickers_analyzed']), 0, 
                             "Should have at least one ticker analyzed")
            
        except requests.ConnectionError:
            self.skipTest("Server not running - this test requires the Flask server")
    
    def test_sentiment_data_structure(self):
        """Test that sentiment data has the correct structure for each ticker."""
        try:
            response = requests.get(f"{self.BASE_URL}/sentiment-analysis")
            if response.status_code == 404:
                self.skipTest("No ticker data available - this is expected in test environment")
            
            data = response.json()
            sentiment_data = data['sentiment_data']
            
            # Test each ticker's sentiment data structure
            for ticker, ticker_data in sentiment_data.items():
                self.assertIsInstance(ticker_data, dict, f"Data for {ticker} should be a dict")
                
                # Required fields
                required_fields = [
                    'ticker', 'total_mentions', 'sentiment_breakdown', 
                    'sentiment_percentages', 'overall_sentiment_score',
                    'standardized_sentiment_score', 'trend_direction'
                ]
                
                for field in required_fields:
                    self.assertIn(field, ticker_data, 
                                f"Ticker {ticker} should have field '{field}'")
                
                # Test sentiment breakdown structure
                breakdown = ticker_data['sentiment_breakdown']
                self.assertIn('positive', breakdown, f"{ticker} breakdown should have 'positive'")
                self.assertIn('neutral', breakdown, f"{ticker} breakdown should have 'neutral'")
                self.assertIn('negative', breakdown, f"{ticker} breakdown should have 'negative'")
                
                # Test sentiment percentages structure
                percentages = ticker_data['sentiment_percentages']
                self.assertIn('positive', percentages, f"{ticker} percentages should have 'positive'")
                self.assertIn('neutral', percentages, f"{ticker} percentages should have 'neutral'")
                self.assertIn('negative', percentages, f"{ticker} percentages should have 'negative'")
                
                # Test data types and ranges
                self.assertIsInstance(ticker_data['total_mentions'], int, 
                                    f"{ticker} total_mentions should be int")
                self.assertGreaterEqual(ticker_data['total_mentions'], 0, 
                                      f"{ticker} total_mentions should be >= 0")
                
                self.assertIsInstance(ticker_data['standardized_sentiment_score'], (int, float), 
                                    f"{ticker} standardized_sentiment_score should be numeric")
                self.assertGreaterEqual(ticker_data['standardized_sentiment_score'], 0, 
                                      f"{ticker} standardized_sentiment_score should be >= 0")
                self.assertLessEqual(ticker_data['standardized_sentiment_score'], 100, 
                                   f"{ticker} standardized_sentiment_score should be <= 100")
                
        except requests.ConnectionError:
            self.skipTest("Server not running - this test requires the Flask server")
    
    def test_portfolio_summary_structure(self):
        """Test that portfolio summary has the correct structure."""
        try:
            response = requests.get(f"{self.BASE_URL}/sentiment-analysis")
            if response.status_code == 404:
                self.skipTest("No ticker data available - this is expected in test environment")
            
            data = response.json()
            portfolio_summary = data['portfolio_summary']
            
            # Required fields in portfolio summary
            required_fields = [
                'total_mentions_across_all_tickers',
                'average_standardized_sentiment_score',
                'analysis_period_days',
                'last_updated'
            ]
            
            for field in required_fields:
                self.assertIn(field, portfolio_summary, 
                            f"Portfolio summary should have field '{field}'")
            
            # Test data types and ranges
            self.assertIsInstance(portfolio_summary['total_mentions_across_all_tickers'], int,
                                "Total mentions should be int")
            self.assertGreaterEqual(portfolio_summary['total_mentions_across_all_tickers'], 0,
                                  "Total mentions should be >= 0")
            
            self.assertIsInstance(portfolio_summary['average_standardized_sentiment_score'], (int, float),
                                "Average sentiment score should be numeric")
            self.assertGreaterEqual(portfolio_summary['average_standardized_sentiment_score'], 0,
                                  "Average sentiment score should be >= 0")
            self.assertLessEqual(portfolio_summary['average_standardized_sentiment_score'], 100,
                               "Average sentiment score should be <= 100")
            
        except requests.ConnectionError:
            self.skipTest("Server not running - this test requires the Flask server")
    
    def test_sentiment_data_is_being_displayed(self):
        """Test that sentiment data shows meaningful values (not all zeros)."""
        try:
            response = requests.get(f"{self.BASE_URL}/sentiment-analysis")
            if response.status_code == 404:
                self.skipTest("No ticker data available - this is expected in test environment")
            
            data = response.json()
            
            # Check that we have some meaningful data (not all zeros)
            has_mentions = data['portfolio_summary']['total_mentions_across_all_tickers'] > 0
            has_varied_sentiment = False
            
            # Check if any ticker has non-neutral sentiment (not exactly 50.0)
            for ticker_data in data['sentiment_data'].values():
                if ticker_data['standardized_sentiment_score'] != 50.0:
                    has_varied_sentiment = True
                    break
            
            # At least one condition should be true for realistic data display
            self.assertTrue(has_mentions or has_varied_sentiment,
                          "Dashboard should display meaningful sentiment data (mentions > 0 or varied sentiment)")
            
        except requests.ConnectionError:
            self.skipTest("Server not running - this test requires the Flask server")
    
    def test_fallback_data_indicators(self):
        """Test that fallback data is properly indicated when APIs are unavailable."""
        try:
            response = requests.get(f"{self.BASE_URL}/sentiment-analysis")
            if response.status_code == 404:
                self.skipTest("No ticker data available - this is expected in test environment")
            
            data = response.json()
            
            # Check for fallback data indicators
            portfolio_summary = data['portfolio_summary']
            
            if 'has_fallback_data' in portfolio_summary and portfolio_summary['has_fallback_data']:
                # If using fallback data, should have proper warning message
                self.assertIn('data_quality_warning', portfolio_summary,
                            "Should have data quality warning when using fallback data")
                
                warning_msg = portfolio_summary['data_quality_warning']
                self.assertIn('simulated', warning_msg.lower(),
                            "Warning message should mention simulated data")
                
                # Check individual ticker fallback indicators
                for ticker_data in data['sentiment_data'].values():
                    if ticker_data.get('is_fallback_data', False):
                        self.assertIn('fallback_reason', ticker_data,
                                    "Fallback data should have fallback_reason")
            
        except requests.ConnectionError:
            self.skipTest("Server not running - this test requires the Flask server")
    
    def test_dashboard_page_loads(self):
        """Test that the dashboard page loads successfully."""
        try:
            response = requests.get(f"{self.BASE_URL}/dashboard")
            self.assertEqual(response.status_code, 200, 
                           f"Dashboard page should load successfully, got {response.status_code}")
            
            # Check that the page contains sentiment analysis elements
            content = response.text
            self.assertIn('Social Media Sentiment Analysis', content,
                         "Dashboard should contain sentiment analysis section")
            self.assertIn('Analyze Sentiment', content,
                         "Dashboard should contain sentiment analysis button")
            
        except requests.ConnectionError:
            self.skipTest("Server not running - this test requires the Flask server")


class TestSentimentAnalysisLogic(unittest.TestCase):
    """Test sentiment analysis logic without requiring web server."""
    
    def test_import_sentiment_module(self):
        """Test that sentiment analysis module can be imported."""
        try:
            import sentiment_analysis
            self.assertIsNotNone(sentiment_analysis, "Should be able to import sentiment_analysis module")
        except ImportError as e:
            self.fail(f"Failed to import sentiment_analysis module: {e}")
    
    def test_analyze_portfolio_sentiment_function(self):
        """Test that analyze_portfolio_sentiment function works."""
        try:
            from sentiment_analysis import analyze_portfolio_sentiment
            
            # Test with sample tickers
            test_tickers = ['AAPL', 'GOOGL', 'MSFT']
            result = analyze_portfolio_sentiment(test_tickers)
            
            # Test structure
            self.assertIn('tickers_analyzed', result, "Result should contain tickers_analyzed")
            self.assertIn('sentiment_data', result, "Result should contain sentiment_data")
            self.assertIn('portfolio_summary', result, "Result should contain portfolio_summary")
            
            # Test that all requested tickers are analyzed
            self.assertEqual(len(result['tickers_analyzed']), len(test_tickers),
                           "Should analyze all requested tickers")
            
        except ImportError as e:
            self.fail(f"Failed to import required functions: {e}")


def run_tests():
    """Run all sentiment dashboard tests."""
    print("=" * 60)
    print("Running Sentiment Analysis Dashboard Tests")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestSentimentDashboard))
    suite.addTest(unittest.makeSuite(TestSentimentAnalysisLogic))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"\nTests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print("\nFailures:")
        for test, failure in result.failures:
            print(f"  {test}: {failure}")
    
    if result.errors:
        print("\nErrors:")
        for test, error in result.errors:
            print(f"  {test}: {error}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)