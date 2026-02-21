"""
Trader Health Score Module
Computes composite health score (0-100) from multiple risk dimensions.

Health Score Components:
- Risk Discipline (30%)
- Behavioral Stability (30%)
- Exposure Control (20%)
- Performance Consistency (20%)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum


class HealthStatus(Enum):
    """Health status categories."""
    HEALTHY = "healthy"
    CAUTION = "caution"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class HealthReport:
    """Container for trader health assessment."""
    trader_id: str
    health_score: float
    status: HealthStatus
    component_scores: Dict[str, float]
    risk_factors: List[str]
    recommendations: List[str]


class TraderHealthScorer:
    """
    Calculates comprehensive trader health score (0-100).
    
    Scoring Framework:
    - 80-100: Healthy (Green) - Trading within normal parameters
    - 60-79: Caution (Yellow) - Minor concerns, monitor closely
    - 40-59: Warning (Orange) - Significant issues, intervention recommended
    - 0-39: Critical (Red) - Immediate action required
    """
    
    def __init__(self):
        """Initialize health scorer with component weights."""
        self.weights = {
            'risk_discipline': 0.30,
            'behavioral_stability': 0.30,
            'exposure_control': 0.20,
            'performance_consistency': 0.20
        }
        
        self.thresholds = {
            'healthy': 80,
            'caution': 60,
            'warning': 40
        }
    
    def calculate_risk_discipline_score(self,
                                       trades_df: pd.DataFrame,
                                       trader_id: str) -> float:
        """
        Score risk discipline (0-100).
        
        Factors:
        - Position size consistency
        - Stop loss adherence
        - Max daily loss respect
        - Risk per trade variance
        
        Args:
            trades_df: DataFrame with trade data
            trader_id: Trader identifier
            
        Returns:
            Risk discipline score
        """
        trader_trades = trades_df[trades_df['trader_id'] == trader_id].copy()
        
        if len(trader_trades) < 5:
            return 50.0  # Neutral score for insufficient data
        
        score = 100.0
        
        # 1. Position size consistency (40 points)
        size_cv = trader_trades['quantity'].std() / trader_trades['quantity'].mean()
        if size_cv > 0.5:  # High variance
            score -= 40 * (min(size_cv, 2.0) / 2.0)
        
        # 2. Loss control (30 points)
        if 'pnl' in trader_trades.columns:
            losses = trader_trades[trader_trades['pnl'] < 0]
            if len(losses) > 0:
                max_loss = abs(losses['pnl'].min())
                avg_loss = abs(losses['pnl'].mean())
                
                # Penalize if max loss >> avg loss
                loss_ratio = max_loss / avg_loss if avg_loss > 0 else 1.0
                if loss_ratio > 3:  # Max loss 3x+ average
                    score -= 30 * (min(loss_ratio - 3, 7) / 7)
        
        # 3. Daily loss respect (30 points)
        if 'account_equity' in trader_trades.columns:
            trader_trades['date'] = pd.to_datetime(trader_trades['timestamp']).dt.date
            daily_pnl = trader_trades.groupby('date')['pnl'].sum()
            
            if len(daily_pnl) > 0:
                # Check for very large daily losses
                daily_loss_pct = (daily_pnl / trader_trades['account_equity'].mean())
                max_daily_loss = abs(daily_loss_pct.min())
                
                if max_daily_loss > 0.05:  # >5% daily loss
                    score -= 30 * (min(max_daily_loss, 0.20) / 0.20)
        
        return max(0, min(100, score))
    
    def calculate_behavioral_stability_score(self,
                                           trades_df: pd.DataFrame,
                                           trader_id: str,
                                           drift_signals: List = None) -> float:
        """
        Score behavioral stability (0-100).
        
        Factors:
        - Consistency in trading patterns
        - Absence of revenge trading
        - Stable frequency
        - Emotional control
        
        Args:
            trades_df: DataFrame with trade data
            trader_id: Trader identifier
            drift_signals: List of drift signals from BehavioralDriftDetector
            
        Returns:
            Behavioral stability score
        """
        trader_trades = trades_df[trades_df['trader_id'] == trader_id].copy()
        
        if len(trader_trades) < 5:
            return 50.0
        
        score = 100.0
        
        # 1. Penalize for drift signals (40 points)
        if drift_signals:
            from models.behavioral_drift import DriftSeverity
            
            critical_count = sum(1 for s in drift_signals if s.severity == DriftSeverity.CRITICAL)
            warning_count = sum(1 for s in drift_signals if s.severity == DriftSeverity.WARNING)
            
            score -= (critical_count * 20 + warning_count * 10)
        
        # 2. Trading frequency stability (30 points)
        trader_trades['date'] = pd.to_datetime(trader_trades['timestamp']).dt.date
        daily_counts = trader_trades.groupby('date').size()
        
        if len(daily_counts) > 1:
            freq_cv = daily_counts.std() / daily_counts.mean()
            if freq_cv > 0.5:  # Inconsistent frequency
                score -= 30 * (min(freq_cv, 2.0) / 2.0)
        
        # 3. Emotional control - no size spikes after losses (30 points)
        if len(trader_trades) >= 10:
            trader_trades = trader_trades.sort_values('timestamp')
            trader_trades['prev_pnl'] = trader_trades['pnl'].shift(1)
            
            # Compare size after losses vs after wins
            after_loss = trader_trades[trader_trades['prev_pnl'] < 0]
            after_win = trader_trades[trader_trades['prev_pnl'] > 0]
            
            if len(after_loss) > 0 and len(after_win) > 0:
                loss_size = after_loss['quantity'].mean()
                win_size = after_win['quantity'].mean()
                
                if loss_size > win_size * 1.3:  # 30% larger after losses
                    score -= 30
        
        return max(0, min(100, score))
    
    def calculate_exposure_control_score(self,
                                       trades_df: pd.DataFrame,
                                       trader_id: str,
                                       risk_signals: List = None) -> float:
        """
        Score exposure control (0-100).
        
        Factors:
        - Position diversification
        - Leverage management
        - Correlation risk
        
        Args:
            trades_df: DataFrame with trade data
            trader_id: Trader identifier
            risk_signals: List of risk signals from RiskEscalationMonitor
            
        Returns:
            Exposure control score
        """
        trader_trades = trades_df[trades_df['trader_id'] == trader_id].copy()
        
        if len(trader_trades) < 5:
            return 50.0
        
        score = 100.0
        
        # 1. Penalize for risk escalation signals (50 points)
        if risk_signals:
            from models.risk_escalation import RiskLevel
            
            critical_count = sum(1 for s in risk_signals if s.risk_level == RiskLevel.CRITICAL)
            dangerous_count = sum(1 for s in risk_signals if s.risk_level == RiskLevel.DANGEROUS)
            
            score -= (critical_count * 25 + dangerous_count * 15)
        
        # 2. Diversification (25 points)
        if 'symbol' in trader_trades.columns:
            unique_symbols = trader_trades['symbol'].nunique()
            total_trades = len(trader_trades)
            
            diversification_ratio = unique_symbols / total_trades
            
            if diversification_ratio < 0.3:  # Low diversification
                score -= 25 * (1 - diversification_ratio / 0.3)
        
        # 3. Leverage control (25 points)
        if 'account_equity' in trader_trades.columns:
            trader_trades['position_value'] = trader_trades['quantity'] * trader_trades.get('entry_price', trader_trades.get('price', 100))
            trader_trades['leverage'] = trader_trades['position_value'] / trader_trades['account_equity']
            
            avg_leverage = trader_trades['leverage'].mean()
            
            if avg_leverage > 3.0:  # High leverage
                score -= 25 * (min(avg_leverage - 3, 7) / 7)
        
        return max(0, min(100, score))
    
    def calculate_performance_consistency_score(self,
                                               trades_df: pd.DataFrame,
                                               trader_id: str) -> float:
        """
        Score performance consistency (0-100).
        
        Factors:
        - P&L stability
        - Win rate consistency
        - Drawdown recovery
        - Equity curve smoothness
        
        Args:
            trades_df: DataFrame with trade data
            trader_id: Trader identifier
            
        Returns:
            Performance consistency score
        """
        trader_trades = trades_df[trades_df['trader_id'] == trader_id].copy()
        
        if len(trader_trades) < 10:
            return 50.0
        
        score = 100.0
        
        # 1. P&L volatility (40 points)
        if 'pnl' in trader_trades.columns:
            avg_pnl = trader_trades['pnl'].mean()
            std_pnl = trader_trades['pnl'].std()
            
            if avg_pnl != 0:
                sharpe_proxy = abs(avg_pnl) / (std_pnl + 1e-10)
                
                # Good consistency: sharpe_proxy > 0.5
                if sharpe_proxy < 0.3:
                    score -= 40 * (1 - min(sharpe_proxy / 0.3, 1.0))
        
        # 2. Win rate stability (30 points)
        wins = (trader_trades['pnl'] > 0).sum()
        total = len(trader_trades)
        win_rate = wins / total if total > 0 else 0
        
        # Penalize very low win rates
        if win_rate < 0.35:
            score -= 30 * (1 - win_rate / 0.35)
        
        # 3. Drawdown severity (30 points)
        if 'account_equity' in trader_trades.columns:
            equity_curve = trader_trades['account_equity']
            running_max = equity_curve.expanding().max()
            drawdown = (equity_curve - running_max) / running_max
            max_drawdown = abs(drawdown.min())
            
            if max_drawdown > 0.15:  # >15% drawdown
                score -= 30 * (min(max_drawdown, 0.5) / 0.5)
        
        return max(0, min(100, score))
    
    def compute_health_score(self,
                           trades_df: pd.DataFrame,
                           trader_id: str,
                           drift_signals: List = None,
                           risk_signals: List = None) -> HealthReport:
        """
        Compute comprehensive trader health score.
        
        Args:
            trades_df: DataFrame with trade data
            trader_id: Trader identifier
            drift_signals: Behavioral drift signals
            risk_signals: Risk escalation signals
            
        Returns:
            HealthReport with score and details
        """
        # Calculate component scores
        risk_discipline = self.calculate_risk_discipline_score(trades_df, trader_id)
        behavioral_stability = self.calculate_behavioral_stability_score(
            trades_df, trader_id, drift_signals
        )
        exposure_control = self.calculate_exposure_control_score(
            trades_df, trader_id, risk_signals
        )
        performance_consistency = self.calculate_performance_consistency_score(
            trades_df, trader_id
        )
        
        component_scores = {
            'risk_discipline': risk_discipline,
            'behavioral_stability': behavioral_stability,
            'exposure_control': exposure_control,
            'performance_consistency': performance_consistency
        }
        
        # Weighted composite score
        health_score = (
            risk_discipline * self.weights['risk_discipline'] +
            behavioral_stability * self.weights['behavioral_stability'] +
            exposure_control * self.weights['exposure_control'] +
            performance_consistency * self.weights['performance_consistency']
        )
        
        # Determine status
        if health_score >= self.thresholds['healthy']:
            status = HealthStatus.HEALTHY
        elif health_score >= self.thresholds['caution']:
            status = HealthStatus.CAUTION
        elif health_score >= self.thresholds['warning']:
            status = HealthStatus.WARNING
        else:
            status = HealthStatus.CRITICAL
        
        # Identify risk factors
        risk_factors = []
        if risk_discipline < 60:
            risk_factors.append("Poor risk discipline")
        if behavioral_stability < 60:
            risk_factors.append("Behavioral instability detected")
        if exposure_control < 60:
            risk_factors.append("Exposure management issues")
        if performance_consistency < 60:
            risk_factors.append("Inconsistent performance")
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            component_scores, drift_signals, risk_signals
        )
        
        return HealthReport(
            trader_id=trader_id,
            health_score=health_score,
            status=status,
            component_scores=component_scores,
            risk_factors=risk_factors,
            recommendations=recommendations
        )
    
    def _generate_recommendations(self,
                                 component_scores: Dict[str, float],
                                 drift_signals: List,
                                 risk_signals: List) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Risk discipline
        if component_scores['risk_discipline'] < 70:
            recommendations.append("Implement stricter position sizing rules")
            recommendations.append("Set and respect daily loss limits")
        
        # Behavioral stability
        if component_scores['behavioral_stability'] < 70:
            recommendations.append("Take a break after consecutive losses")
            recommendations.append("Review trading journal for emotional patterns")
        
        # Exposure control
        if component_scores['exposure_control'] < 70:
            recommendations.append("Reduce leverage immediately")
            recommendations.append("Diversify across uncorrelated assets")
        
        # Performance consistency
        if component_scores['performance_consistency'] < 70:
            recommendations.append("Focus on high probability setups")
            recommendations.append("Reduce trade frequency to improve selectivity")
        
        return recommendations


if __name__ == "__main__":
    # Example usage
    print("Trader Health Scorer")
    print("=" * 60)
    
    # Create sample data
    np.random.seed(42)
    
    trades = []
    equity = 100000
    
    for i in range(50):
        # Simulate deteriorating trader behavior
        if i < 30:
            # Good period
            pnl = np.random.normal(200, 400)
            size = np.random.normal(100, 10)
        else:
            # Bad period - larger losses, revenge trading
            pnl = np.random.normal(-300, 800)
            size = np.random.normal(200, 50)
        
        equity += pnl
        
        trade = {
            'trade_id': f'T{i+1:04d}',
            'trader_id': 'TR001',
            'timestamp': pd.Timestamp('2026-01-01') + pd.Timedelta(days=i),
            'symbol': f'STOCK{i%3}',
            'quantity': size,
            'price': 100,
            'entry_price': 100,
            'pnl': pnl,
            'account_equity': equity
        }
        trades.append(trade)
    
    df = pd.DataFrame(trades)
    
    # Compute health score
    scorer = TraderHealthScorer()
    report = scorer.compute_health_score(df, 'TR001')
    
    print(f"\nTrader: {report.trader_id}")
    print(f"Health Score: {report.health_score:.1f}/100")
    print(f"Status: {report.status.value.upper()}")
    
    print(f"\nComponent Scores:")
    for component, score in report.component_scores.items():
        print(f"  {component.replace('_', ' ').title()}: {score:.1f}")
    
    if report.risk_factors:
        print(f"\nRisk Factors:")
        for factor in report.risk_factors:
            print(f"  - {factor}")
    
    if report.recommendations:
        print(f"\nRecommendations:")
        for rec in report.recommendations:
            print(f"  - {rec}")
