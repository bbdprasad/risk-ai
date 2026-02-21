"""
Fake Trader Generation Module for Risk AI
Generates synthetic trader data for testing and simulation purposes.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict
import random


class FakeTraderGenerator:
    """
    Generate synthetic trader and trade data for testing risk models.
    """
    
    def __init__(self, seed: int = 42):
        """
        Initialize generator with random seed for reproducibility.
        
        Args:
            seed: Random seed
        """
        np.random.seed(seed)
        random.seed(seed)
        
        self.assets = [
            'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META', 'TSLA', 'NVDA',
            'JPM', 'BAC', 'GS', 'MS', 'C', 'WFC',
            'V', 'MA', 'PYPL', 'SQ',
            'DIS', 'NFLX', 'T', 'VZ',
            'INTC', 'AMD', 'QCOM', 'ORCL', 'CRM'
        ]
        
        self.markets = ['NASDAQ', 'NYSE', 'AMEX']
        self.regions = ['NA', 'EU', 'ASIA', 'LATAM']
        self.trade_types = ['BUY', 'SELL']
        
    def generate_trader_profiles(self, n_traders: int) -> pd.DataFrame:
        """
        Generate trader profiles with characteristics.
        
        Args:
            n_traders: Number of traders to generate
            
        Returns:
            DataFrame with trader profiles
        """
        traders = []
        
        for i in range(n_traders):
            trader_id = f"TR{str(i+1).zfill(4)}"
            
            # Trader characteristics
            experience = np.random.choice(
                [1, 2, 3, 5, 7, 10, 15],
                p=[0.15, 0.20, 0.20, 0.20, 0.15, 0.07, 0.03]
            )
            
            # Risk profile affects trading behavior
            risk_profile = np.random.choice(
                ['conservative', 'moderate', 'aggressive'],
                p=[0.3, 0.5, 0.2]
            )
            
            # Trader specialization
            specialization = np.random.choice(
                ['tech', 'finance', 'diversified', 'energy', 'consumer'],
                p=[0.3, 0.25, 0.25, 0.1, 0.1]
            )
            
            traders.append({
                'trader_id': trader_id,
                'experience_years': experience,
                'risk_profile': risk_profile,
                'specialization': specialization,
                'is_anomalous': np.random.random() < 0.1  # 10% anomalous traders
            })
        
        return pd.DataFrame(traders)
    
    def generate_trades_for_trader(self, trader: Dict, 
                                   start_date: datetime,
                                   n_days: int,
                                   trades_per_day_range: tuple = (1, 10)) -> List[Dict]:
        """
        Generate trades for a specific trader.
        
        Args:
            trader: Trader profile dictionary
            start_date: Starting date for trades
            n_days: Number of days to simulate
            trades_per_day_range: Min/max trades per day
            
        Returns:
            List of trade dictionaries
        """
        trades = []
        trade_counter = 1
        
        # Determine assets based on specialization
        if trader['specialization'] == 'tech':
            preferred_assets = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META', 'NVDA', 'INTC', 'AMD']
        elif trader['specialization'] == 'finance':
            preferred_assets = ['JPM', 'BAC', 'GS', 'MS', 'C', 'WFC', 'V', 'MA']
        elif trader['specialization'] == 'energy':
            preferred_assets = ['XOM', 'CVX', 'COP', 'SLB', 'OXY']
        elif trader['specialization'] == 'consumer':
            preferred_assets = ['DIS', 'NFLX', 'WMT', 'TGT', 'HD', 'NKE']
        else:
            preferred_assets = self.assets
        
        # Determine trade characteristics based on risk profile
        if trader['risk_profile'] == 'conservative':
            quantity_range = (50, 200)
            volatility = 0.05
        elif trader['risk_profile'] == 'moderate':
            quantity_range = (100, 500)
            volatility = 0.10
        else:  # aggressive
            quantity_range = (200, 1000)
            volatility = 0.20
        
        # Generate trades over time
        for day in range(n_days):
            current_date = start_date + timedelta(days=day)
            
            # Skip weekends
            if current_date.weekday() >= 5:
                continue
            
            # Number of trades for this day
            n_trades = np.random.randint(*trades_per_day_range)
            
            # Anomalous traders may have unusual patterns
            if trader['is_anomalous']:
                if np.random.random() < 0.2:  # 20% chance of unusual activity
                    n_trades = int(n_trades * np.random.uniform(3, 5))
                    quantity_range = (quantity_range[0] * 2, quantity_range[1] * 3)
            
            for _ in range(n_trades):
                # Random time during trading hours (9:30 AM - 4:00 PM)
                hour = np.random.randint(9, 16)
                minute = np.random.randint(0, 60) if hour < 16 else np.random.randint(0, 1)
                timestamp = current_date.replace(hour=hour, minute=minute, second=np.random.randint(0, 60))
                
                # Select asset
                asset = np.random.choice(preferred_assets)
                
                # Generate quantity
                quantity = np.random.randint(*quantity_range)
                
                # Generate price with some market volatility
                base_prices = {
                    'AAPL': 175, 'GOOGL': 145, 'MSFT': 420, 'AMZN': 180, 'META': 485,
                    'TSLA': 195, 'NVDA': 875, 'JPM': 185, 'BAC': 35, 'GS': 425,
                    'MS': 98, 'C': 62, 'WFC': 55, 'V': 280, 'MA': 465,
                    'INTC': 43, 'AMD': 186, 'DIS': 108, 'NFLX': 625
                }
                base_price = base_prices.get(asset, 100)
                price = base_price * (1 + np.random.uniform(-volatility, volatility))
                
                # Trade type
                trade_type = np.random.choice(self.trade_types)
                
                # Market and region
                market = 'NASDAQ' if asset in ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META', 'TSLA', 'NVDA'] else 'NYSE'
                region = np.random.choice(self.regions, p=[0.6, 0.2, 0.15, 0.05])
                
                trade = {
                    'trade_id': f"T{str(trade_counter).zfill(6)}",
                    'trader_id': trader['trader_id'],
                    'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'asset': asset,
                    'quantity': quantity,
                    'price': round(price, 2),
                    'trade_type': trade_type,
                    'market': market,
                    'region': region,
                    'trader_experience': trader['experience_years']
                }
                
                trades.append(trade)
                trade_counter += 1
        
        return trades
    
    def generate_dataset(self, n_traders: int = 50,
                        n_days: int = 30,
                        trades_per_day_range: tuple = (2, 8)) -> tuple:
        """
        Generate complete dataset with traders and trades.
        
        Args:
            n_traders: Number of traders to generate
            n_days: Number of days to simulate
            trades_per_day_range: Min/max trades per day per trader
            
        Returns:
            Tuple of (traders_df, trades_df)
        """
        print(f"Generating {n_traders} traders...")
        traders_df = self.generate_trader_profiles(n_traders)
        
        print(f"Generating trades for {n_days} days...")
        all_trades = []
        
        start_date = datetime.now() - timedelta(days=n_days)
        
        for idx, trader in traders_df.iterrows():
            trader_dict = trader.to_dict()
            trades = self.generate_trades_for_trader(
                trader_dict,
                start_date,
                n_days,
                trades_per_day_range
            )
            all_trades.extend(trades)
        
        trades_df = pd.DataFrame(all_trades)
        
        print(f"Generated {len(trades_df)} trades for {n_traders} traders")
        print(f"Date range: {trades_df['timestamp'].min()} to {trades_df['timestamp'].max()}")
        
        return traders_df, trades_df
    
    def save_dataset(self, trades_df: pd.DataFrame, 
                    traders_df: pd.DataFrame,
                    output_dir: str = '../data') -> None:
        """
        Save generated dataset to CSV files.
        
        Args:
            trades_df: Trades DataFrame
            traders_df: Traders DataFrame
            output_dir: Directory to save files
        """
        import os
        
        os.makedirs(output_dir, exist_ok=True)
        
        trades_path = os.path.join(output_dir, 'generated_trades.csv')
        traders_path = os.path.join(output_dir, 'generated_traders.csv')
        
        trades_df.to_csv(trades_path, index=False)
        traders_df.to_csv(traders_path, index=False)
        
        print(f"\nDataset saved:")
        print(f"  Trades: {trades_path}")
        print(f"  Traders: {traders_path}")
    
    def generate_anomalous_trades(self, n_trades: int = 50) -> pd.DataFrame:
        """
        Generate specifically anomalous trades for testing.
        
        Args:
            n_trades: Number of anomalous trades to generate
            
        Returns:
            DataFrame of anomalous trades
        """
        trades = []
        
        for i in range(n_trades):
            timestamp = datetime.now() - timedelta(
                days=np.random.randint(0, 30),
                hours=np.random.randint(0, 24),
                minutes=np.random.randint(0, 60)
            )
            
            # Unusual characteristics
            asset = np.random.choice(self.assets)
            
            # Extremely large quantity
            quantity = np.random.randint(5000, 20000)
            
            # Unusual price
            price = np.random.uniform(10, 2000)
            
            trade = {
                'trade_id': f"ANOM{str(i+1).zfill(4)}",
                'trader_id': f"TR_ANOM{str(i+1).zfill(3)}",
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'asset': asset,
                'quantity': quantity,
                'price': round(price, 2),
                'trade_type': np.random.choice(self.trade_types),
                'market': np.random.choice(self.markets),
                'region': np.random.choice(self.regions),
                'trader_experience': np.random.randint(0, 2)
            }
            
            trades.append(trade)
        
        return pd.DataFrame(trades)


if __name__ == "__main__":
    print("Fake Trader Generator")
    print("=" * 60)
    
    # Generate dataset
    generator = FakeTraderGenerator(seed=42)
    
    traders_df, trades_df = generator.generate_dataset(
        n_traders=30,
        n_days=14,
        trades_per_day_range=(2, 6)
    )
    
    # Display summary
    print("\n" + "=" * 60)
    print("DATASET SUMMARY")
    print("=" * 60)
    print(f"\nTraders: {len(traders_df)}")
    print(f"Trades: {len(trades_df)}")
    print(f"\nRisk Profile Distribution:")
    print(traders_df['risk_profile'].value_counts())
    print(f"\nSpecialization Distribution:")
    print(traders_df['specialization'].value_counts())
    print(f"\nAnomalous Traders: {traders_df['is_anomalous'].sum()}")
    
    print("\n" + "=" * 60)
    print("SAMPLE TRADES")
    print("=" * 60)
    print(trades_df.head(10))
    
    # Save dataset
    generator.save_dataset(trades_df, traders_df)
    
    # Generate anomalous trades
    print("\n" + "=" * 60)
    print("GENERATING ANOMALOUS TRADES")
    print("=" * 60)
    anom_trades = generator.generate_anomalous_trades(n_trades=10)
    print(anom_trades.head())
