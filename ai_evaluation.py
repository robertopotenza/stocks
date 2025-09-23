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
        self.weights = {
            'technical_position': 0.25,    # Position relative to support/resistance
            'valuation': 0.20,             # PE ratio and valuation flags
            'risk_reward': 0.20,           # Risk/reward ratio
            'momentum': 0.15,              # Distance from 52w high/low
            'upside_potential': 0.10,      # Upside vs downside potential
            'sentiment': 0.10              # Social media sentiment
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
        # Skip if no price data
        price = data.get('Price')
        if not isinstance(price, (int, float)) or price <= 0:
            return None
        
        # Calculate individual component scores
        technical_score = self._score_technical_position(data)
        valuation_score = self._score_valuation(data)
        risk_reward_score = self._score_risk_reward(data)
        momentum_score = self._score_momentum(data)
        upside_score = self._score_upside_potential(data)
        sentiment_score = self._score_sentiment(data)
        
        # Calculate weighted total score
        total_score = (
            technical_score * self.weights['technical_position'] +
            valuation_score * self.weights['valuation'] +
            risk_reward_score * self.weights['risk_reward'] +
            momentum_score * self.weights['momentum'] +
            upside_score * self.weights['upside_potential'] +
            sentiment_score * self.weights['sentiment']
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
            'price': price,
            'pe_ratio': data.get('PE_Ratio', 'N/A'),
            'risk_reward_ratio': data.get('Risk_Reward_Ratio', 'N/A'),
            'distance_from_52w_high': data.get('Distance_from_52w_High_Pct', 'N/A'),
            'valuation_flag': data.get('Valuation_Flag', 'N/A'),
            'entry_flag': data.get('Entry_Opportunity_Flag', 'N/A'),
            'price_level_flag': data.get('Price_Level_Flag', 'N/A'),
            'sentiment_data': sentiment_info,
            'sentiment': sentiment_data.get('overall_sentiment_score', 0.0) if sentiment_data else 0.0
        }
    
    def _score_technical_position(self, data: Dict[str, Any]) -> float:
        """Score based on technical position relative to support/resistance."""
        score = 50.0  # Neutral base score
        
        price = data.get('Price')
        recent_support = data.get('Recent_Support')
        recent_resistance = data.get('Recent_Resistance')
        pivot_support = data.get('Pivot_Support_1')
        pivot_resistance = data.get('Pivot_Resistance_1')
        
        if not isinstance(price, (int, float)):
            return score
        
        # Score based on position relative to support levels
        if isinstance(recent_support, (int, float)) and recent_support > 0:
            support_distance = ((price - recent_support) / recent_support) * 100
            if support_distance < 2:  # Very close to support
                score += 30
            elif support_distance < 5:  # Near support
                score += 20
            elif support_distance > 20:  # Far from support
                score -= 10
        
        # Score based on position relative to resistance levels  
        if isinstance(recent_resistance, (int, float)) and recent_resistance > price:
            resistance_distance = ((recent_resistance - price) / price) * 100
            if resistance_distance > 10:  # Good upside room
                score += 20
            elif resistance_distance < 3:  # Near resistance
                score -= 20
        
        # Additional scoring from pivot levels
        if isinstance(pivot_support, (int, float)) and isinstance(pivot_resistance, (int, float)):
            if pivot_support > 0 and pivot_resistance > price:
                position_in_range = (price - pivot_support) / (pivot_resistance - pivot_support)
                if position_in_range < 0.3:  # In lower 30% of range
                    score += 15
                elif position_in_range > 0.7:  # In upper 70% of range
                    score -= 10
        
        return max(0, min(100, score))
    
    def _score_valuation(self, data: Dict[str, Any]) -> float:
        """Score based on valuation metrics."""
        score = 50.0  # Neutral base score
        
        pe_ratio = data.get('PE_Ratio')
        valuation_flag = data.get('Valuation_Flag')
        
        # Score based on PE ratio
        if isinstance(pe_ratio, (int, float)) and pe_ratio > 0:
            if pe_ratio < 15:  # Very attractive valuation
                score += 40
            elif pe_ratio < 20:  # Good valuation
                score += 25
            elif pe_ratio < 25:  # Fair valuation
                score += 10
            elif pe_ratio < 30:  # Slightly expensive
                score -= 10
            else:  # Expensive
                score -= 30
        
        # Adjust based on valuation flag
        if valuation_flag == "Undervalued":
            score += 20
        elif valuation_flag == "Overvalued":
            score -= 25
        
        return max(0, min(100, score))
    
    def _score_risk_reward(self, data: Dict[str, Any]) -> float:
        """Score based on risk/reward ratio using standardized normalization."""
        risk_reward = data.get('Risk_Reward_Ratio')
        entry_flag = data.get('Entry_Opportunity_Flag')
        
        # Base score using direct ratio normalization as specified
        # RR Score = min(100, (RR/Max RR) × 100)
        # Using max RR = 10 as suggested in requirements
        max_rr = 10.0
        
        if isinstance(risk_reward, (int, float)) and risk_reward > 0:
            # Direct ratio normalization: RR Score = min(100, (RR/Max RR) × 100)
            score = min(100, (risk_reward / max_rr) * 100)
        else:
            score = 0.0  # No risk/reward data available
        
        # Adjust based on entry flag (small adjustment to the normalized score)
        if entry_flag == "Favorable":
            score = min(100, score + 10)  # Bonus for favorable entry
        elif entry_flag == "Unfavorable":
            score = max(0, score - 15)   # Penalty for unfavorable entry
        
        return max(0, min(100, score))
    
    def _score_momentum(self, data: Dict[str, Any]) -> float:
        """Score based on price momentum and 52-week positioning."""
        score = 50.0  # Neutral base score
        
        dist_from_high = data.get('Distance_from_52w_High_Pct')
        dist_from_low = data.get('Distance_from_52w_Low_Pct')
        price_level_flag = data.get('Price_Level_Flag')
        
        # Score based on distance from 52-week high
        if isinstance(dist_from_high, (int, float)):
            if dist_from_high > 50:  # Far from high - potential upside
                score += 25
            elif dist_from_high > 30:  # Moderate distance from high
                score += 15
            elif dist_from_high < 5:  # Very close to high - may be topped out
                score -= 15
        
        # Score based on distance from 52-week low
        if isinstance(dist_from_low, (int, float)):
            if dist_from_low < 20:  # Close to low - may be bottoming
                score += 10
            elif dist_from_low > 80:  # Far from low - good momentum
                score += 15
        
        # Adjust based on price level flag
        if price_level_flag == "Near Bottom":
            score += 20
        elif price_level_flag == "Near Top":
            score -= 15
        
        return max(0, min(100, score))
    
    def _score_upside_potential(self, data: Dict[str, Any]) -> float:
        """Score based on upside vs downside potential."""
        score = 50.0  # Neutral base score
        
        upside_potential = data.get('Upside_Potential_Pct')
        downside_risk = data.get('Downside_Risk_Pct')
        
        # Score based on upside potential
        if isinstance(upside_potential, (int, float)):
            if upside_potential > 20:  # High upside potential
                score += 30
            elif upside_potential > 10:  # Moderate upside
                score += 15
            elif upside_potential < 5:  # Limited upside
                score -= 10
        
        # Penalize high downside risk
        if isinstance(downside_risk, (int, float)):
            if downside_risk > 15:  # High downside risk
                score -= 20
            elif downside_risk > 10:  # Moderate downside risk
                score -= 10
        
        return max(0, min(100, score))
    
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
        """Generate AI commentary for the stock."""
        price = data.get('Price')
        pe_ratio = data.get('PE_Ratio')
        valuation_flag = data.get('Valuation_Flag', 'N/A')
        risk_reward = data.get('Risk_Reward_Ratio')
        dist_from_high = data.get('Distance_from_52w_High_Pct')
        upside_potential = data.get('Upside_Potential_Pct')
        entry_flag = data.get('Entry_Opportunity_Flag', 'N/A')
        
        commentary_parts = []
        
        # Valuation assessment
        if isinstance(pe_ratio, (int, float)):
            if pe_ratio < 15:
                commentary_parts.append(f"attractively valued at {pe_ratio:.1f}x earnings")
            elif pe_ratio < 25:
                commentary_parts.append(f"fairly priced at {pe_ratio:.1f}x earnings")
            else:
                commentary_parts.append(f"expensive at {pe_ratio:.1f}x earnings")
        elif valuation_flag != 'N/A':
            commentary_parts.append(f"appears {valuation_flag.lower()}")
        
        # Technical position
        if scores['technical'] > 70:
            commentary_parts.append("strong technical setup near support levels")
        elif scores['technical'] < 30:
            commentary_parts.append("challenging technical position near resistance")
        else:
            commentary_parts.append("neutral technical position")
        
        # Risk/reward assessment
        if isinstance(risk_reward, (int, float)):
            if risk_reward > 2:
                commentary_parts.append(f"excellent risk/reward ratio of {risk_reward:.1f}")
            elif risk_reward > 1.5:
                commentary_parts.append(f"favorable risk/reward of {risk_reward:.1f}")
            else:
                commentary_parts.append(f"limited risk/reward of {risk_reward:.1f}")
        elif entry_flag == "Favorable":
            commentary_parts.append("favorable entry opportunity")
        
        # Distance from highs
        if isinstance(dist_from_high, (int, float)) and dist_from_high > 30:
            commentary_parts.append(f"{dist_from_high:.0f}% below 52-week high")
        
        # Upside potential
        if isinstance(upside_potential, (int, float)) and upside_potential > 10:
            commentary_parts.append(f"{upside_potential:.0f}% upside potential to resistance")
        
        # Sentiment analysis
        sentiment_data = data.get('sentiment_data', {})
        if sentiment_data and sentiment_data.get('total_mentions', 0) > 0:
            sentiment_score = sentiment_data.get('overall_sentiment_score', 0)
            mentions = sentiment_data.get('total_mentions', 0)
            trend = sentiment_data.get('trend_direction', 'stable')
            
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
                commentary_parts.append(f"{sentiment_desc} social media sentiment with {mentions} mentions")
            elif mentions > 0:
                commentary_parts.append(f"{sentiment_desc} sentiment from social media")
        
        # Combine commentary
        if commentary_parts:
            return f"{ticker} is " + ", ".join(commentary_parts) + "."
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
                                           include_sentiment: bool = True) -> Dict[str, Any]:
    """
    Enhanced function to evaluate a portfolio of stocks with optional sentiment analysis.
    
    Args:
        stock_data: Dictionary mapping ticker to stock data
        include_sentiment: Whether to include sentiment analysis
        
    Returns:
        Dictionary containing ranked stocks and portfolio summary with sentiment data
    """
    from sentiment_analysis import analyze_portfolio_sentiment
    
    logger.info("🤖 Starting enhanced AI-powered stock evaluation with sentiment analysis...")
    
    # Get list of tickers for sentiment analysis
    tickers = list(stock_data.keys())
    
    # Fetch sentiment data if requested
    sentiment_results = {}
    if include_sentiment and tickers:
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