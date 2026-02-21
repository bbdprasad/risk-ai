"""
Simulated Trader Behavior Generator
Creates realistic trader profiles with specific behavioral patterns for testing.

Trader Types:
1. Disciplined Trader - Consistent, follows rules
2. Revenge Trader - Increases size after losses
3. Overconfident Trader - Increases size after wins
4. Risk Creep Trader - Gradually increases leverage
5. Erratic Trader - Highly variable behavior
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict
from enum import Enum


class TraderBehaviorType(Enum):
    """Types of trader behaviors."""
    DISCIPLINED = "disciplined"
    REVENGE_TRADER = "revenge_trader"
    OVERCONFIDENT = "overconfident"
    RISK_CREEP = "risk_creep"
    ERRATIC = "erratic"


class BehavioralTraderSimulator:
    """
    Generates realistic trader data with specific behavioral patterns.
    
    Purpose: Validate that the risk detection system can identify
    problematic trading behaviors.
    """
    
    def __init__(self, seed: int = 42):
        """Initialize simulator with random seed."""
        np.random.seed(seed)
        self.trade_counter = 0
    
    def generate_disciplined_trader(self,
                                   trader_id: str,
                                   start_date: datetime,
                                   n_days: int = 60,
                                   initial_equity: float = 100000) -> pd.DataFrame:
        """
        Generate disciplined trader behavior.
        
        Characteristics:
        - Consistent position sizing
        - Respects stop losses
        - Doesn't chase losses
        - Stable win rate ~55%
        - Low variance in behavior
        
        This is the "control" - healthy trader baseline.
        """
        trades = []
        equity = initial_equity
        
        # Consistent parameters
        base_size = 100
        size_variance = 10  # Low variance
        win_rate = 0.55
        
        for day in range(n_days):
            current_date = start_date + timedelta(days=day)
            if current_date.weekday() >= 5:  # Skip weekends
                continue
            
            # 2-4 trades per day
            n_trades = np.random.randint(2, 5)
            
            for _ in range(n_trades):
                self.trade_counter += 1
                
                # Consistent sizing
                quantity = np.random.normal(base_size, size_variance)
                quantity = max(50, quantity)  # Min size
                
                # Consistent P&L distribution
                is_win = np.random.random() < win_rate
                if is_win:
                    pnl = np.random.normal(150, 50)
                else:
                    pnl = np.random.normal(-100, 30)  # Controlled losses
                
                equity += pnl
                
                trade = {
                    'trade_id': f'T{self.trade_counter:06d}',
                    'trader_id': trader_id,
                    'timestamp': current_date + timedelta(hours=np.random.randint(9, 16)),
                    'symbol': f'STOCK{np.random.randint(1, 6)}',
                    'side': 'long' if np.random.random() > 0.5 else 'short',
                    'quantity': quantity,
                    'price': 100,
                    'entry_price': 100,
                    'exit_price': 100 + pnl/quantity,
                    'pnl': pnl,
                    'account_equity': equity,
                    'behavior_type': TraderBehaviorType.DISCIPLINED.value
                }
                trades.append(trade)
        
        return pd.DataFrame(trades)
    
    def generate_revenge_trader(self,
                               trader_id: str,
                               start_date: datetime,
                               n_days: int = 60,
                               initial_equity: float = 100000) -> pd.DataFrame:
        """
        Generate revenge trader behavior.
        
        Characteristics:
        - Starts normal (first 30 days)
        - After losses, increases position size significantly
        - Chases losses
        - Eventually blows up
        
        CRITICAL behavior to detect.
        """
        trades = []
        equity = initial_equity
        base_size = 100
        
        for day in range(n_days):
            current_date = start_date + timedelta(days=day)
            if current_date.weekday() >= 5:
                continue
            
            n_trades = np.random.randint(2, 5)
            
            for _ in range(n_trades):
                self.trade_counter += 1
                
                # Check if previous trade was a loss
                if len(trades) > 0:
                    prev_pnl = trades[-1]['pnl']
                    
                    # Revenge trading kicks in after day 20
                    if day > 20 and prev_pnl < 0:
                        # Increase size after loss (REVENGE SIGNAL)
                        size_multiplier = np.random.uniform(1.5, 2.5)
                        quantity = base_size * size_multiplier
                    else:
                        quantity = np.random.normal(base_size, 15)
                else:
                    quantity = np.random.normal(base_size, 15)
                
                quantity = max(50, quantity)
                
                # Win rate
                is_win = np.random.random() < 0.48  # Slightly negative
                
                if is_win:
                    pnl = np.random.normal(120, 40)
                else:
                    # Larger losses due to larger sizes
                    pnl = np.random.normal(-150, 60)
                
                equity += pnl
                
                trade = {
                    'trade_id': f'T{self.trade_counter:06d}',
                    'trader_id': trader_id,
                    'timestamp': current_date + timedelta(hours=np.random.randint(9, 16)),
                    'symbol': f'STOCK{np.random.randint(1, 4)}',
                    'side': 'long' if np.random.random() > 0.5 else 'short',
                    'quantity': quantity,
                    'price': 100,
                    'entry_price': 100,
                    'exit_price': 100 + pnl/quantity,
                    'pnl': pnl,
                    'account_equity': equity,
                    'behavior_type': TraderBehaviorType.REVENGE_TRADER.value
                }
                trades.append(trade)
        
        return pd.DataFrame(trades)
    
    def generate_overconfident_trader(self,
                                     trader_id: str,
                                     start_date: datetime,
                                     n_days: int = 60,
                                     initial_equity: float = 100000) -> pd.DataFrame:
        """
        Generate overconfident trader behavior.
        
        Characteristics:
        - Increases size after winning streaks
        - Gets aggressive after 2+ wins
        - Eventually takes too much risk
        """
        trades = []
        equity = initial_equity
        base_size = 100
        consecutive_wins = 0
        
        for day in range(n_days):
            current_date = start_date + timedelta(days=day)
            if current_date.weekday() >= 5:
                continue
            
            n_trades = np.random.randint(2, 5)
            
            for _ in range(n_trades):
                self.trade_counter += 1
                
                # Overconfidence after win streaks (after day 15)
                if day > 15 and consecutive_wins >= 2:
                    # Increase size significantly
                    quantity = base_size * np.random.uniform(1.8, 3.0)
                else:
                    quantity = np.random.normal(base_size, 15)
                
                quantity = max(50, quantity)
                
                # Win rate
                is_win = np.random.random() < 0.52
                
                if is_win:
                    pnl = np.random.normal(140, 50)
                    consecutive_wins += 1
                else:
                    # Large loss when overconfident
                    if consecutive_wins >= 2:
                        pnl = np.random.normal(-400, 150)  # BIG loss
                    else:
                        pnl = np.random.normal(-120, 40)
                    consecutive_wins = 0
                
                equity += pnl
                
                trade = {
                    'trade_id': f'T{self.trade_counter:06d}',
                    'trader_id': trader_id,
                    'timestamp': current_date + timedelta(hours=np.random.randint(9, 16)),
                    'symbol': f'STOCK{np.random.randint(1, 5)}',
                    'side': 'long' if np.random.random() > 0.5 else 'short',
                    'quantity': quantity,
                    'price': 100,
                    'entry_price': 100,
                    'exit_price': 100 + pnl/quantity,
                    'pnl': pnl,
                    'account_equity': equity,
                    'behavior_type': TraderBehaviorType.OVERCONFIDENT.value
                }
                trades.append(trade)
        
        return pd.DataFrame(trades)
    
    def generate_risk_creep_trader(self,
                                   trader_id: str,
                                   start_date: datetime,
                                   n_days: int = 60,
                                   initial_equity: float = 100000) -> pd.DataFrame:
        """
        Generate risk creep trader behavior.
        
        Characteristics:
        - Gradually increases position sizes over time
        - Slow, insidious leverage increase
        - May not notice until too late
        """
        trades = []
        equity = initial_equity
        
        for day in range(n_days):
            current_date = start_date + timedelta(days=day)
            if current_date.weekday() >= 5:
                continue
            
            n_trades = np.random.randint(2, 5)
            
            # Gradual size increase: 2% per day
            size_multiplier = 1 + (day * 0.02)
            base_size = 100 * size_multiplier
            
            for _ in range(n_trades):
                self.trade_counter += 1
                
                quantity = np.random.normal(base_size, base_size * 0.15)
                quantity = max(50, quantity)
                
                # Win rate
                is_win = np.random.random() < 0.51
                
                if is_win:
                    pnl = np.random.normal(150, 50)
                else:
                    # Losses scale with size
                    pnl = np.random.normal(-130, 50)
                
                equity += pnl
                
                trade = {
                    'trade_id': f'T{self.trade_counter:06d}',
                    'trader_id': trader_id,
                    'timestamp': current_date + timedelta(hours=np.random.randint(9, 16)),
                    'symbol': f'STOCK{np.random.randint(1, 4)}',
                    'side': 'long' if np.random.random() > 0.5 else 'short',
                    'quantity': quantity,
                    'price': 100,
                    'entry_price': 100,
                    'exit_price': 100 + pnl/quantity,
                    'pnl': pnl,
                    'account_equity': equity,
                    'behavior_type': TraderBehaviorType.RISK_CREEP.value
                }
                trades.append(trade)
        
        return pd.DataFrame(trades)
    
    def generate_erratic_trader(self,
                               trader_id: str,
                               start_date: datetime,
                               n_days: int = 60,
                               initial_equity: float = 100000) -> pd.DataFrame:
        """
        Generate erratic trader behavior.
        
        Characteristics:
        - Highly variable position sizes
        - Inconsistent frequency
        - No clear pattern
        - High behavioral volatility
        """
        trades = []
        equity = initial_equity
        
        for day in range(n_days):
            current_date = start_date + timedelta(days=day)
            if current_date.weekday() >= 5:
                continue
            
            # Highly variable trade count
            n_trades = np.random.randint(1, 12)
            
            for _ in range(n_trades):
                self.trade_counter += 1
                
                # Highly variable sizing
                quantity = np.random.uniform(50, 300)
                
                # Random win rate
                is_win = np.random.random() < np.random.uniform(0.4, 0.6)
                
                if is_win:
                    pnl = np.random.normal(150, 100)
                else:
                    pnl = np.random.normal(-150, 100)
                
                equity += pnl
                
                trade = {
                    'trade_id': f'T{self.trade_counter:06d}',
                    'trader_id': trader_id,
                    'timestamp': current_date + timedelta(hours=np.random.randint(9, 16)),
                    'symbol': f'STOCK{np.random.randint(1, 8)}',
                    'side': 'long' if np.random.random() > 0.5 else 'short',
                    'quantity': quantity,
                    'price': 100,
                    'entry_price': 100,
                    'exit_price': 100 + pnl/quantity,
                    'pnl': pnl,
                    'account_equity': equity,
                    'behavior_type': TraderBehaviorType.ERRATIC.value
                }
                trades.append(trade)
        
        return pd.DataFrame(trades)
    
    def generate_mixed_population(self,
                                 n_traders: int = 20,
                                 n_days: int = 60) -> pd.DataFrame:
        """
        Generate a mixed population of traders with different behaviors.
        
        Distribution:
        - 50% Disciplined (healthy)
        - 20% Revenge traders (critical)
        - 15% Overconfident (warning)
        - 10% Risk creep (warning)
        - 5% Erratic (warning)
        """
        all_trades = []
        start_date = datetime(2026, 1, 1)
        
        behavior_distribution = [
            (TraderBehaviorType.DISCIPLINED, 0.50),
            (TraderBehaviorType.REVENGE_TRADER, 0.20),
            (TraderBehaviorType.OVERCONFIDENT, 0.15),
            (TraderBehaviorType.RISK_CREEP, 0.10),
            (TraderBehaviorType.ERRATIC, 0.05)
        ]
        
        for i in range(n_traders):
            trader_id = f'SIM{i+1:03d}'
            
            # Assign behavior type based on distribution
            rand = np.random.random()
            cumulative = 0
            assigned_behavior = TraderBehaviorType.DISCIPLINED
            
            for behavior, prob in behavior_distribution:
                cumulative += prob
                if rand <= cumulative:
                    assigned_behavior = behavior
                    break
            
            # Generate trades based on behavior type
            if assigned_behavior == TraderBehaviorType.DISCIPLINED:
                trades_df = self.generate_disciplined_trader(trader_id, start_date, n_days)
            elif assigned_behavior == TraderBehaviorType.REVENGE_TRADER:
                trades_df = self.generate_revenge_trader(trader_id, start_date, n_days)
            elif assigned_behavior == TraderBehaviorType.OVERCONFIDENT:
                trades_df = self.generate_overconfident_trader(trader_id, start_date, n_days)
            elif assigned_behavior == TraderBehaviorType.RISK_CREEP:
                trades_df = self.generate_risk_creep_trader(trader_id, start_date, n_days)
            else:  # ERRATIC
                trades_df = self.generate_erratic_trader(trader_id, start_date, n_days)
            
            all_trades.append(trades_df)
        
        return pd.concat(all_trades, ignore_index=True)


if __name__ == "__main__":
    print("Behavioral Trader Simulator")
    print("=" * 60)
    
    simulator = BehavioralTraderSimulator(seed=42)
    
    # Generate mixed population
    print("\nGenerating mixed trader population...")
    all_trades = simulator.generate_mixed_population(n_traders=20, n_days=60)
    
    print(f"\nGenerated {len(all_trades)} trades for 20 simulated traders")
    print(f"\nBehavior Distribution:")
    print(all_trades['behavior_type'].value_counts())
    
    # Save for testing
    all_trades.to_csv('data/simulated_traders.csv', index=False)
    print("\nSaved to: data/simulated_traders.csv")
    
    # Show sample
    print("\nSample trades:")
    print(all_trades[['trader_id', 'quantity', 'pnl', 'account_equity', 'behavior_type']].head(10))
