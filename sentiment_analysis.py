#!/usr/bin/env python3
"""
Social Media Sentiment Analysis Module

This module fetches social media posts from Reddit and Twitter for stock tickers
and analyzes sentiment to provide insights into market sentiment for each stock.
"""

import praw
import tweepy
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
import requests
from textblob import TextBlob
from nltk.sentiment import SentimentIntensityAnalyzer
import os
import hashlib
from logging_config import get_logger

# Get logger instance
logger = get_logger('stocks_app.sentiment_analysis')

# Module-level sentiment cache with TTL
_sentiment_cache = {}

class SentimentAnalyzer:
    """Analyzes sentiment of text using multiple methods."""
    
    def __init__(self):
        """Initialize sentiment analyzers."""
        try:
            self.sia = SentimentIntensityAnalyzer()
        except LookupError as e:
            logger.warning(f"NLTK VADER lexicon not available: {e}")
            logger.warning("Sentiment analysis will use TextBlob only")
            self.sia = None
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of given text using multiple methods.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary containing sentiment scores and classification
        """
        if not text or not text.strip():
            return {
                'polarity': 0.0,
                'subjectivity': 0.0,
                'compound': 0.0,
                'classification': 'neutral'
            }
        
        # TextBlob analysis
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # VADER analysis (if available)
        if self.sia:
            vader_scores = self.sia.polarity_scores(text)
            compound = vader_scores['compound']
            
            # Determine classification based on compound score
            if compound >= 0.05:
                classification = 'positive'
            elif compound <= -0.05:
                classification = 'negative'
            else:
                classification = 'neutral'
            
            return {
                'polarity': polarity,
                'subjectivity': subjectivity,
                'compound': compound,
                'classification': classification,
                'pos': vader_scores['pos'],
                'neu': vader_scores['neu'],
                'neg': vader_scores['neg']
            }
        else:
            # Fall back to TextBlob-only analysis
            if polarity >= 0.1:
                classification = 'positive'
            elif polarity <= -0.1:
                classification = 'negative'
            else:
                classification = 'neutral'
            
            return {
                'polarity': polarity,
                'subjectivity': subjectivity,
                'compound': polarity,  # Use polarity as compound score fallback
                'classification': classification,
                'pos': max(0, polarity),  # Approximate positive score
                'neu': 1 - abs(polarity),  # Approximate neutral score
                'neg': max(0, -polarity)  # Approximate negative score
            }

class RedditSentimentFetcher:
    """Fetches and analyzes sentiment from Reddit."""
    
    def __init__(self, client_id: str = None, client_secret: str = None, user_agent: str = None):
        """
        Initialize Reddit client.
        
        Args:
            client_id: Reddit API client ID
            client_secret: Reddit API client secret
            user_agent: User agent string
        """
        self.client_id = client_id or os.getenv('REDDIT_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('REDDIT_CLIENT_SECRET')
        self.user_agent = user_agent or os.getenv('REDDIT_USER_AGENT', 'StockSentimentBot/1.0')
        
        self.reddit = None
        self.analyzer = SentimentAnalyzer()
        
        # Initialize Reddit client if credentials are available
        if self.client_id and self.client_secret:
            try:
                self.reddit = praw.Reddit(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    user_agent=self.user_agent
                )
                logger.info("Reddit client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Reddit client: {e}")
        else:
            logger.warning("Reddit credentials not provided - Reddit sentiment will return empty data")
    
    def fetch_ticker_sentiment(self, ticker: str, days: int = 5) -> Dict[str, Any]:
        """
        Fetch sentiment data for a ticker from Reddit.
        
        Args:
            ticker: Stock ticker symbol
            days: Number of days to look back
            
        Returns:
            Dictionary containing sentiment analysis results
        """
        if not self.reddit:
            return self._get_empty_reddit_sentiment(ticker)
        
        try:
            # Search for posts about the ticker
            subreddits = ['investing', 'stocks', 'SecurityAnalysis', 'ValueInvesting', 'StockMarket']
            posts = []
            
            search_terms = [
                f"${ticker}",
                ticker,
                f"{ticker} stock"
            ]
            
            # Collect posts from multiple subreddits
            for subreddit_name in subreddits:
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)
                    
                    for term in search_terms:
                        for post in subreddit.search(term, time_filter='week', limit=10):
                            # Check if post is recent enough
                            post_date = datetime.fromtimestamp(post.created_utc)
                            if post_date >= datetime.now() - timedelta(days=days):
                                posts.append({
                                    'title': post.title,
                                    'text': post.selftext,
                                    'score': post.score,
                                    'num_comments': post.num_comments,
                                    'created': post_date,
                                    'url': post.url
                                })
                except Exception as e:
                    logger.warning(f"Error searching subreddit {subreddit_name}: {e}")
                    continue
            
            # Analyze sentiment of collected posts
            return self._analyze_posts_sentiment(ticker, posts)
            
        except Exception as e:
            logger.error(f"Error fetching Reddit sentiment for {ticker}: {e}")
            return self._get_empty_reddit_sentiment(ticker)
    
    def _analyze_posts_sentiment(self, ticker: str, posts: List[Dict]) -> Dict[str, Any]:
        """Analyze sentiment of collected Reddit posts."""
        if not posts:
            return {
                'ticker': ticker,
                'source': 'reddit',
                'total_mentions': 0,
                'sentiment_breakdown': {'positive': 0, 'neutral': 0, 'negative': 0},
                'sentiment_percentages': {'positive': 0.0, 'neutral': 0.0, 'negative': 0.0},
                'overall_score': 0.0,
                'trend_direction': 'neutral',
                'posts_analyzed': []
            }
        
        sentiments = []
        analyzed_posts = []
        
        for post in posts:
            # Combine title and text for analysis
            text = f"{post['title']} {post['text']}".strip()
            
            if text:
                sentiment = self.analyzer.analyze_text(text)
                sentiment['weight'] = min(post['score'], 10)  # Cap weight at 10
                sentiments.append(sentiment)
                
                analyzed_posts.append({
                    'text': text[:200],  # Truncate for storage
                    'sentiment': sentiment['classification'],
                    'score': sentiment['compound'],
                    'weight': sentiment['weight']
                })
        
        return self._calculate_overall_sentiment(ticker, 'reddit', sentiments, analyzed_posts)
    
    def _get_empty_reddit_sentiment(self, ticker: str) -> Dict[str, Any]:
        """Return empty Reddit sentiment data when API is not available."""
        return {
            'ticker': ticker,
            'source': 'reddit',
            'total_mentions': 0,
            'sentiment_breakdown': {
                'positive': 0,
                'neutral': 0,
                'negative': 0
            },
            'sentiment_percentages': {
                'positive': 0.0,
                'neutral': 0.0,
                'negative': 0.0
            },
            'overall_score': 0.0,
            'standardized_sentiment_score': 50.0,  # Neutral on 0-100 scale
            'trend_direction': 'stable',
            'posts_analyzed': []
        }
    
    def _calculate_overall_sentiment(self, ticker: str, source: str, sentiments: List[Dict], posts: List[Dict]) -> Dict[str, Any]:
        """Calculate overall sentiment metrics from individual sentiment scores."""
        if not sentiments:
            return {
                'ticker': ticker,
                'source': source,
                'total_mentions': 0,
                'sentiment_breakdown': {'positive': 0, 'neutral': 0, 'negative': 0},
                'sentiment_percentages': {'positive': 0.0, 'neutral': 0.0, 'negative': 0.0},
                'overall_score': 0.0,
                'trend_direction': 'neutral',
                'posts_analyzed': []
            }
        
        # Count sentiment classifications
        positive_count = sum(1 for s in sentiments if s['classification'] == 'positive')
        neutral_count = sum(1 for s in sentiments if s['classification'] == 'neutral')
        negative_count = sum(1 for s in sentiments if s['classification'] == 'negative')
        total_mentions = len(sentiments)
        
        # Calculate weighted average score
        total_weight = sum(s.get('weight', 1) for s in sentiments)
        if total_weight > 0:
            weighted_score = sum(s['compound'] * s.get('weight', 1) for s in sentiments) / total_weight
        else:
            weighted_score = sum(s['compound'] for s in sentiments) / len(sentiments)
        
        # Determine trend direction (simplified)
        if weighted_score > 0.1:
            trend_direction = 'improving'
        elif weighted_score < -0.1:
            trend_direction = 'declining'
        else:
            trend_direction = 'stable'
        
        return {
            'ticker': ticker,
            'source': source,
            'total_mentions': total_mentions,
            'sentiment_breakdown': {
                'positive': positive_count,
                'neutral': neutral_count,
                'negative': negative_count
            },
            'sentiment_percentages': {
                'positive': round((positive_count / total_mentions) * 100, 1) if total_mentions > 0 else 0,
                'neutral': round((neutral_count / total_mentions) * 100, 1) if total_mentions > 0 else 0,
                'negative': round((negative_count / total_mentions) * 100, 1) if total_mentions > 0 else 0
            },
            'overall_score': round(weighted_score, 3),
            'trend_direction': trend_direction,
            'posts_analyzed': posts[:10]  # Keep only first 10 for storage
        }

class TwitterSentimentFetcher:
    """Fetches and analyzes sentiment from Twitter/X."""
    
    def __init__(self, bearer_token: str = None):
        """
        Initialize Twitter client.
        
        Args:
            bearer_token: Twitter API v2 bearer token
        """
        self.bearer_token = bearer_token or os.getenv('TWITTER_BEARER_TOKEN')
        self.client = None
        self.analyzer = SentimentAnalyzer()
        
        # Initialize Twitter client if credentials are available
        if self.bearer_token:
            try:
                self.client = tweepy.Client(bearer_token=self.bearer_token)
                logger.info("Twitter client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Twitter client: {e}")
        else:
            logger.warning("Twitter credentials not provided - Twitter sentiment will return empty data")
    
    def fetch_ticker_sentiment(self, ticker: str, days: int = 5) -> Dict[str, Any]:
        """
        Fetch sentiment data for a ticker from Twitter.
        
        Args:
            ticker: Stock ticker symbol
            days: Number of days to look back
            
        Returns:
            Dictionary containing sentiment analysis results
        """
        if not self.client:
            return self._get_empty_twitter_sentiment(ticker)
        
        try:
            # Search for tweets about the ticker
            search_query = f"${ticker} OR {ticker} stock -is:retweet lang:en"
            
            # Calculate date range
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            tweets = []
            
            # Fetch tweets (limited by API rate limits)
            try:
                response = self.client.search_recent_tweets(
                    query=search_query,
                    max_results=100,  # API limit for basic access
                    start_time=start_time,
                    end_time=end_time,
                    tweet_fields=['created_at', 'public_metrics', 'author_id']
                )
                
                if response.data:
                    for tweet in response.data:
                        tweets.append({
                            'text': tweet.text,
                            'created_at': tweet.created_at,
                            'metrics': tweet.public_metrics,
                            'author_id': tweet.author_id
                        })
            
            except Exception as e:
                logger.warning(f"Error fetching tweets for {ticker}: {e}")
                return self._get_empty_twitter_sentiment(ticker)
            
            # Analyze sentiment of collected tweets
            return self._analyze_tweets_sentiment(ticker, tweets)
            
        except Exception as e:
            logger.error(f"Error fetching Twitter sentiment for {ticker}: {e}")
            return self._get_empty_twitter_sentiment(ticker)
    
    def _analyze_tweets_sentiment(self, ticker: str, tweets: List[Dict]) -> Dict[str, Any]:
        """Analyze sentiment of collected tweets."""
        if not tweets:
            return {
                'ticker': ticker,
                'source': 'twitter',
                'total_mentions': 0,
                'sentiment_breakdown': {'positive': 0, 'neutral': 0, 'negative': 0},
                'sentiment_percentages': {'positive': 0.0, 'neutral': 0.0, 'negative': 0.0},
                'overall_score': 0.0,
                'trend_direction': 'neutral',
                'posts_analyzed': []
            }
        
        sentiments = []
        analyzed_tweets = []
        
        for tweet in tweets:
            text = tweet['text']
            
            # Clean the text (remove URLs, mentions, etc.)
            cleaned_text = self._clean_tweet_text(text)
            
            if cleaned_text:
                sentiment = self.analyzer.analyze_text(cleaned_text)
                
                # Weight by engagement (likes + retweets)
                metrics = tweet.get('metrics', {})
                weight = min(
                    metrics.get('like_count', 0) + metrics.get('retweet_count', 0) + 1,
                    20  # Cap weight at 20
                )
                sentiment['weight'] = weight
                sentiments.append(sentiment)
                
                analyzed_tweets.append({
                    'text': cleaned_text[:200],  # Truncate for storage
                    'sentiment': sentiment['classification'],
                    'score': sentiment['compound'],
                    'weight': weight
                })
        
        return self._calculate_overall_sentiment(ticker, 'twitter', sentiments, analyzed_tweets)
    
    def _clean_tweet_text(self, text: str) -> str:
        """Clean tweet text for sentiment analysis."""
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove user mentions and hashtags for cleaner analysis
        text = re.sub(r'@\w+|#\w+', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _get_empty_twitter_sentiment(self, ticker: str) -> Dict[str, Any]:
        """Return empty Twitter sentiment data when API is not available."""
        return {
            'ticker': ticker,
            'source': 'twitter',
            'total_mentions': 0,
            'sentiment_breakdown': {
                'positive': 0,
                'neutral': 0,
                'negative': 0
            },
            'sentiment_percentages': {
                'positive': 0.0,
                'neutral': 0.0,
                'negative': 0.0
            },
            'overall_score': 0.0,
            'standardized_sentiment_score': 50.0,  # Neutral on 0-100 scale
            'trend_direction': 'stable',
            'posts_analyzed': []
        }
    
    def _calculate_overall_sentiment(self, ticker: str, source: str, sentiments: List[Dict], posts: List[Dict]) -> Dict[str, Any]:
        """Calculate overall sentiment metrics from individual sentiment scores."""
        if not sentiments:
            return {
                'ticker': ticker,
                'source': source,
                'total_mentions': 0,
                'sentiment_breakdown': {'positive': 0, 'neutral': 0, 'negative': 0},
                'sentiment_percentages': {'positive': 0.0, 'neutral': 0.0, 'negative': 0.0},
                'overall_score': 0.0,
                'trend_direction': 'neutral',
                'posts_analyzed': []
            }
        
        # Count sentiment classifications
        positive_count = sum(1 for s in sentiments if s['classification'] == 'positive')
        neutral_count = sum(1 for s in sentiments if s['classification'] == 'neutral')
        negative_count = sum(1 for s in sentiments if s['classification'] == 'negative')
        total_mentions = len(sentiments)
        
        # Calculate weighted average score
        total_weight = sum(s.get('weight', 1) for s in sentiments)
        if total_weight > 0:
            weighted_score = sum(s['compound'] * s.get('weight', 1) for s in sentiments) / total_weight
        else:
            weighted_score = sum(s['compound'] for s in sentiments) / len(sentiments)
        
        # Determine trend direction (simplified)
        if weighted_score > 0.1:
            trend_direction = 'improving'
        elif weighted_score < -0.1:
            trend_direction = 'declining'
        else:
            trend_direction = 'stable'
        
        return {
            'ticker': ticker,
            'source': source,
            'total_mentions': total_mentions,
            'sentiment_breakdown': {
                'positive': positive_count,
                'neutral': neutral_count,
                'negative': negative_count
            },
            'sentiment_percentages': {
                'positive': round((positive_count / total_mentions) * 100, 1) if total_mentions > 0 else 0,
                'neutral': round((neutral_count / total_mentions) * 100, 1) if total_mentions > 0 else 0,
                'negative': round((negative_count / total_mentions) * 100, 1) if total_mentions > 0 else 0
            },
            'overall_score': round(weighted_score, 3),
            'trend_direction': trend_direction,
            'posts_analyzed': posts[:10]  # Keep only first 10 for storage
        }

class SocialMediaSentimentAnalyzer:
    """Main class for fetching and analyzing social media sentiment for stocks."""
    
    def __init__(self, reddit_client_id: str = None, reddit_client_secret: str = None, 
                 twitter_bearer_token: str = None):
        """
        Initialize the social media sentiment analyzer.
        
        Args:
            reddit_client_id: Reddit API client ID
            reddit_client_secret: Reddit API client secret
            twitter_bearer_token: Twitter API v2 bearer token
        """
        self.reddit_fetcher = RedditSentimentFetcher(reddit_client_id, reddit_client_secret)
        self.twitter_fetcher = TwitterSentimentFetcher(twitter_bearer_token)
    
    def analyze_tickers_sentiment(self, tickers: List[str], days: int = 5) -> Dict[str, Dict[str, Any]]:
        """
        Analyze sentiment for multiple stock tickers.
        
        Args:
            tickers: List of stock ticker symbols
            days: Number of days to look back for posts
            
        Returns:
            Dictionary mapping ticker to combined sentiment analysis
        """
        results = {}
        
        logger.info(f"Analyzing sentiment for {len(tickers)} tickers over {days} days")
        
        for ticker in tickers:
            try:
                logger.debug(f"Analyzing sentiment for {ticker}")
                
                # Fetch sentiment from both platforms
                reddit_sentiment = self.reddit_fetcher.fetch_ticker_sentiment(ticker, days)
                twitter_sentiment = self.twitter_fetcher.fetch_ticker_sentiment(ticker, days)
                
                # Combine results
                combined_sentiment = self._combine_sentiment_results(ticker, reddit_sentiment, twitter_sentiment)
                results[ticker] = combined_sentiment
                
                # Add small delay to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error analyzing sentiment for {ticker}: {e}")
                # Provide fallback data
                results[ticker] = self._get_fallback_sentiment(ticker)
        
        logger.info(f"Sentiment analysis completed for {len(results)} tickers")
        return results
    
    def _combine_sentiment_results(self, ticker: str, reddit_data: Dict, twitter_data: Dict) -> Dict[str, Any]:
        """Combine sentiment results from Reddit and Twitter."""
        # Calculate total mentions
        total_mentions = reddit_data['total_mentions'] + twitter_data['total_mentions']
        
        if total_mentions == 0:
            return self._get_fallback_sentiment(ticker)
        
        # Combine sentiment breakdowns
        combined_breakdown = {
            'positive': reddit_data['sentiment_breakdown']['positive'] + twitter_data['sentiment_breakdown']['positive'],
            'neutral': reddit_data['sentiment_breakdown']['neutral'] + twitter_data['sentiment_breakdown']['neutral'],
            'negative': reddit_data['sentiment_breakdown']['negative'] + twitter_data['sentiment_breakdown']['negative']
        }
        
        # Calculate combined percentages
        combined_percentages = {
            'positive': round((combined_breakdown['positive'] / total_mentions) * 100, 1),
            'neutral': round((combined_breakdown['neutral'] / total_mentions) * 100, 1),
            'negative': round((combined_breakdown['negative'] / total_mentions) * 100, 1)
        }
        
        # Weight scores by volume of mentions
        reddit_weight = reddit_data['total_mentions'] / total_mentions if total_mentions > 0 else 0
        twitter_weight = twitter_data['total_mentions'] / total_mentions if total_mentions > 0 else 0
        
        combined_score = (reddit_data['overall_score'] * reddit_weight + 
                         twitter_data['overall_score'] * twitter_weight)
        
        # Determine overall trend
        if combined_score > 0.1:
            trend_direction = 'improving'
        elif combined_score < -0.1:
            trend_direction = 'declining'
        else:
            trend_direction = 'stable'
        
        # Calculate standardized sentiment score using new formula
        # Sentiment Score = ((% Positive - % Negative) + 100) / 2
        standardized_sentiment_score = ((combined_percentages['positive'] - combined_percentages['negative']) + 100) / 2

        return {
            'ticker': ticker,
            'total_mentions': total_mentions,
            'sentiment_breakdown': combined_breakdown,
            'sentiment_percentages': combined_percentages,
            'overall_sentiment_score': round(combined_score, 3),  # Keep original for compatibility
            'standardized_sentiment_score': round(standardized_sentiment_score, 1),  # New standardized score
            'trend_direction': trend_direction,
            'platform_data': {
                'reddit': reddit_data,
                'twitter': twitter_data
            },
            'last_updated': datetime.now().isoformat()
        }
    
    def _get_fallback_sentiment(self, ticker: str) -> Dict[str, Any]:
        """Generate fallback sentiment data when analysis fails."""
        return {
            'ticker': ticker,
            'total_mentions': 0,
            'sentiment_breakdown': {'positive': 0, 'neutral': 0, 'negative': 0},
            'sentiment_percentages': {'positive': 0.0, 'neutral': 0.0, 'negative': 0.0},
            'overall_sentiment_score': 0.0,
            'standardized_sentiment_score': 50.0,  # Neutral sentiment = 50 on 0-100 scale
            'trend_direction': 'stable',
            'platform_data': {
                'reddit': {'total_mentions': 0, 'overall_score': 0.0},
                'twitter': {'total_mentions': 0, 'overall_score': 0.0}
            },
            'last_updated': datetime.now().isoformat(),
            'error': 'Unable to fetch sentiment data'
        }

def get_cached_portfolio_sentiment(tickers: List[str], days: int = 5, ttl_seconds: int = 300) -> Dict[str, Any]:
    """
    Get cached portfolio sentiment analysis with TTL functionality.
    
    Args:
        tickers: List of stock ticker symbols
        days: Number of days to look back
        ttl_seconds: Time-to-live for cache entries in seconds (default: 5 minutes)
        
    Returns:
        Dictionary containing sentiment analysis for all tickers
    """
    # Create cache key based on sorted tickers and days
    key = (tuple(sorted(tickers)), days)
    now = datetime.now()
    
    # Check if we have a valid cached entry
    entry = _sentiment_cache.get(key)
    if entry and (now - entry['timestamp']).total_seconds() < ttl_seconds:
        logger.info(f"Using cached sentiment data for {len(tickers)} tickers (age: {(now - entry['timestamp']).total_seconds():.1f}s)")
        return entry['data']
    
    # Cache miss or expired - fetch fresh data
    logger.info(f"Fetching fresh sentiment data for {len(tickers)} tickers")
    data = _analyze_portfolio_sentiment_original(tickers, days)
    
    # Store in cache
    _sentiment_cache[key] = {
        'timestamp': now,
        'data': data
    }
    
    # Clean up old cache entries (simple cleanup - remove entries older than 1 hour)
    cutoff_time = now - timedelta(hours=1)
    expired_keys = [k for k, v in _sentiment_cache.items() if v['timestamp'] < cutoff_time]
    for expired_key in expired_keys:
        del _sentiment_cache[expired_key]
    
    logger.info(f"Cached sentiment data for {len(tickers)} tickers. Cache size: {len(_sentiment_cache)}")
    return data

def _analyze_portfolio_sentiment_original(tickers: List[str], days: int = 5) -> Dict[str, Any]:
    """
    Original implementation of portfolio sentiment analysis (now internal).
    
    Args:
        tickers: List of stock ticker symbols
        days: Number of days to look back
        
    Returns:
        Dictionary containing sentiment analysis for all tickers
    """
    analyzer = SocialMediaSentimentAnalyzer()
    
    # Analyze sentiment for all tickers
    sentiment_results = analyzer.analyze_tickers_sentiment(tickers, days)
    
    # Calculate portfolio-level statistics
    total_mentions = sum(data['total_mentions'] for data in sentiment_results.values())
    
    if total_mentions > 0:
        # Calculate weighted average sentiment score (raw -1 to 1 scale)
        weighted_score = sum(
            data['overall_sentiment_score'] * data['total_mentions'] 
            for data in sentiment_results.values()
        ) / total_mentions
        
        # Calculate weighted average standardized sentiment score (0-100 scale)
        weighted_standardized_score = sum(
            data['standardized_sentiment_score'] * data['total_mentions'] 
            for data in sentiment_results.values()
        ) / total_mentions
        
        # Find most positive and most negative stocks (using standardized score)
        sorted_by_sentiment = sorted(
            sentiment_results.items(),
            key=lambda x: x[1]['standardized_sentiment_score'],
            reverse=True
        )
        
        most_positive = sorted_by_sentiment[0] if sorted_by_sentiment else None
        most_negative = sorted_by_sentiment[-1] if sorted_by_sentiment else None
    else:
        weighted_score = 0.0
        weighted_standardized_score = 50.0  # Neutral on 0-100 scale
        most_positive = None
        most_negative = None
    
    return {
        'tickers_analyzed': list(sentiment_results.keys()),
        'sentiment_data': sentiment_results,
        'portfolio_summary': {
            'total_mentions_across_all_tickers': total_mentions,
            'average_sentiment_score': round(weighted_score, 3),  # Legacy raw score
            'average_standardized_sentiment_score': round(weighted_standardized_score, 1),  # Standardized 0-100 score
            'most_positive_ticker': most_positive[0] if most_positive else None,
            'most_negative_ticker': most_negative[0] if most_negative else None,
            'analysis_period_days': days,
            'last_updated': datetime.now().isoformat()
        }
    }

def analyze_portfolio_sentiment(tickers: List[str], days: int = 5) -> Dict[str, Any]:
    """
    Main function to analyze sentiment for a portfolio of stocks (with caching).
    
    Args:
        tickers: List of stock ticker symbols
        days: Number of days to look back
        
    Returns:
        Dictionary containing sentiment analysis for all tickers
    """
    return get_cached_portfolio_sentiment(tickers, days)

if __name__ == "__main__":
    # Test usage
    test_tickers = ["AAPL", "GOOGL", "MSFT"]
    results = analyze_portfolio_sentiment(test_tickers)
    print(f"Analyzed sentiment for {len(results['tickers_analyzed'])} tickers")
    print(f"Total mentions: {results['portfolio_summary']['total_mentions_across_all_tickers']}")
    print(f"Average standardized sentiment: {results['portfolio_summary']['average_standardized_sentiment_score']}")
    print(f"Cache stats: {len(_sentiment_cache)} entries cached")