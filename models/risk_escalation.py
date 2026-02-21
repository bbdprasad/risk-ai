"""
Risk Escalation Monitor Module
Detects structural risk build-up before it becomes catastrophic.

Key Focus:
- Loss acceleration
- Correlation exposure
- Leverage creep
- Drawdown patterns
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum


class RiskLevel(Enum):
    """Risk escalation levels."""
    SAFE = "safe"
    ELEVATED = "elevated"
    DANGEROUS = "dangerous"
    CRITICAL = "critical"


@dataclass
class RiskSignal:
    """Container for risk escalation signal."""
    category: str
    metric: str
    current_value: float
    threshold: float
    risk_level: RiskLevel
    message: str


class RiskEscalationMonitor:
    """
    Monitors structural risk build-up indicators.
    
    Detects:
    - Accelerating losses
    - Correlation concentration
    - Leverage increases
    - Drawdown deterioration
    """
    
    def __init__(self):
        """Initialize risk escalation monitor."""
        self.signals = []
        self.thresholds = {
            'drawdown_warning': 0.10,   # 10% drawdown
            'drawdown_critical': 0.20,   # 20% drawdown
            'loss_acceleration': 1.5,    # 1.5x acceleration
            'leverage_warning': 3.0,     # 3x leverage
            'leverage_critical': 5.0,    # 5x leverage
            'correlation_high': 0.7      # 70% correlation
        }
    
    def calculate_drawdown(self, equity_curve: pd.Series) -> Tuple[float, int]:
        """
        Calculate maximum drawdown and duration.
        
        Args:
            equity_curve: Series of account equity values
            
        Returns:
            Tuple of (max_drawdown, days_in_drawdown)
        """
        # Calculate running maximum
        running_max = equity_curve.expanding().max()
        
        # Calculate drawdown at each point
        drawdown = (equity_curve - running_max) / running_max
        
        # Maximum drawdown (most negative)
        max_drawdown = drawdown.min()
        
        # Days in current drawdown
        current_drawdown_days = 0
        if drawdown.iloc[-1] < -0.01:  # Currently in drawdown
            # Count consecutive negative days
            for dd in reversed(drawdown.values):
                if dd < -0.01:
                    current_drawdown_days += 1
                else:
                    break
        
        return abs(max_drawdown), current_drawdown_days
    
    def detect_loss_acceleration(self,
                                trades_df: pd.DataFrame,
                                trader_id: str) -> List[RiskSignal]:
        """
        Detect if losses are accelerating over time.
        
        Args:
            trades_df: DataFrame with trade data
            trader_id: Trader identifier
            
        Returns:
            List of risk signals
        """
        signals = []
        
        trader_trades = trades_df[trades_df['trader_id'] == trader_id].copy()
        trader_trades = trader_trades.sort_values('timestamp')
        
        if len(trader_trades) < 20:
            return signals
        
        # Split into recent and historical periods
        recent = trader_trades.tail(10)
        historical = trader_trades.iloc[-30:-10] if len(trader_trades) >= 30 else trader_trades.iloc[:-10]
        
        # Calculate loss rates
        recent_loss_rate = (recent['pnl'] < 0).sum() / len(recent)
        historical_loss_rate = (historical['pnl'] < 0).sum() / len(historical) if len(historical) > 0 else 0
        
        # Calculate average loss magnitude
        recent_avg_loss = abs(recent[recent['pnl'] < 0]['pnl'].mean()) if (recent['pnl'] < 0).any() else 0
        historical_avg_loss = abs(historical[historical['pnl'] < 0]['pnl'].mean()) if len(historical) > 0 and (historical['pnl'] < 0).any() else 1
        
        # Loss acceleration factor
        if historical_avg_loss > 0:
            acceleration = recent_avg_loss / historical_avg_loss
            
            if acceleration >= self.thresholds['loss_acceleration']:
                risk_level = RiskLevel.DANGEROUS if acceleration >= 2.0 else RiskLevel.ELEVATED
                
                signal = RiskSignal(
                    category="loss_acceleration",
                    metric="avg_loss_magnitude",
                    current_value=recent_avg_loss,
                    threshold=historical_avg_loss * self.thresholds['loss_acceleration'],
                    risk_level=risk_level,
                    message=f"Losses accelerating {acceleration:.1f}x - recent avg loss: ${recent_avg_loss:.2f} vs ${historical_avg_loss:.2f}"
                )
                signals.append(signal)
        
        return signals
    
    def detect_drawdown_risk(self,
                           trades_df: pd.DataFrame,
                           trader_id: str) -> List[RiskSignal]:
        """
        Monitor drawdown levels and duration.
        
        Args:
            trades_df: DataFrame with trade data
            trader_id: Trader identifier
            
        Returns:
            List of risk signals
        """
        signals = []
        
        trader_trades = trades_df[trades_df['trader_id'] == trader_id].copy()
        trader_trades = trader_trades.sort_values('timestamp')
        
        if len(trader_trades) < 10 or 'account_equity' not in trader_trades.columns:
            return signals
        
        # Calculate drawdown
        equity_curve = trader_trades['account_equity']
        max_drawdown, days_in_drawdown = self.calculate_drawdown(equity_curve)
        
        # Assess risk level
        if max_drawdown >= self.thresholds['drawdown_critical']:
            risk_level = RiskLevel.CRITICAL
        elif max_drawdown >= self.thresholds['drawdown_warning']:
            risk_level = RiskLevel.DANGEROUS
        else:
            risk_level = RiskLevel.SAFE
        
        if risk_level != RiskLevel.SAFE:
            signal = RiskSignal(
                category="drawdown",
                metric="max_drawdown",
                current_value=max_drawdown,
                threshold=self.thresholds['drawdown_warning'],
                risk_level=risk_level,
                message=f"Drawdown at {max_drawdown:.1%} for {days_in_drawdown} days"
            )
            signals.append(signal)
        
        return signals
    
    def detect_leverage_creep(self,
                            trades_df: pd.DataFrame,
                            trader_id: str) -> List[RiskSignal]:
        """
        Detect gradual increase in effective leverage.
        
        Args:
            trades_df: DataFrame with trade data
            trader_id: Trader identifier
            
        Returns:
            List of risk signals
        """
        signals = []
        
        trader_trades = trades_df[trades_df['trader_id'] == trader_id].copy()
        trader_trades = trader_trades.sort_values('timestamp')
        
        if len(trader_trades) < 10 or 'account_equity' not in trader_trades.columns:
            return signals
        
        # Calculate effective leverage (position value / equity)
        trader_trades['position_value'] = trader_trades['quantity'] * trader_trades.get('entry_price', trader_trades.get('price', 100))
        trader_trades['leverage'] = trader_trades['position_value'] / trader_trades['account_equity']
        
        # Recent vs historical leverage
        recent_leverage = trader_trades.tail(10)['leverage'].mean()
        historical_leverage = trader_trades.iloc[:-10]['leverage'].mean() if len(trader_trades) > 10 else recent_leverage
        
        # Check for leverage creep
        leverage_increase = recent_leverage / historical_leverage if historical_leverage > 0 else 1.0
        
        # Assess risk
        if recent_leverage >= self.thresholds['leverage_critical']:
            risk_level = RiskLevel.CRITICAL
        elif recent_leverage >= self.thresholds['leverage_warning']:
            risk_level = RiskLevel.DANGEROUS
        elif leverage_increase >= 1.5:  # 50% increase
            risk_level = RiskLevel.ELEVATED
        else:
            risk_level = RiskLevel.SAFE
        
        if risk_level != RiskLevel.SAFE:
            signal = RiskSignal(
                category="leverage",
                metric="effective_leverage",
                current_value=recent_leverage,
                threshold=self.thresholds['leverage_warning'],
                risk_level=risk_level,
                message=f"Leverage at {recent_leverage:.2f}x (increased {leverage_increase:.1%} from {historical_leverage:.2f}x)"
            )
            signals.append(signal)
        
        return signals
    
    def detect_correlation_risk(self,
                               trades_df: pd.DataFrame,
                               trader_id: str) -> List[RiskSignal]:
        """
        Detect concentrated correlated exposure.
        
        Args:
            trades_df: DataFrame with trade data
            trader_id: Trader identifier
            
        Returns:
            List of risk signals
        """
        signals = []
        
        trader_trades = trades_df[trades_df['trader_id'] == trader_id].copy()
        
        if len(trader_trades) < 5:
            return signals
        
        # Get open positions (last trade per symbol)
        if 'symbol' in trader_trades.columns:
            open_positions = trader_trades.groupby('symbol').tail(1)
            
            # Calculate sector concentration
            total_exposure = open_positions['quantity'].sum()
            
            if total_exposure > 0:
                # Calculate concentration (Herfindahl index)
                position_weights = open_positions['quantity'] / total_exposure
                concentration = (position_weights ** 2).sum()
                
                # High concentration = potential correlation risk
                if concentration >= 0.5:  # More than 50% in one position
                    risk_level = RiskLevel.DANGEROUS if concentration >= 0.7 else RiskLevel.ELEVATED
                    
                    signal = RiskSignal(
                        category="concentration",
                        metric="position_concentration",
                        current_value=concentration,
                        threshold=0.5,
                        risk_level=risk_level,
                        message=f"High position concentration: {concentration:.1%} (diversify exposure)"
                    )
                    signals.append(signal)
        
        return signals
    
    def detect_volatility_mismatch(self,
                                  trades_df: pd.DataFrame,
                                  trader_id: str) -> List[RiskSignal]:
        """
        Detect if trader is not adjusting to volatility changes.
        
        Args:
            trades_df: DataFrame with trade data
            trader_id: Trader identifier
            
        Returns:
            List of risk signals
        """
        signals = []
        
        trader_trades = trades_df[trades_df['trader_id'] == trader_id].copy()
        trader_trades = trader_trades.sort_values('timestamp')
        
        if len(trader_trades) < 30:
            return signals
        
        # Calculate P&L volatility over time
        recent_vol = trader_trades.tail(10)['pnl'].std()
        historical_vol = trader_trades.iloc[:-10]['pnl'].std()
        
        # Calculate position size over time
        recent_size = trader_trades.tail(10)['quantity'].mean()
        historical_size = trader_trades.iloc[:-10]['quantity'].mean()
        
        # Check for volatility regime change without size adjustment
        vol_increase = recent_vol / historical_vol if historical_vol > 0 else 1.0
        size_change = recent_size / historical_size if historical_size > 0 else 1.0
        
        # If volatility increased significantly but size didn't decrease
        if vol_increase >= 1.5 and size_change >= 0.9:
            risk_level = RiskLevel.DANGEROUS if vol_increase >= 2.0 else RiskLevel.ELEVATED
            
            signal = RiskSignal(
                category="volatility_mismatch",
                metric="risk_adjustment",
                current_value=vol_increase,
                threshold=1.5,
                risk_level=risk_level,
                message=f"Market volatility increased {vol_increase:.1f}x but position size unchanged - adjust risk"
            )
            signals.append(signal)
        
        return signals
    
    def monitor_all_risks(self,
                         trades_df: pd.DataFrame,
                         trader_id: str) -> List[RiskSignal]:
        """
        Run all risk escalation monitors.
        
        Args:
            trades_df: DataFrame with trade data
            trader_id: Trader identifier
            
        Returns:
            Combined list of all risk signals
        """
        all_signals = []
        
        # Loss acceleration
        all_signals.extend(
            self.detect_loss_acceleration(trades_df, trader_id)
        )
        
        # Drawdown risk
        all_signals.extend(
            self.detect_drawdown_risk(trades_df, trader_id)
        )
        
        # Leverage creep
        all_signals.extend(
            self.detect_leverage_creep(trades_df, trader_id)
        )
        
        # Correlation risk
        all_signals.extend(
            self.detect_correlation_risk(trades_df, trader_id)
        )
        
        # Volatility mismatch
        all_signals.extend(
            self.detect_volatility_mismatch(trades_df, trader_id)
        )
        
        self.signals = all_signals
        return all_signals
    
    def get_risk_summary(self) -> Dict:
        """
        Get summary of risk escalation signals.
        
        Returns:
            Dictionary with risk statistics
        """
        if not self.signals:
            return {
                'total_signals': 0,
                'critical': 0,
                'dangerous': 0,
                'elevated': 0,
                'overall_risk': 'safe'
            }
        
        critical_count = sum(1 for s in self.signals if s.risk_level == RiskLevel.CRITICAL)
        dangerous_count = sum(1 for s in self.signals if s.risk_level == RiskLevel.DANGEROUS)
        elevated_count = sum(1 for s in self.signals if s.risk_level == RiskLevel.ELEVATED)
        
        # Overall risk assessment
        if critical_count > 0:
            overall = 'critical'
        elif dangerous_count >= 2:
            overall = 'critical'
        elif dangerous_count >= 1:
            overall = 'dangerous'
        elif elevated_count >= 2:
            overall = 'elevated'
        else:
            overall = 'safe'
        
        return {
            'total_signals': len(self.signals),
            'critical': critical_count,
            'dangerous': dangerous_count,
            'elevated': elevated_count,
            'overall_risk': overall
        }


if __name__ == "__main__":
    # Example usage
    print("Risk Escalation Monitor")
    print("=" * 60)
    
    # Create sample data with escalating risk
    np.random.seed(42)
    
    trades = []
    equity = 100000
    
    # Normal period
    for i in range(40):
        pnl = np.random.normal(200, 500)
        equity += pnl
        
        trade = {
            'trade_id': f'T{i+1:04d}',
            'trader_id': 'TR001',
            'timestamp': pd.Timestamp('2026-01-01') + pd.Timedelta(days=i),
            'symbol': f'STOCK{i%5}',
            'quantity': 100,
            'price': 100,
            'entry_price': 100,
            'pnl': pnl,
            'account_equity': equity
        }
        trades.append(trade)
    
    # Risk escalation period - larger losses, higher leverage
    for i in range(40, 60):
        pnl = np.random.normal(-500, 800)  # Larger losses
        equity += pnl
        
        trade = {
            'trade_id': f'T{i+1:04d}',
            'trader_id': 'TR001',
            'timestamp': pd.Timestamp('2026-01-01') + pd.Timedelta(days=i),
            'symbol': f'STOCK{i%3}',  # More concentrated
            'quantity': 300,  # 3x larger positions
            'price': 100,
            'entry_price': 100,
            'pnl': pnl,
            'account_equity': equity
        }
        trades.append(trade)
    
    df = pd.DataFrame(trades)
    
    # Monitor risks
    monitor = RiskEscalationMonitor()
    signals = monitor.monitor_all_risks(df, 'TR001')
    
    print(f"\nDetected {len(signals)} risk signals:")
    for signal in signals:
        print(f"\n[{signal.risk_level.value.upper()}] {signal.category}")
        print(f"  {signal.message}")
    
    summary = monitor.get_risk_summary()
    print(f"\nRisk Summary:")
    print(f"  Overall Risk: {summary['overall_risk'].upper()}")
    print(f"  Critical: {summary['critical']}")
    print(f"  Dangerous: {summary['dangerous']}")
    print(f"  Elevated: {summary['elevated']}")
