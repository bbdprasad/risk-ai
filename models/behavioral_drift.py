"""
Behavioral Drift Detection Module
Detects when a trader deviates from their historical patterns.

Key Focus:
- Position size changes
- Trade frequency shifts
- Holding time deviation
- Post-loss/win behavior changes
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum


class DriftSeverity(Enum):
    """Severity levels for behavioral drift."""
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class DriftSignal:
    """Container for drift detection signal."""
    metric: str
    current_value: float
    baseline_value: float
    z_score: float
    severity: DriftSeverity
    message: str


class BehavioralDriftDetector:
    """
    Detects behavioral drift from trader's historical patterns.
    
    Methodology:
    - Compute rolling baselines (5d, 20d, 60d)
    - Calculate Z-scores for key metrics
    - Detect change points
    - Flag significant deviations
    """
    
    def __init__(self, 
                 z_warning: float = 2.0,
                 z_critical: float = 3.0):
        """
        Initialize drift detector.
        
        Args:
            z_warning: Z-score threshold for warning
            z_critical: Z-score threshold for critical alert
        """
        self.z_warning = z_warning
        self.z_critical = z_critical
        self.signals = []
        
    def compute_rolling_baseline(self,
                                 df: pd.DataFrame,
                                 metric: str,
                                 windows: List[int] = [5, 20, 60]) -> pd.DataFrame:
        """
        Compute rolling statistics for a metric.
        
        Args:
            df: DataFrame with trader data (sorted by timestamp)
            metric: Column name to analyze
            windows: List of window sizes
            
        Returns:
            DataFrame with rolling mean and std
        """
        result = df.copy()
        
        for window in windows:
            result[f'{metric}_mean_{window}d'] = (
                result[metric].rolling(window=window, min_periods=1).mean()
            )
            result[f'{metric}_std_{window}d'] = (
                result[metric].rolling(window=window, min_periods=1).std()
            )
        
        return result
    
    def calculate_z_score(self,
                         current: float,
                         baseline_mean: float,
                         baseline_std: float) -> float:
        """
        Calculate Z-score for deviation detection.
        
        Args:
            current: Current metric value
            baseline_mean: Historical mean
            baseline_std: Historical standard deviation
            
        Returns:
            Z-score
        """
        if baseline_std == 0 or pd.isna(baseline_std):
            return 0.0
        
        return (current - baseline_mean) / baseline_std
    
    def assess_severity(self, z_score: float) -> DriftSeverity:
        """
        Assess severity based on Z-score.
        
        Args:
            z_score: Deviation Z-score
            
        Returns:
            Severity level
        """
        abs_z = abs(z_score)
        
        if abs_z >= self.z_critical:
            return DriftSeverity.CRITICAL
        elif abs_z >= self.z_warning:
            return DriftSeverity.WARNING
        else:
            return DriftSeverity.NORMAL
    
    def detect_position_size_drift(self,
                                   trades_df: pd.DataFrame,
                                   trader_id: str) -> List[DriftSignal]:
        """
        Detect position size deviation from normal.
        
        Args:
            trades_df: DataFrame with trade data
            trader_id: Trader identifier
            
        Returns:
            List of drift signals
        """
        signals = []
        
        # Filter to trader and sort by time
        trader_trades = trades_df[trades_df['trader_id'] == trader_id].copy()
        trader_trades = trader_trades.sort_values('timestamp')
        
        if len(trader_trades) < 10:
            return signals  # Not enough data
        
        # Compute rolling baselines
        trader_trades = self.compute_rolling_baseline(
            trader_trades, 'quantity', windows=[5, 20, 60]
        )
        
        # Get recent trades (last 5)
        recent = trader_trades.tail(5)
        current_size = recent['quantity'].mean()
        
        # Compare to 60-day baseline
        baseline_mean = trader_trades['quantity_mean_60d'].iloc[-1]
        baseline_std = trader_trades['quantity_std_60d'].iloc[-1]
        
        if pd.notna(baseline_mean) and pd.notna(baseline_std):
            z_score = self.calculate_z_score(current_size, baseline_mean, baseline_std)
            severity = self.assess_severity(z_score)
            
            if severity != DriftSeverity.NORMAL:
                signal = DriftSignal(
                    metric="position_size",
                    current_value=current_size,
                    baseline_value=baseline_mean,
                    z_score=z_score,
                    severity=severity,
                    message=f"Position size {current_size:.0f} vs baseline {baseline_mean:.0f} (Z={z_score:.2f})"
                )
                signals.append(signal)
        
        return signals
    
    def detect_frequency_drift(self,
                              trades_df: pd.DataFrame,
                              trader_id: str) -> List[DriftSignal]:
        """
        Detect trade frequency changes.
        
        Args:
            trades_df: DataFrame with trade data
            trader_id: Trader identifier
            
        Returns:
            List of drift signals
        """
        signals = []
        
        trader_trades = trades_df[trades_df['trader_id'] == trader_id].copy()
        trader_trades = trader_trades.sort_values('timestamp')
        
        if len(trader_trades) < 20:
            return signals
        
        # Calculate daily trade counts
        trader_trades['date'] = pd.to_datetime(trader_trades['timestamp']).dt.date
        daily_counts = trader_trades.groupby('date').size().reset_index(name='trade_count')
        
        # Recent frequency (last 5 days)
        recent_freq = daily_counts.tail(5)['trade_count'].mean()
        
        # Baseline frequency (20-60 days)
        baseline_freq = daily_counts['trade_count'].mean()
        baseline_std = daily_counts['trade_count'].std()
        
        if baseline_std > 0:
            z_score = self.calculate_z_score(recent_freq, baseline_freq, baseline_std)
            severity = self.assess_severity(z_score)
            
            if severity != DriftSeverity.NORMAL:
                signal = DriftSignal(
                    metric="trade_frequency",
                    current_value=recent_freq,
                    baseline_value=baseline_freq,
                    z_score=z_score,
                    severity=severity,
                    message=f"Trade frequency {recent_freq:.1f}/day vs baseline {baseline_freq:.1f}/day (Z={z_score:.2f})"
                )
                signals.append(signal)
        
        return signals
    
    def detect_revenge_trading(self,
                              trades_df: pd.DataFrame,
                              trader_id: str) -> List[DriftSignal]:
        """
        Detect position size increase after losses (revenge trading).
        
        Args:
            trades_df: DataFrame with trade data
            trader_id: Trader identifier
            
        Returns:
            List of drift signals
        """
        signals = []
        
        trader_trades = trades_df[trades_df['trader_id'] == trader_id].copy()
        trader_trades = trader_trades.sort_values('timestamp')
        
        if len(trader_trades) < 10:
            return signals
        
        # Compute size after wins vs losses
        trader_trades['prev_pnl'] = trader_trades['pnl'].shift(1)
        trader_trades['is_after_loss'] = trader_trades['prev_pnl'] < 0
        trader_trades['is_after_win'] = trader_trades['prev_pnl'] > 0
        
        # Skip first trade (no previous)
        trader_trades = trader_trades.iloc[1:]
        
        if len(trader_trades[trader_trades['is_after_loss']]) > 0:
            avg_size_after_loss = trader_trades[trader_trades['is_after_loss']]['quantity'].mean()
            avg_normal_size = trader_trades['quantity'].mean()
            
            # Check if size increases significantly after losses
            increase_ratio = avg_size_after_loss / avg_normal_size if avg_normal_size > 0 else 1.0
            
            # Revenge trading flag: >30% size increase after losses
            if increase_ratio > 1.3:
                signal = DriftSignal(
                    metric="revenge_trading",
                    current_value=avg_size_after_loss,
                    baseline_value=avg_normal_size,
                    z_score=(increase_ratio - 1) * 10,  # Convert to pseudo Z-score
                    severity=DriftSeverity.CRITICAL if increase_ratio > 1.5 else DriftSeverity.WARNING,
                    message=f"Position size {increase_ratio:.1%} larger after losses - revenge trading signal"
                )
                signals.append(signal)
        
        return signals
    
    def detect_overconfidence(self,
                            trades_df: pd.DataFrame,
                            trader_id: str) -> List[DriftSignal]:
        """
        Detect position size increase after wins (overconfidence).
        
        Args:
            trades_df: DataFrame with trade data
            trader_id: Trader identifier
            
        Returns:
            List of drift signals
        """
        signals = []
        
        trader_trades = trades_df[trades_df['trader_id'] == trader_id].copy()
        trader_trades = trader_trades.sort_values('timestamp')
        
        if len(trader_trades) < 10:
            return signals
        
        # Detect consecutive wins
        trader_trades['prev_pnl'] = trader_trades['pnl'].shift(1)
        trader_trades['prev_prev_pnl'] = trader_trades['pnl'].shift(2)
        
        # After 2+ consecutive wins
        consecutive_wins = (
            (trader_trades['prev_pnl'] > 0) & 
            (trader_trades['prev_prev_pnl'] > 0)
        )
        
        if consecutive_wins.sum() > 0:
            avg_size_after_wins = trader_trades[consecutive_wins]['quantity'].mean()
            avg_normal_size = trader_trades['quantity'].mean()
            
            increase_ratio = avg_size_after_wins / avg_normal_size if avg_normal_size > 0 else 1.0
            
            # Overconfidence flag: >40% size increase after win streaks
            if increase_ratio > 1.4:
                signal = DriftSignal(
                    metric="overconfidence",
                    current_value=avg_size_after_wins,
                    baseline_value=avg_normal_size,
                    z_score=(increase_ratio - 1) * 10,
                    severity=DriftSeverity.WARNING if increase_ratio < 1.6 else DriftSeverity.CRITICAL,
                    message=f"Position size {increase_ratio:.1%} larger after win streaks - overconfidence signal"
                )
                signals.append(signal)
        
        return signals
    
    def detect_all_drift_signals(self,
                                trades_df: pd.DataFrame,
                                trader_id: str) -> List[DriftSignal]:
        """
        Run all drift detection methods.
        
        Args:
            trades_df: DataFrame with trade data
            trader_id: Trader identifier
            
        Returns:
            Combined list of all drift signals
        """
        all_signals = []
        
        # Position size drift
        all_signals.extend(
            self.detect_position_size_drift(trades_df, trader_id)
        )
        
        # Frequency drift
        all_signals.extend(
            self.detect_frequency_drift(trades_df, trader_id)
        )
        
        # Revenge trading
        all_signals.extend(
            self.detect_revenge_trading(trades_df, trader_id)
        )
        
        # Overconfidence
        all_signals.extend(
            self.detect_overconfidence(trades_df, trader_id)
        )
        
        self.signals = all_signals
        return all_signals
    
    def get_summary(self) -> Dict:
        """
        Get summary of detected drift signals.
        
        Returns:
            Dictionary with signal counts by severity
        """
        if not self.signals:
            return {
                'total_signals': 0,
                'critical': 0,
                'warning': 0,
                'normal': 0
            }
        
        severity_counts = {
            'critical': sum(1 for s in self.signals if s.severity == DriftSeverity.CRITICAL),
            'warning': sum(1 for s in self.signals if s.severity == DriftSeverity.WARNING),
            'normal': sum(1 for s in self.signals if s.severity == DriftSeverity.NORMAL)
        }
        
        return {
            'total_signals': len(self.signals),
            **severity_counts
        }


if __name__ == "__main__":
    # Example usage with sample data
    print("Behavioral Drift Detection Module")
    print("=" * 60)
    
    # Create sample trader data
    np.random.seed(42)
    
    # Normal trading for 50 days
    normal_trades = []
    for i in range(50):
        trade = {
            'trade_id': f'T{i+1:04d}',
            'trader_id': 'TR001',
            'timestamp': pd.Timestamp('2026-01-01') + pd.Timedelta(days=i),
            'quantity': np.random.normal(100, 10),  # Stable sizing
            'pnl': np.random.normal(100, 500)
        }
        normal_trades.append(trade)
    
    # Add recent drift - increasing position sizes
    for i in range(50, 60):
        trade = {
            'trade_id': f'T{i+1:04d}',
            'trader_id': 'TR001',
            'timestamp': pd.Timestamp('2026-01-01') + pd.Timedelta(days=i),
            'quantity': np.random.normal(200, 20),  # 2x larger!
            'pnl': np.random.normal(-200, 600)
        }
        normal_trades.append(trade)
    
    df = pd.DataFrame(normal_trades)
    
    # Detect drift
    detector = BehavioralDriftDetector()
    signals = detector.detect_all_drift_signals(df, 'TR001')
    
    print(f"\nDetected {len(signals)} drift signals:")
    for signal in signals:
        print(f"\n[{signal.severity.value.upper()}] {signal.metric}")
        print(f"  {signal.message}")
    
    summary = detector.get_summary()
    print(f"\nSummary:")
    print(f"  Total signals: {summary['total_signals']}")
    print(f"  Critical: {summary['critical']}")
    print(f"  Warning: {summary['warning']}")
