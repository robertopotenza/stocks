#!/usr/bin/env python3
"""
AI-Powered Stock Evaluation Module

This module provides intelligent analysis and ranking of stock data based on
technical analysis, valuation metrics, and risk-reward characteristics.
It automatically interprets key metrics and provides plain English recommendations.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from logging_config import get_logger

# Get logger instance
logger = get_logger('stocks_app.ai_evaluation')


class StockEvaluator:
    """AI-powered stock evaluation and ranking engine."""
    
    def __init__(self):
        """Initialize the stock evaluator with scoring weights."""
        # Scoring weights for different factors (sum should be 1.0)
        # Note: sentiment removed from total score calculation per requirements
        self.weights = {
            'technical_position': 0.28,    # Position relative to support/resistance (increased from 0.25)
            'valuation': 0.22,             # PE ratio and valuation flags (increased from 0.20)
            'risk_reward': 0.22,           # Risk/reward ratio (increased from 0.20)
            'momentum': 0.17,              # Distance from 52w high/low (increased from 0.15)
            'upside_potential': 0.11       # Upside vs downside potential (increased from 0.10)
        }
    
    def evaluate_stocks(self, stock_data: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Evaluate and rank stocks based on AI analysis.
        
        Args:
            stock_data: Dictionary mapping ticker to stock data
            
        Returns:
            List of evaluated stocks sorted by attractiveness score
        """
        evaluated_stocks = []
        
        for ticker, data in stock_data.items():
            try:
                evaluation = self._evaluate_single_stock(ticker, data)
                if evaluation:
                    evaluated_stocks.append(evaluation)
            except Exception as e:
                logger.error(f"Error evaluating {ticker}: {e}")
                continue
        
        # Sort by total score (descending - higher is better)
        evaluated_stocks.sort(key=lambda x: x['total_score'], reverse=True)
        
        return evaluated_stocks
    
    def _evaluate_single_stock(self, ticker: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a single stock and calculate comprehensive scoring.
        
        Args:
            ticker: Stock ticker symbol
            data: Stock data dictionary
            
        Returns:
            Dictionary containing evaluation results and scores
        """
        # Always proceed with evaluation since we use neutral defaults now
        
        # Calculate individual component scores
        technical_score = self._score_technical_position(data)
        valuation_score = self._score_valuation(data)
        risk_reward_score = self._score_risk_reward(data)
        momentum_score = self._score_momentum(data)
        upside_score = self._score_upside_potential(data)
        sentiment_score = self._score_sentiment(data)
        
        # Calculate weighted total score (excluding sentiment per requirements)
        total_score = (
            technical_score * self.weights['technical_position'] +
            valuation_score * self.weights['valuation'] +
            risk_reward_score * self.weights['risk_reward'] +
            momentum_score * self.weights['momentum'] +
            upside_score * self.weights['upside_potential']
        )
        
        # Generate AI commentary
        commentary = self._generate_commentary(ticker, data, {
            'technical': technical_score,
            'valuation': valuation_score,
            'risk_reward': risk_reward_score,
            'momentum': momentum_score,
            'upside': upside_score,
            'sentiment': sentiment_score
        })
        
        # Determine overall recommendation
        recommendation = self._get_recommendation(total_score)
        
        # Extract sentiment information for the record
        sentiment_data = data.get('sentiment_data', {})
        sentiment_info = None
        if sentiment_data and sentiment_data.get('total_mentions', 0) > 0:
            sentiment_info = {
                'overall_sentiment_score': sentiment_data.get('overall_sentiment_score', 0.0),
                'total_mentions': sentiment_data.get('total_mentions', 0),
                'trend_direction': sentiment_data.get('trend_direction', 'stable'),
                'sentiment_percentages': sentiment_data.get('sentiment_percentages', {})
            }

        return {
            'ticker': ticker,
            'total_score': round(total_score, 2),
            'recommendation': recommendation,
            'commentary': commentary,
            'scores': {
                'technical_position': round(technical_score, 2),
                'valuation': round(valuation_score, 2),
                'risk_reward': round(risk_reward_score, 2),
                'momentum': round(momentum_score, 2),
                'upside_potential': round(upside_score, 2),
                'sentiment': round(sentiment_score, 2)
            },
            'sentiment_data': sentiment_info,
            'sentiment': sentiment_data.get('overall_sentiment_score', 0.0) if sentiment_data else 0.0
        }
    
    def _score_technical_position(self, data: Dict[str, Any]) -> float:
        """Score based on technical position - using neutral default since fields are removed."""
        # Return neutral score since technical fields (Support/Resistance) are removed
        return 50.0
    
    def _score_valuation(self, data: Dict[str, Any]) -> float:
        """Score based on valuation metrics - using neutral default since fields are removed."""
        # Return neutral score since valuation fields (PE_Ratio, Valuation_Flag) are removed
        return 50.0
    
    def _score_risk_reward(self, data: Dict[str, Any]) -> float:
        """Score based on risk/reward ratio - using neutral default since fields are removed."""
        # Return neutral score since risk/reward fields are removed
        return 50.0
    
    def _score_momentum(self, data: Dict[str, Any]) -> float:
        """Score based on price momentum - using neutral default since fields are removed."""
        # Return neutral score since momentum fields (Distance_from_52w_High_Pct, etc.) are removed
        return 50.0
    
    def _score_upside_potential(self, data: Dict[str, Any]) -> float:
        """Score based on upside potential - using neutral default since fields are removed."""
        # Return neutral score since upside/downside fields are removed
        return 50.0
    
    def _score_sentiment(self, data: Dict[str, Any]) -> float:
        """Score based on social media sentiment analysis."""
        score = 50.0  # Neutral base score
        
        sentiment_data = data.get('sentiment_data', {})
        
        if not sentiment_data or sentiment_data.get('total_mentions', 0) == 0:
            # No sentiment data available - return neutral score
            return score
        
        overall_sentiment_score = sentiment_data.get('overall_sentiment_score', 0.0)
        total_mentions = sentiment_data.get('total_mentions', 0)
        trend_direction = sentiment_data.get('trend_direction', 'stable')
        sentiment_percentages = sentiment_data.get('sentiment_percentages', {})
        
        # Base sentiment score (compound score from -1 to +1)
        # Convert to 0-100 scale
        sentiment_adjustment = overall_sentiment_score * 30  # Scale to max ±30 points
        score += sentiment_adjustment
        
        # Bonus for high volume of mentions (indicates high interest)
        if total_mentions > 50:
            score += 10
        elif total_mentions > 20:
            score += 5
        
        # Trend direction bonus/penalty
        if trend_direction == 'improving':
            score += 10
        elif trend_direction == 'declining':
            score -= 10
        
        # Bonus for overwhelmingly positive sentiment
        positive_pct = sentiment_percentages.get('positive', 0)
        negative_pct = sentiment_percentages.get('negative', 0)
        
        if positive_pct > 60 and negative_pct < 20:
            score += 15  # Very positive sentiment
        elif positive_pct < 20 and negative_pct > 60:
            score -= 15  # Very negative sentiment
        
        return max(0, min(100, score))
    
    def _generate_commentary(self, ticker: str, data: Dict[str, Any], scores: Dict[str, float]) -> str:
        """Generate AI commentary for the stock based on available data."""
        commentary_parts = []
        
        # Since removed fields are no longer available, use neutral scoring-based commentary
        total_score = (
            scores['technical'] * self.weights['technical_position'] +
            scores['valuation'] * self.weights['valuation'] +
            scores['risk_reward'] * self.weights['risk_reward'] +
            scores['momentum'] * self.weights['momentum'] +
            scores['upside'] * self.weights['upside_potential']
        )
        
        # Overall assessment based on score components
        if total_score >= 70:
            commentary_parts.append("shows strong overall characteristics")
        elif total_score >= 60:
            commentary_parts.append("presents moderate investment appeal")
        elif total_score >= 40:
            commentary_parts.append("shows neutral investment characteristics")
        else:
            commentary_parts.append("presents some investment challenges")
        
        # Sentiment analysis (if available)
        sentiment_data = data.get('sentiment_data', {})
        if sentiment_data and sentiment_data.get('total_mentions', 0) > 0:
            sentiment_score = sentiment_data.get('overall_sentiment_score', 0)
            mentions = sentiment_data.get('total_mentions', 0)
            
            if sentiment_score > 0.2:
                sentiment_desc = "very positive"
            elif sentiment_score > 0.05:
                sentiment_desc = "positive"
            elif sentiment_score < -0.2:
                sentiment_desc = "very negative"
            elif sentiment_score < -0.05:
                sentiment_desc = "negative"
            else:
                sentiment_desc = "neutral"
            
            if mentions > 20:
                commentary_parts.append(f"with {sentiment_desc} social media sentiment ({mentions} mentions)")
            elif mentions > 0:
                commentary_parts.append(f"with {sentiment_desc} social media sentiment")
        
        # Combine commentary
        if commentary_parts:
            return f"{ticker} " + ", ".join(commentary_parts) + "."
        else:
            return f"{ticker} has limited data for comprehensive analysis."
    
    def _get_recommendation(self, total_score: float) -> str:
        """Get recommendation based on standardized total score thresholds."""
        # Standardized recommendation tiers:
        # Strong Buy ≥ 70, Buy 60-69, Hold 50-59, Weak Hold 40-49, Avoid < 40
        if total_score >= 70:
            return "Strong Buy"
        elif total_score >= 60:
            return "Buy"
        elif total_score >= 50:
            return "Hold"
        elif total_score >= 40:
            return "Weak Hold"
        else:
            return "Avoid"


def evaluate_stock_portfolio(stock_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Main function to evaluate a portfolio of stocks using AI analysis.
    
    Args:
        stock_data: Dictionary mapping ticker to stock data
        
    Returns:
        Dictionary containing ranked stocks and portfolio summary
    """
    evaluator = StockEvaluator()
    
    logger.info("🤖 Starting AI-powered stock evaluation...")
    
    # Evaluate all stocks
    evaluated_stocks = evaluator.evaluate_stocks(stock_data)
    
    if not evaluated_stocks:
        logger.warning("No stocks could be evaluated")
        return {
            'ranked_stocks': [],
            'summary': {
                'total_stocks': 0,
                'strong_buys': 0,
                'buys': 0,
                'holds': 0,
                'weak_holds': 0,
                'avoids': 0
            }
        }
    
    # Generate summary statistics
    total_stocks = len(evaluated_stocks)
    recommendations = [stock['recommendation'] for stock in evaluated_stocks]
    
    summary = {
        'total_stocks': total_stocks,
        'strong_buys': recommendations.count('Strong Buy'),
        'buys': recommendations.count('Buy'),
        'holds': recommendations.count('Hold'),
        'weak_holds': recommendations.count('Weak Hold'),
        'avoids': recommendations.count('Avoid'),
        'top_pick': evaluated_stocks[0]['ticker'] if evaluated_stocks else None,
        'average_score': round(np.mean([s['total_score'] for s in evaluated_stocks]), 2)
    }
    
    logger.info(f"✅ Evaluated {total_stocks} stocks")
    logger.info(f"🎯 Top pick: {summary['top_pick']} (Score: {evaluated_stocks[0]['total_score']})")
    logger.info(f"📊 Strong Buys: {summary['strong_buys']}, Buys: {summary['buys']}, Holds: {summary['holds']}")
    
    return {
        'ranked_stocks': evaluated_stocks,
        'summary': summary
    }


def evaluate_stock_portfolio_with_sentiment(stock_data: Dict[str, Dict[str, Any]], 
                                           include_sentiment: bool = True,
                                           sentiment_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Enhanced function to evaluate a portfolio of stocks with optional sentiment analysis.
    
    Args:
        stock_data: Dictionary mapping ticker to stock data
        include_sentiment: Whether to include sentiment analysis
        sentiment_data: Optional pre-fetched sentiment data
        
    Returns:
        Dictionary containing ranked stocks and portfolio summary with sentiment data
    """
    from sentiment_analysis import analyze_portfolio_sentiment
    
    logger.info("🤖 Starting enhanced AI-powered stock evaluation with sentiment analysis...")
    
    # Get list of tickers for sentiment analysis
    tickers = list(stock_data.keys())
    
    # Use provided sentiment data or fetch fresh data if requested
    sentiment_results = {}
    if include_sentiment and tickers:
        if sentiment_data:
            logger.info("📱 Using provided sentiment analysis data...")
            sentiment_results = sentiment_data.get('sentiment_data', {})
        else:
            try:
                logger.info(f"📱 Analyzing social media sentiment for {len(tickers)} tickers...")
                portfolio_sentiment = analyze_portfolio_sentiment(tickers, days=5)
                sentiment_results = portfolio_sentiment.get('sentiment_data', {})
                logger.info(f"✅ Sentiment analysis completed for {len(sentiment_results)} tickers")
            except Exception as e:
                logger.warning(f"Failed to fetch sentiment data: {e}")
                sentiment_results = {}
    
    # Integrate sentiment data into stock data
    enhanced_stock_data = {}
    for ticker, data in stock_data.items():
        enhanced_data = data.copy()
        if ticker in sentiment_results:
            enhanced_data['sentiment_data'] = sentiment_results[ticker]
        enhanced_stock_data[ticker] = enhanced_data
    
    # Run standard AI evaluation with enhanced data
    evaluation_result = evaluate_stock_portfolio(enhanced_stock_data)
    
    # Add sentiment summary to the result
    if sentiment_results:
        # Calculate portfolio sentiment metrics
        total_mentions = sum(s.get('total_mentions', 0) for s in sentiment_results.values())
        
        # Sort by sentiment for most/least positive
        sentiment_sorted = sorted(
            [(ticker, data) for ticker, data in sentiment_results.items()],
            key=lambda x: x[1].get('overall_sentiment_score', 0),
            reverse=True
        )
        
        most_positive_ticker = sentiment_sorted[0][0] if sentiment_sorted else None
        most_negative_ticker = sentiment_sorted[-1][0] if sentiment_sorted else None
        
        # Calculate average sentiment score weighted by mentions
        if total_mentions > 0:
            weighted_sentiment = sum(
                data.get('overall_sentiment_score', 0) * data.get('total_mentions', 0)
                for data in sentiment_results.values()
            ) / total_mentions
        else:
            weighted_sentiment = 0.0
        
        evaluation_result['sentiment_summary'] = {
            'total_mentions_across_portfolio': total_mentions,
            'average_sentiment_score': round(weighted_sentiment, 3),
            'most_positive_ticker': most_positive_ticker,
            'most_negative_ticker': most_negative_ticker,
            'tickers_with_sentiment': len(sentiment_results),
            'sentiment_data': sentiment_results
        }
    
    return evaluation_result