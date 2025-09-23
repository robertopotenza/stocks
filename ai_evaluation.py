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
            'technical_position': 0.30,    # Position relative to support/resistance
            'valuation': 0.25,             # PE ratio and valuation flags
            'risk_reward': 0.20,           # Risk/reward ratio
            'momentum': 0.15,              # Distance from 52w high/low
            'upside_potential': 0.10       # Upside vs downside potential
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
        
        # Calculate weighted total score
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
            'upside': upside_score
        })
        
        # Determine overall recommendation
        recommendation = self._get_recommendation(total_score)
        
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
                'upside_potential': round(upside_score, 2)
            },
            'price': price,
            'pe_ratio': data.get('PE_Ratio', 'N/A'),
            'risk_reward_ratio': data.get('Risk_Reward_Ratio', 'N/A'),
            'distance_from_52w_high': data.get('Distance_from_52w_High_Pct', 'N/A'),
            'valuation_flag': data.get('Valuation_Flag', 'N/A'),
            'entry_flag': data.get('Entry_Opportunity_Flag', 'N/A'),
            'price_level_flag': data.get('Price_Level_Flag', 'N/A')
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
        """Score based on risk/reward ratio."""
        score = 50.0  # Neutral base score
        
        risk_reward = data.get('Risk_Reward_Ratio')
        entry_flag = data.get('Entry_Opportunity_Flag')
        
        if isinstance(risk_reward, (int, float)):
            if risk_reward > 3:  # Excellent risk/reward
                score += 40
            elif risk_reward > 2:  # Good risk/reward
                score += 25
            elif risk_reward > 1.5:  # Decent risk/reward
                score += 10
            elif risk_reward < 1:  # Poor risk/reward
                score -= 30
        
        # Adjust based on entry flag
        if entry_flag == "Favorable":
            score += 15
        elif entry_flag == "Unfavorable":
            score -= 20
        
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
        
        # Combine commentary
        if commentary_parts:
            return f"{ticker} is " + ", ".join(commentary_parts) + "."
        else:
            return f"{ticker} has limited data for comprehensive analysis."
    
    def _get_recommendation(self, total_score: float) -> str:
        """Get recommendation based on total score."""
        if total_score >= 75:
            return "Strong Buy"
        elif total_score >= 60:
            return "Buy"
        elif total_score >= 45:
            return "Hold"
        elif total_score >= 30:
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