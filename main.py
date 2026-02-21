"""
Risk AI - Main Application
End-to-end risk analysis pipeline for trader behavior monitoring.

This application:
1. Loads or generates trader data
2. Extracts features from trading patterns
3. Detects anomalous behavior
4. Calculates comprehensive risk scores
5. Generates risk reports
"""

import sys
import os
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from features.feature_engine import FeatureEngine
from models.anomaly_detection import AnomalyDetector
from scoring.risk_score import RiskScorer
from simulation.generate_fake_traders import FakeTraderGenerator

import pandas as pd
import numpy as np


class RiskAIPipeline:
    """
    Complete pipeline for risk analysis of trading behavior.
    """
    
    def __init__(self, data_path: str = None, contamination: float = 0.1):
        """
        Initialize the Risk AI pipeline.
        
        Args:
            data_path: Path to trade data CSV file
            contamination: Expected proportion of anomalies (default: 10%)
        """
        self.data_path = data_path
        self.feature_engine = FeatureEngine()
        self.anomaly_detector = AnomalyDetector(contamination=contamination)
        self.risk_scorer = RiskScorer()
        
        self.trades_df = None
        self.trader_features_df = None
        self.results_df = None
        
    def load_data(self, path: str = None) -> pd.DataFrame:
        """Load trade data from CSV file."""
        if path is None:
            path = self.data_path
        
        if path is None or not os.path.exists(path):
            raise FileNotFoundError(f"Data file not found: {path}")
        
        print(f"Loading data from: {path}")
        self.trades_df = self.feature_engine.load_trades(path)
        print(f"Loaded {len(self.trades_df)} trades")
        
        return self.trades_df
    
    def extract_features(self) -> pd.DataFrame:
        """Extract features from trade data."""
        if self.trades_df is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        print("\n" + "=" * 60)
        print("EXTRACTING FEATURES")
        print("=" * 60)
        
        # Generate trade-level and trader-level features
        self.trades_df, self.trader_features_df = self.feature_engine.generate_all_features(
            self.data_path
        )
        
        print(f"Generated features for {len(self.trader_features_df)} unique traders")
        print(f"Trade-level features: {self.trades_df.shape[1]} columns")
        print(f"Trader-level features: {self.trader_features_df.shape[1]} columns")
        
        return self.trader_features_df
    
    def detect_anomalies(self, method: str = 'ensemble') -> pd.DataFrame:
        """Detect anomalous traders."""
        if self.trader_features_df is None:
            raise ValueError("No features extracted. Call extract_features() first.")
        
        print("\n" + "=" * 60)
        print("DETECTING ANOMALIES")
        print("=" * 60)
        
        # Define feature columns for anomaly detection
        feature_columns = [
            'total_trades', 'total_volume', 'avg_trade_size',
            'trade_size_volatility', 'avg_price', 'price_volatility',
            'asset_diversity', 'buy_sell_ratio'
        ]
        
        # Filter to only available columns
        available_features = [col for col in feature_columns if col in self.trader_features_df.columns]
        
        print(f"Using {len(available_features)} features for anomaly detection")
        print(f"Method: {method}")
        
        # Detect anomalies
        self.trader_features_df = self.anomaly_detector.detect_anomalies(
            self.trader_features_df,
            feature_columns=available_features,
            method=method
        )
        
        # Print summary
        summary = self.anomaly_detector.get_anomaly_summary(self.trader_features_df)
        print(f"\nTotal traders: {summary['total_records']}")
        print(f"Anomalies detected: {summary['total_anomalies']}")
        print(f"Anomaly rate: {summary['anomaly_rate']:.2%}")
        
        return self.trader_features_df
    
    def calculate_risk_scores(self) -> pd.DataFrame:
        """Calculate comprehensive risk scores."""
        if self.trader_features_df is None:
            raise ValueError("No features available. Run the pipeline first.")
        
        print("\n" + "=" * 60)
        print("CALCULATING RISK SCORES")
        print("=" * 60)
        
        # Calculate composite risk scores
        self.results_df = self.risk_scorer.calculate_composite_risk_score(
            self.trader_features_df
        )
        
        # Assign risk levels
        self.results_df = self.risk_scorer.assign_risk_level(self.results_df)
        
        print("Risk scores calculated successfully")
        
        return self.results_df
    
    def generate_report(self) -> str:
        """Generate comprehensive risk report."""
        if self.results_df is None:
            raise ValueError("No results available. Run the full pipeline first.")
        
        print("\n" + "=" * 60)
        print("GENERATING RISK REPORT")
        print("=" * 60)
        
        report = self.risk_scorer.generate_risk_report(self.results_df)
        print(report)
        
        return report
    
    def run_pipeline(self, method: str = 'ensemble') -> pd.DataFrame:
        """
        Run the complete risk analysis pipeline.
        
        Args:
            method: Anomaly detection method ('ensemble', 'isolation_forest', 
                   'elliptic_envelope', 'statistical')
                   
        Returns:
            DataFrame with complete risk analysis results
        """
        print("=" * 60)
        print("RISK AI PIPELINE")
        print("=" * 60)
        
        # Step 1: Load data
        if self.trades_df is None:
            self.load_data()
        
        # Step 2: Extract features
        self.extract_features()
        
        # Step 3: Detect anomalies
        self.detect_anomalies(method=method)
        
        # Step 4: Calculate risk scores
        self.calculate_risk_scores()
        
        # Step 5: Generate report
        self.generate_report()
        
        print("\n" + "=" * 60)
        print("PIPELINE COMPLETED")
        print("=" * 60)
        
        return self.results_df
    
    def save_results(self, output_path: str) -> None:
        """Save results to CSV file."""
        if self.results_df is None:
            raise ValueError("No results to save. Run the pipeline first.")
        
        self.results_df.to_csv(output_path, index=False)
        print(f"\nResults saved to: {output_path}")
    
    def get_top_risk_traders(self, n: int = 10) -> pd.DataFrame:
        """Get top N riskiest traders."""
        if self.results_df is None:
            raise ValueError("No results available. Run the pipeline first.")
        
        top_traders = self.results_df.nlargest(n, 'composite_risk_score')
        
        columns_to_show = [
            'trader_id', 'composite_risk_score', 'risk_level',
            'total_trades', 'total_volume', 'is_anomaly'
        ]
        available_columns = [col for col in columns_to_show if col in top_traders.columns]
        
        return top_traders[available_columns]


