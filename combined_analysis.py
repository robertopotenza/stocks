#!/usr/bin/env python3
"""
Combined Stock Analysis Module

This module provides a unified analysis that merges AI-powered stock evaluation
with social media sentiment analysis to create a comprehensive ranking system
that highlights stocks strong in both technical/fundamental analysis and sentiment.
"""

from typing import Dict, List, Any, Tuple
from logging_config import get_logger
from ai_evaluation import evaluate_stock_portfolio
from sentiment_analysis import analyze_portfolio_sentiment

# Get logger instance
logger = get_logger('stocks_app.combined_analysis')


class CombinedStockAnalyzer:
    """Combined analysis engine that merges AI evaluation with sentiment analysis."""
    
    def __init__(self):
        """Initialize the combined analyzer with weighting factors."""
        # Weighting for final combined score (should sum to 1.0)
        self.weights = {
            'ai_evaluation': 0.7,    # AI technical/fundamental analysis weight
            'sentiment': 0.3         # Social media sentiment weight
        }
        
        # Score thresholds for combined recommendations
        self.recommendation_thresholds = {
            'buy': 75,      # Combined score >= 75
            'hold': 50,     # Combined score >= 50 but < 75
            'avoid': 50     # Combined score < 50
        }
    
    def analyze_portfolio(self, tickers: List[str], stock_data: Dict[str, Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform combined analysis on a portfolio of stocks.
        
        Args:
            tickers: List of stock ticker symbols to analyze
            stock_data: Optional pre-fetched stock data (if None, will be fetched)
            
        Returns:
            Dictionary containing combined analysis results with unified rankings
        """
        logger.info(f"🚀 Starting combined stock analysis for {len(tickers)} tickers")
        
        try:
            # Step 1: Get AI evaluation results
            logger.info("📊 Running AI-powered stock evaluation...")
            if stock_data:
                ai_results = evaluate_stock_portfolio(stock_data)
            else:
                # If no stock data provided, we need to fetch it
                from stock_prices import fetch_stock_data
                logger.info("📈 Fetching fresh stock data...")
                stock_data = fetch_stock_data(tickers)
                ai_results = evaluate_stock_portfolio(stock_data)
            
            logger.info(f"✅ AI evaluation completed for {len(ai_results.get('ranked_stocks', []))} stocks")
            
            # Step 2: Get sentiment analysis results
            logger.info("📱 Running social media sentiment analysis...")
            sentiment_results = analyze_portfolio_sentiment(tickers, days=5)
            
            logger.info(f"✅ Sentiment analysis completed for {len(sentiment_results.get('sentiment_data', {}))} tickers")
            
            # Step 3: Combine the results
            logger.info("🤝 Combining AI evaluation and sentiment analysis...")
            combined_results = self._combine_analysis_results(ai_results, sentiment_results)
            
            logger.info(f"✅ Combined analysis completed. Top recommendation: {combined_results.get('top_recommendation', {}).get('ticker', 'N/A')}")
            
            return combined_results
            
        except Exception as e:
            logger.error(f"Error in combined analysis: {e}")
            raise
    
    def _combine_analysis_results(self, ai_results: Dict[str, Any], sentiment_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combine AI evaluation and sentiment analysis results into unified rankings.
        
        Args:
            ai_results: Results from AI evaluation
            sentiment_results: Results from sentiment analysis
            
        Returns:
            Combined analysis results with unified rankings
        """
        # Extract data from both analyses
        ai_stocks = {stock['ticker']: stock for stock in ai_results.get('ranked_stocks', [])}
        sentiment_data = sentiment_results.get('sentiment_data', {})
        
        combined_stocks = []
        
        for ticker in ai_stocks.keys():
            ai_stock = ai_stocks[ticker]
            sentiment_info = sentiment_data.get(ticker, {})
            
            # Create combined analysis for this stock
            combined_stock = self._create_combined_stock_analysis(ticker, ai_stock, sentiment_info)
            combined_stocks.append(combined_stock)
        
        # Sort by combined score (highest first)
        combined_stocks.sort(key=lambda x: x['combined_score'], reverse=True)
        
        # Create summary statistics
        summary = self._create_combined_summary(combined_stocks, ai_results, sentiment_results)
        
        return {
            'combined_rankings': combined_stocks,
            'summary': summary,
            'methodology': {
                'ai_weight': self.weights['ai_evaluation'],
                'sentiment_weight': self.weights['sentiment'],
                'description': 'Combined score = (AI Score × 0.7) + (Sentiment Score × 0.3)'
            }
        }
    
    def _create_combined_stock_analysis(self, ticker: str, ai_stock: Dict[str, Any], sentiment_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create combined analysis for a single stock.
        
        Args:
            ticker: Stock ticker symbol
            ai_stock: AI evaluation results for the stock
            sentiment_info: Sentiment analysis results for the stock
            
        Returns:
            Combined analysis results for the stock
        """
        # Extract AI evaluation details
        ai_score = ai_stock.get('total_score', 0)
        ai_recommendation = ai_stock.get('recommendation', 'Hold')
        ai_commentary = ai_stock.get('commentary', 'No commentary available')
        
        # Extract sentiment details  
        sentiment_score_raw = sentiment_info.get('overall_sentiment_score', 0.0)
        sentiment_mentions = sentiment_info.get('total_mentions', 0)
        sentiment_percentages = sentiment_info.get('sentiment_percentages', {})
        trend_direction = sentiment_info.get('trend_direction', 'stable')
        
        # Convert sentiment score (-1 to +1) to 0-100 scale for consistency
        sentiment_score = max(0, min(100, (sentiment_score_raw + 1) * 50))
        
        # Calculate combined score
        combined_score = (
            ai_score * self.weights['ai_evaluation'] + 
            sentiment_score * self.weights['sentiment']
        )
        
        # Generate combined recommendation
        combined_recommendation = self._get_combined_recommendation(combined_score, ai_score, sentiment_score)
        
        # Create sentiment summary
        sentiment_summary = self._create_sentiment_summary(sentiment_info)
        
        # Create AI reasoning summary
        ai_reasoning = self._create_ai_reasoning(ai_stock)
        
        return {
            'ticker': ticker,
            'combined_score': round(combined_score, 2),
            'combined_recommendation': combined_recommendation,
            'ai_evaluation': {
                'score': ai_score,
                'recommendation': ai_recommendation,
                'reasoning': ai_reasoning
            },
            'sentiment_analysis': {
                'score': round(sentiment_score, 2),
                'raw_score': sentiment_score_raw,
                'total_mentions': sentiment_mentions,
                'trend_direction': trend_direction,
                'summary': sentiment_summary
            },
            'price': ai_stock.get('price', 'N/A'),
            'market_cap': ai_stock.get('market_cap', 'N/A')
        }
    
    def _get_combined_recommendation(self, combined_score: float, ai_score: float, sentiment_score: float) -> str:
        """
        Generate combined recommendation based on both AI and sentiment scores.
        
        Args:
            combined_score: Overall combined score
            ai_score: AI evaluation score
            sentiment_score: Sentiment score (0-100 scale)
            
        Returns:
            Combined recommendation (Buy/Hold/Avoid)
        """
        # Strong Buy: High combined score AND both components are strong
        if combined_score >= 75 and ai_score >= 70 and sentiment_score >= 60:
            return "Buy"
        
        # Hold: Moderate combined score OR mixed signals
        elif combined_score >= 50:
            return "Hold"
        
        # Avoid: Low combined score OR negative sentiment with weak AI
        else:
            return "Avoid"
    
    def _create_sentiment_summary(self, sentiment_info: Dict[str, Any]) -> str:
        """
        Create a human-readable sentiment summary.
        
        Args:
            sentiment_info: Sentiment analysis data
            
        Returns:
            Human-readable sentiment summary
        """
        if not sentiment_info or sentiment_info.get('total_mentions', 0) == 0:
            return "Limited social media activity with neutral sentiment"
        
        mentions = sentiment_info.get('total_mentions', 0)
        score = sentiment_info.get('overall_sentiment_score', 0.0)
        percentages = sentiment_info.get('sentiment_percentages', {})
        trend = sentiment_info.get('trend_direction', 'stable')
        
        # Determine sentiment tone
        if score > 0.1:
            tone = "positive"
        elif score < -0.1:
            tone = "negative"
        else:
            tone = "neutral"
        
        # Build summary
        summary_parts = []
        
        # Mention volume
        if mentions > 50:
            summary_parts.append(f"High social media activity ({mentions} mentions)")
        elif mentions > 10:
            summary_parts.append(f"Moderate social media activity ({mentions} mentions)")
        else:
            summary_parts.append(f"Limited social media activity ({mentions} mentions)")
        
        # Sentiment breakdown
        if percentages:
            pos_pct = percentages.get('positive', 0)
            neg_pct = percentages.get('negative', 0)
            summary_parts.append(f"with {tone} sentiment ({pos_pct}% positive, {neg_pct}% negative)")
        else:
            summary_parts.append(f"with {tone} sentiment")
        
        # Trend
        if trend == 'improving':
            summary_parts.append("and improving trend")
        elif trend == 'declining':
            summary_parts.append("but declining trend")
        
        return " ".join(summary_parts)
    
    def _create_ai_reasoning(self, ai_stock: Dict[str, Any]) -> str:
        """
        Create a concise AI reasoning summary.
        
        Args:
            ai_stock: AI evaluation results
            
        Returns:
            Concise AI reasoning summary
        """
        scores = ai_stock.get('scores', {})
        commentary = ai_stock.get('commentary', '')
        
        # Extract key strengths and weaknesses
        reasoning_parts = []
        
        # Technical position
        technical_score = scores.get('technical_position', 0)
        if technical_score >= 70:
            reasoning_parts.append("strong technical position")
        elif technical_score <= 30:
            reasoning_parts.append("weak technical position")
        
        # Valuation
        valuation_score = scores.get('valuation', 0)
        if valuation_score >= 70:
            reasoning_parts.append("attractive valuation")
        elif valuation_score <= 30:
            reasoning_parts.append("expensive valuation")
        
        # Risk/Reward
        risk_reward_score = scores.get('risk_reward', 0)
        if risk_reward_score >= 70:
            reasoning_parts.append("favorable risk/reward ratio")
        
        # Momentum
        momentum_score = scores.get('momentum', 0)
        if momentum_score >= 70:
            reasoning_parts.append("positive momentum")
        elif momentum_score <= 30:
            reasoning_parts.append("weak momentum")
        
        if reasoning_parts:
            return f"AI analysis shows {', '.join(reasoning_parts)}"
        else:
            return commentary if commentary else "Mixed technical and fundamental indicators"
    
    def _create_combined_summary(self, combined_stocks: List[Dict[str, Any]], ai_results: Dict[str, Any], sentiment_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create summary statistics for the combined analysis.
        
        Args:
            combined_stocks: List of combined stock analyses
            ai_results: Original AI evaluation results
            sentiment_results: Original sentiment analysis results
            
        Returns:
            Summary statistics
        """
        if not combined_stocks:
            return {
                'total_stocks_analyzed': 0,
                'buy_recommendations': 0,
                'hold_recommendations': 0,
                'avoid_recommendations': 0
            }
        
        # Count recommendations
        buy_count = sum(1 for stock in combined_stocks if stock['combined_recommendation'] == 'Buy')
        hold_count = sum(1 for stock in combined_stocks if stock['combined_recommendation'] == 'Hold')
        avoid_count = sum(1 for stock in combined_stocks if stock['combined_recommendation'] == 'Avoid')
        
        # Get top recommendation
        top_stock = combined_stocks[0] if combined_stocks else None
        
        # Calculate average scores
        avg_combined_score = sum(stock['combined_score'] for stock in combined_stocks) / len(combined_stocks)
        avg_ai_score = sum(stock['ai_evaluation']['score'] for stock in combined_stocks) / len(combined_stocks)
        avg_sentiment_score = sum(stock['sentiment_analysis']['score'] for stock in combined_stocks) / len(combined_stocks)
        
        return {
            'total_stocks_analyzed': len(combined_stocks),
            'buy_recommendations': buy_count,
            'hold_recommendations': hold_count,
            'avoid_recommendations': avoid_count,
            'top_recommendation': {
                'ticker': top_stock['ticker'] if top_stock else None,
                'combined_score': top_stock['combined_score'] if top_stock else 0,
                'recommendation': top_stock['combined_recommendation'] if top_stock else 'N/A'
            },
            'average_scores': {
                'combined': round(avg_combined_score, 2),
                'ai_evaluation': round(avg_ai_score, 2),
                'sentiment': round(avg_sentiment_score, 2)
            },
            'sentiment_coverage': {
                'total_mentions': sentiment_results.get('portfolio_summary', {}).get('total_mentions', 0),
                'most_mentioned': sentiment_results.get('portfolio_summary', {}).get('most_mentioned_ticker', 'N/A')
            }
        }


def analyze_combined_portfolio(tickers: List[str], stock_data: Dict[str, Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Convenience function to run combined portfolio analysis.
    
    Args:
        tickers: List of stock ticker symbols
        stock_data: Optional pre-fetched stock data
        
    Returns:
        Combined analysis results
    """
    analyzer = CombinedStockAnalyzer()
    return analyzer.analyze_portfolio(tickers, stock_data)