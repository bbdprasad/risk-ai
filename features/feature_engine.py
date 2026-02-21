"""
Feature Engineering Module for Risk AI
Extracts and transforms features from trade data for risk analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime, timedelta


class FeatureEngine:
    """
    Feature engine to extract meaningful features from trade data.
    """
    
    def __init__(self):
        self.features = []
        
    def load_trades(self, filepath: str) -> pd.DataFrame:
        """Load trade data from CSV file."""
        df = pd.read_csv(filepath)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    
    def calculate_trader_features(self, trades_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate trader-level aggregated features.
        
        Features include:
        - Total trade volume
        - Average trade size
        - Trade frequency
        - Asset diversity
        - Buy/Sell ratio
        """
        trader_features = trades_df.groupby('trader_id').agg({
            'trade_id': 'count',  # Total trades
            'quantity': ['sum', 'mean', 'std'],  # Volume metrics
            'price': ['mean', 'std'],  # Price metrics
            'asset': 'nunique',  # Asset diversity
            'trader_experience': 'first'
        }).reset_index()
        
        trader_features.columns = ['_'.join(col).strip('_') for col in trader_features.columns.values]
        trader_features.rename(columns={
            'trade_id_count': 'total_trades',
            'quantity_sum': 'total_volume',
            'quantity_mean': 'avg_trade_size',
            'quantity_std': 'trade_size_volatility',
            'price_mean': 'avg_price',
            'price_std': 'price_volatility',
            'asset_nunique': 'asset_diversity',
            'trader_experience_first': 'experience_years'
        }, inplace=True)
        
        # Calculate buy/sell ratio
        buy_sell = trades_df.groupby(['trader_id', 'trade_type']).size().unstack(fill_value=0)
        if 'BUY' in buy_sell.columns and 'SELL' in buy_sell.columns:
            trader_features['buy_sell_ratio'] = (
                buy_sell['BUY'] / (buy_sell['SELL'] + 1)
            ).values
        else:
            trader_features['buy_sell_ratio'] = 0
        
        return trader_features
    
    def calculate_temporal_features(self, trades_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate time-based features.
        
        Features include:
        - Trading time patterns (morning/afternoon)
        - Time between trades
        - Trading velocity
        """
        trades_df = trades_df.sort_values('timestamp')
        
        # Extract hour of day
        trades_df['hour'] = trades_df['timestamp'].dt.hour
        trades_df['is_morning'] = (trades_df['hour'] < 12).astype(int)
        
        # Time between trades for each trader
        trades_df['time_since_last_trade'] = trades_df.groupby('trader_id')['timestamp'].diff()
        trades_df['time_since_last_trade_seconds'] = trades_df['time_since_last_trade'].dt.total_seconds()
        
        return trades_df
    
    def calculate_risk_indicators(self, trades_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate risk-related indicators.
        
        Features include:
        - Large trade flag (> 2 std deviations)
        - Unusual price flag
        - Concentration risk
        """
        # Flag large trades
        mean_qty = trades_df['quantity'].mean()
        std_qty = trades_df['quantity'].std()
        trades_df['is_large_trade'] = (trades_df['quantity'] > mean_qty + 2 * std_qty).astype(int)
        
        # Flag unusual prices
        mean_price = trades_df['price'].mean()
        std_price = trades_df['price'].std()
        trades_df['is_unusual_price'] = (
            (trades_df['price'] > mean_price + 2 * std_price) |
            (trades_df['price'] < mean_price - 2 * std_price)
        ).astype(int)
        
        # Calculate position concentration per trader
        trader_asset_concentration = trades_df.groupby('trader_id')['asset'].apply(
            lambda x: x.value_counts().iloc[0] / len(x) if len(x) > 0 else 0
        ).reset_index()
        trader_asset_concentration.columns = ['trader_id', 'asset_concentration']
        
        trades_df = trades_df.merge(trader_asset_concentration, on='trader_id', how='left')
        
        return trades_df
    
    def generate_all_features(self, filepath: str) -> tuple:
        """
        Generate all features from trade data.
        
        Returns:
            tuple: (trade_level_features_df, trader_level_features_df)
        """
        # Load data
        trades_df = self.load_trades(filepath)
        
        # Generate features
        trades_df = self.calculate_temporal_features(trades_df)
        trades_df = self.calculate_risk_indicators(trades_df)
        trader_features = self.calculate_trader_features(trades_df)
        
        return trades_df, trader_features
    
    def get_feature_names(self, level: str = 'trader') -> List[str]:
        """Get list of feature names."""
        if level == 'trader':
            return [
                'total_trades', 'total_volume', 'avg_trade_size',
                'trade_size_volatility', 'avg_price', 'price_volatility',
                'asset_diversity', 'experience_years', 'buy_sell_ratio'
            ]
        elif level == 'trade':
            return [
                'hour', 'is_morning', 'time_since_last_trade_seconds',
                'is_large_trade', 'is_unusual_price', 'asset_concentration'
            ]
        else:
            raise ValueError(f"Unknown level: {level}")


if __name__ == "__main__":
    # Example usage
    engine = FeatureEngine()
    trades_df, trader_features = engine.generate_all_features("../data/sample_trades.csv")
    
    print("Trade-level features shape:", trades_df.shape)
    print("\nTrader-level features:")
    print(trader_features.head())
    
    print("\nFeature names:")
    print("Trader features:", engine.get_feature_names('trader'))
    print("Trade features:", engine.get_feature_names('trade'))