def generate_sample_data(n_traders: int = 30, n_days: int = 14):
    """Generate sample data for demonstration."""
    print("=" * 60)
    print("GENERATING SAMPLE DATA")
    print("=" * 60)
    
    generator = FakeTraderGenerator(seed=42)
    traders_df, trades_df = generator.generate_dataset(
        n_traders=n_traders,
        n_days=n_days,
        trades_per_day_range=(2, 6)
    )
    
    # Save to data directory
    data_dir = os.path.join(project_root, 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    output_path = os.path.join(data_dir, 'generated_trades.csv')
    trades_df.to_csv(output_path, index=False)
    
    print(f"\nSample data saved to: {output_path}")
    return output_path


def main():
    """Main entry point for the Risk AI application."""
    parser = argparse.ArgumentParser(
        description='Risk AI - Trading Behavior Risk Analysis'
    )
    
    parser.add_argument(
        '--data',
        type=str,
        default='data/sample_trades.csv',
        help='Path to trade data CSV file'
    )
    
    parser.add_argument(
        '--generate',
        action='store_true',
        help='Generate sample data before analysis'
    )
    
    parser.add_argument(
        '--traders',
        type=int,
        default=30,
        help='Number of traders to generate (if --generate flag is used)'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=14,
        help='Number of days to simulate (if --generate flag is used)'
    )
    
    parser.add_argument(
        '--method',
        type=str,
        default='ensemble',
        choices=['ensemble', 'isolation_forest', 'elliptic_envelope', 'statistical'],
        help='Anomaly detection method'
    )
    
    parser.add_argument(
        '--contamination',
        type=float,
        default=0.1,
        help='Expected proportion of anomalies (0.0 to 0.5)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='data/risk_analysis_results.csv',
        help='Path to save results'
    )
    
    parser.add_argument(
        '--top',
        type=int,
        default=10,
        help='Number of top risk traders to display'
    )
    
    args = parser.parse_args()
    
    try:
        # Generate sample data if requested
        if args.generate:
            data_path = generate_sample_data(n_traders=args.traders, n_days=args.days)
        else:
            data_path = os.path.join(project_root, args.data)
        
        # Initialize and run pipeline
        pipeline = RiskAIPipeline(
            data_path=data_path,
            contamination=args.contamination
        )
        
        results = pipeline.run_pipeline(method=args.method)
        
        # Display top risk traders
        print("\n" + "=" * 60)
        print(f"TOP {args.top} RISKIEST TRADERS")
        print("=" * 60)
        top_traders = pipeline.get_top_risk_traders(n=args.top)
        print(top_traders.to_string(index=False))
        
        # Save results
        output_path = os.path.join(project_root, args.output)
        pipeline.save_results(output_path)
        
        print("\n✓ Risk analysis completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
