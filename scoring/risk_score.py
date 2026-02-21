"""
Risk Scoring Module for Risk AI
Calculates comprehensive risk scores for traders based on multiple factors.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from enum import Enum


class RiskLevel(Enum):
    """Risk level categories."""
    LOW = "Low Risk"
    MEDIUM = "Medium Risk"
    HIGH = "High Risk"
    CRITICAL = "Critical Risk"


class RiskScorer:
    """
    Calculate and aggregate risk scores for traders.
    """
    
    def __init__(self):
        """Initialize risk scorer with default weights."""
        self.weights = {
            'volume_risk': 0.20,
            'volatility_risk': 0.25,
            'concentration_risk': 0.20,
            'anomaly_risk': 0.25,
            'experience_risk': 0.10
        }
        self.risk_thresholds = {
            'low': 30,
            'medium': 60,
            'high': 85
        }
        
    def set_weights(self, weights: Dict[str, float]) -> None:
        """
        Set custom weights for risk components.
        
        Args:
            weights: Dictionary of component names to weights (must sum to 1.0)
        """
        if not np.isclose(sum(weights.values()), 1.0):
            raise ValueError("Weights must sum to 1.0")
        self.weights = weights
        
    def calculate_volume_risk(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate risk based on trading volume.
        
        Higher volumes indicate higher potential risk.
        Score range: 0-100
        """
        if 'total_volume' not in df.columns:
            return pd.Series(0, index=df.index)
        
        # Normalize volume to 0-100 scale
        volume = df['total_volume']
        volume_normalized = (volume - volume.min()) / (volume.max() - volume.min() + 1e-10)
        
        return volume_normalized * 100
    
    def calculate_volatility_risk(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate risk based on trading volatility.
        
        High volatility in trade sizes or prices indicates higher risk.
        Score range: 0-100
        """
        risk_score = pd.Series(0, index=df.index)
        
        # Trade size volatility
        if 'trade_size_volatility' in df.columns:
            trade_vol = df['trade_size_volatility'].fillna(0)
            trade_vol_norm = (trade_vol - trade_vol.min()) / (trade_vol.max() - trade_vol.min() + 1e-10)
            risk_score += trade_vol_norm * 50
        
        # Price volatility
        if 'price_volatility' in df.columns:
            price_vol = df['price_volatility'].fillna(0)
            price_vol_norm = (price_vol - price_vol.min()) / (price_vol.max() - price_vol.min() + 1e-10)
            risk_score += price_vol_norm * 50
        
        return risk_score
    
    def calculate_concentration_risk(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate risk based on asset concentration.
        
        Low diversification (high concentration) indicates higher risk.
        Score range: 0-100
        """
        if 'asset_diversity' not in df.columns:
            return pd.Series(0, index=df.index)
        
        # Inverse of diversity = concentration
        diversity = df['asset_diversity']
        max_diversity = diversity.max()
        
        # Normalize: low diversity = high risk
        concentration_score = (1 - (diversity / (max_diversity + 1))) * 100
        
        return concentration_score
    
    def calculate_anomaly_risk(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate risk based on anomaly detection.
        
        Anomalous behavior indicates higher risk.
        Score range: 0-100
        """
        risk_score = pd.Series(0, index=df.index)
        
        # Binary anomaly flag
        if 'is_anomaly' in df.columns:
            risk_score += df['is_anomaly'] * 60
        
        # Anomaly score (continuous)
        if 'anomaly_score' in df.columns:
            anomaly_scores = df['anomaly_score'].fillna(0)
            # Normalize to 0-40 range
            if anomaly_scores.max() > 0:
                anomaly_norm = (anomaly_scores - anomaly_scores.min()) / (
                    anomaly_scores.max() - anomaly_scores.min() + 1e-10
                )
                risk_score += anomaly_norm * 40
        
        return risk_score
    
    def calculate_experience_risk(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate risk based on trader experience.
        
        Less experienced traders present higher risk.
        Score range: 0-100
        """
        if 'experience_years' not in df.columns:
            return pd.Series(0, index=df.index)
        
        experience = df['experience_years']
        
        # Inverse relationship: less experience = higher risk
        # Assume 10+ years = very low risk, 0 years = high risk
        max_experience = 10
        experience_capped = experience.clip(upper=max_experience)
        
        # Normalize: low experience = high risk
        risk_score = (1 - (experience_capped / max_experience)) * 100
        
        return risk_score
    
    def calculate_composite_risk_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate weighted composite risk score.
        
        Args:
            df: DataFrame with trader features
            
        Returns:
            DataFrame with individual and composite risk scores
        """
        result_df = df.copy()
        
        # Calculate individual risk components
        result_df['volume_risk_score'] = self.calculate_volume_risk(df)
        result_df['volatility_risk_score'] = self.calculate_volatility_risk(df)
        result_df['concentration_risk_score'] = self.calculate_concentration_risk(df)
        result_df['anomaly_risk_score'] = self.calculate_anomaly_risk(df)
        result_df['experience_risk_score'] = self.calculate_experience_risk(df)
        
        # Calculate weighted composite score
        result_df['composite_risk_score'] = (
            result_df['volume_risk_score'] * self.weights['volume_risk'] +
            result_df['volatility_risk_score'] * self.weights['volatility_risk'] +
            result_df['concentration_risk_score'] * self.weights['concentration_risk'] +
            result_df['anomaly_risk_score'] * self.weights['anomaly_risk'] +
            result_df['experience_risk_score'] * self.weights['experience_risk']
        )
        
        # Ensure score is in 0-100 range
        result_df['composite_risk_score'] = result_df['composite_risk_score'].clip(0, 100)
        
        return result_df
    
    def assign_risk_level(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Assign risk level category based on composite score.
        
        Args:
            df: DataFrame with 'composite_risk_score' column
            
        Returns:
            DataFrame with 'risk_level' column added
        """
        result_df = df.copy()
        
        def categorize_risk(score):
            if score < self.risk_thresholds['low']:
                return RiskLevel.LOW.value
            elif score < self.risk_thresholds['medium']:
                return RiskLevel.MEDIUM.value
            elif score < self.risk_thresholds['high']:
                return RiskLevel.HIGH.value
            else:
                return RiskLevel.CRITICAL.value
        
        result_df['risk_level'] = result_df['composite_risk_score'].apply(categorize_risk)
        
        return result_df
    
    def get_risk_summary(self, df: pd.DataFrame) -> Dict:
        """
        Generate summary statistics for risk scores.
        
        Args:
            df: DataFrame with risk scores and levels
            
        Returns:
            Dictionary with summary statistics
        """
        summary = {
            'total_traders': len(df),
            'avg_risk_score': df['composite_risk_score'].mean(),
            'max_risk_score': df['composite_risk_score'].max(),
            'min_risk_score': df['composite_risk_score'].min(),
            'std_risk_score': df['composite_risk_score'].std()
        }
        
        # Risk level distribution
        if 'risk_level' in df.columns:
            risk_dist = df['risk_level'].value_counts().to_dict()
            summary['risk_distribution'] = risk_dist
        
        return summary
    
    def get_high_risk_traders(self, df: pd.DataFrame, 
                             threshold: float = None) -> pd.DataFrame:
        """
        Get traders above a risk threshold.
        
        Args:
            df: DataFrame with risk scores
            threshold: Risk score threshold (default: high risk threshold)
            
        Returns:
            DataFrame of high-risk traders
        """
        if threshold is None:
            threshold = self.risk_thresholds['medium']
        
        high_risk = df[df['composite_risk_score'] >= threshold].copy()
        high_risk = high_risk.sort_values('composite_risk_score', ascending=False)
        
        return high_risk
    
    def generate_risk_report(self, df: pd.DataFrame) -> str:
        """
        Generate a formatted risk report.
        
        Args:
            df: DataFrame with risk scores
            
        Returns:
            Formatted string report
        """
        summary = self.get_risk_summary(df)
        
        report = []
        report.append("=" * 60)
        report.append("RISK ASSESSMENT REPORT")
        report.append("=" * 60)
        report.append(f"\nTotal Traders Analyzed: {summary['total_traders']}")
        report.append(f"Average Risk Score: {summary['avg_risk_score']:.2f}")
        report.append(f"Risk Score Range: {summary['min_risk_score']:.2f} - {summary['max_risk_score']:.2f}")
        report.append(f"Standard Deviation: {summary['std_risk_score']:.2f}")
        
        if 'risk_distribution' in summary:
            report.append("\nRisk Level Distribution:")
            for level, count in summary['risk_distribution'].items():
                percentage = (count / summary['total_traders']) * 100
                report.append(f"  {level}: {count} ({percentage:.1f}%)")
        
        # High risk traders
        high_risk = self.get_high_risk_traders(df, threshold=self.risk_thresholds['high'])
        if len(high_risk) > 0:
            report.append(f"\nHigh Risk Traders (Score >= {self.risk_thresholds['high']}):")
            if 'trader_id' in high_risk.columns:
                for idx, row in high_risk.head(10).iterrows():
                    report.append(f"  {row['trader_id']}: {row['composite_risk_score']:.2f}")
        
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)


if __name__ == "__main__":
    # Example usage
    print("Risk Scoring Module")
    print("=" * 60)
    
    # Create sample trader data
    np.random.seed(42)
    n_traders = 20
    
    sample_data = pd.DataFrame({
        'trader_id': [f'TR{str(i).zfill(3)}' for i in range(1, n_traders + 1)],
        'total_volume': np.random.randint(100, 5000, n_traders),
        'trade_size_volatility': np.random.uniform(10, 200, n_traders),
        'price_volatility': np.random.uniform(5, 100, n_traders),
        'asset_diversity': np.random.randint(1, 10, n_traders),
        'is_anomaly': np.random.choice([0, 1], n_traders, p=[0.85, 0.15]),
        'anomaly_score': np.random.uniform(0, 5, n_traders),
        'experience_years': np.random.randint(0, 15, n_traders)
    })
    
    # Calculate risk scores
    scorer = RiskScorer()
    result_df = scorer.calculate_composite_risk_score(sample_data)
    result_df = scorer.assign_risk_level(result_df)
    
    # Generate report
    print(scorer.generate_risk_report(result_df))
    
    print("\nTop 5 Riskiest Traders:")
    top_risk = result_df.nlargest(5, 'composite_risk_score')
    print(top_risk[['trader_id', 'composite_risk_score', 'risk_level']])
