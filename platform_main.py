"""
Risk AI Platform - Integrated Main Pipeline
Trader Blow-Up Prevention & Behavioral Risk Detection

This is the new integrated system based on the platform vision.
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from models.behavioral_drift import BehavioralDriftDetector
from models.risk_escalation import RiskEscalationMonitor
from scoring.trader_health import TraderHealthScorer
from alerts.alert_system import AlertSystem
from simulation.behavioral_simulator import BehavioralTraderSimulator

import pandas as pd
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class TradingRiskPlatform:
    """
    Complete platform for trader risk and behavioral intelligence.
    
    Core modules:
    1. Behavioral Drift Detection
    2. Risk Escalation Monitoring
    3. Trader Health Scoring
    4. Alert Generation
    """
    
    def __init__(self):
        """Initialize all platform modules."""
        self.drift_detector = BehavioralDriftDetector()
        self.risk_monitor = RiskEscalationMonitor()
        self.health_scorer = TraderHealthScorer()
        self.alert_system = AlertSystem()
        
        self.trades_df = None
        self.results = {}
    
    def load_data(self, filepath: str) -> pd.DataFrame:
        """Load trade data from CSV."""
        print(f"\n{'='*70}")
        print("LOADING TRADE DATA")
        print('='*70)
        
        self.trades_df = pd.read_csv(filepath)
        self.trades_df['timestamp'] = pd.to_datetime(self.trades_df['timestamp'])
        
        print(f"✓ Loaded {len(self.trades_df)} trades")
        print(f"✓ Date range: {self.trades_df['timestamp'].min()} to {self.trades_df['timestamp'].max()}")
        print(f"✓ Unique traders: {self.trades_df['trader_id'].nunique()}")
        
        return self.trades_df
    
    def analyze_trader(self, trader_id: str) -> dict:
        """
        Complete risk analysis for a single trader.
        
        Returns dict with:
        - drift_signals
        - risk_signals
        - health_report
        - alerts
        """
        if self.trades_df is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        # 1. Behavioral Drift Detection
        drift_signals = self.drift_detector.detect_all_drift_signals(
            self.trades_df, trader_id
        )
        
        # 2. Risk Escalation Monitoring
        risk_signals = self.risk_monitor.monitor_all_risks(
            self.trades_df, trader_id
        )
        
        # 3. Trader Health Score
        health_report = self.health_scorer.compute_health_score(
            self.trades_df, trader_id, drift_signals, risk_signals
        )
        
        # 4. Alert Generation
        alerts = self.alert_system.generate_alerts(
            trader_id, health_report, drift_signals, risk_signals
        )
        
        return {
            'trader_id': trader_id,
            'drift_signals': drift_signals,
            'risk_signals': risk_signals,
            'health_report': health_report,
            'alerts': alerts
        }
    
    def analyze_all_traders(self) -> pd.DataFrame:
        """Analyze all traders in the dataset."""
        if self.trades_df is None:
            raise ValueError("No data loaded.")
        
        print(f"\n{'='*70}")
        print("ANALYZING ALL TRADERS")
        print('='*70)
        
        trader_ids = self.trades_df['trader_id'].unique()
        results = []
        
        for i, trader_id in enumerate(trader_ids, 1):
            print(f"\rAnalyzing trader {i}/{len(trader_ids)}: {trader_id}", end='')
            
            try:
                result = self.analyze_trader(trader_id)
                
                # Summarize for DataFrame
                summary = {
                    'trader_id': trader_id,
                    'health_score': result['health_report'].health_score,
                    'health_status': result['health_report'].status.value,
                    'drift_signals': len(result['drift_signals']),
                    'risk_signals': len(result['risk_signals']),
                    'alerts': len(result['alerts']),
                    'critical_alerts': sum(1 for a in result['alerts'] if a.severity.value == 'critical'),
                    'requires_action': any(a.requires_action for a in result['alerts'])
                }
                results.append(summary)
                
                # Store detailed results
                self.results[trader_id] = result
                
            except Exception as e:
                logger.warning("Error analyzing trader %s: %s", trader_id, e)
                continue
        
        print()  # New line after progress
        
        results_df = pd.DataFrame(results)
        return results_df
    
    def generate_report(self, results_df: pd.DataFrame) -> str:
        """Generate comprehensive risk report."""
        print(f"\n{'='*70}")
        print("RISK INTELLIGENCE REPORT")
        print('='*70)
        
        report = []
        
        # Overall statistics
        total_traders = len(results_df)
        traders_with_alerts = results_df[results_df['alerts'] > 0].shape[0]
        critical_traders = results_df[results_df['critical_alerts'] > 0].shape[0]
        action_required = results_df[results_df['requires_action']].shape[0]
        
        report.append(f"\n{'='*70}")
        report.append("OVERVIEW")
        report.append('='*70)
        report.append(f"Total Traders Analyzed: {total_traders}")
        report.append(f"Traders with Alerts: {traders_with_alerts} ({traders_with_alerts/total_traders*100:.1f}%)")
        report.append(f"Critical Risk Traders: {critical_traders}")
        report.append(f"Immediate Action Required: {action_required}")
        
        # Health score distribution
        report.append(f"\n{'='*70}")
        report.append("HEALTH SCORE DISTRIBUTION")
        report.append('='*70)
        
        avg_health = results_df['health_score'].mean()
        report.append(f"Average Health Score: {avg_health:.1f}/100")
        
        status_dist = results_df['health_status'].value_counts()
        for status, count in status_dist.items():
            pct = count / total_traders * 100
            report.append(f"  {status.title()}: {count} ({pct:.1f}%)")
        
        # Critical traders detail
        if critical_traders > 0:
            report.append(f"\n{'='*70}")
            report.append("⚠️  CRITICAL RISK TRADERS - IMMEDIATE ATTENTION")
            report.append('='*70)
            
            critical_df = results_df[results_df['critical_alerts'] > 0]
            critical_df = critical_df.sort_values('health_score')
            
            for idx, row in critical_df.head(10).iterrows():
                report.append(f"\n[CRITICAL] {row['trader_id']}")
                report.append(f"  Health Score: {row['health_score']:.1f}/100")
                report.append(f"  Critical Alerts: {row['critical_alerts']}")
                report.append(f"  Status: {row['health_status'].upper()}")
                
                # Get detailed alerts
                if row['trader_id'] in self.results:
                    trader_result = self.results[row['trader_id']]
                    for alert in trader_result['alerts']:
                        if alert.severity.value == 'critical':
                            report.append(f"  → {alert.title}")
        
        # Warning traders
        warning_df = results_df[
            (results_df['alerts'] > 0) & 
            (results_df['critical_alerts'] == 0)
        ]
        
        if len(warning_df) > 0:
            report.append(f"\n{'='*70}")
            report.append("⚠  WARNING - MONITOR CLOSELY")
            report.append('='*70)
            
            for idx, row in warning_df.head(5).iterrows():
                report.append(f"\n[WARNING] {row['trader_id']}")
                report.append(f"  Health Score: {row['health_score']:.1f}/100")
                report.append(f"  Alerts: {row['alerts']}")
        
        # Healthy traders
        healthy_count = results_df[results_df['health_status'] == 'healthy'].shape[0]
        report.append(f"\n{'='*70}")
        report.append(f"✓ HEALTHY TRADERS: {healthy_count}")
        report.append('='*70)
        
        report.append(f"\nNo immediate concerns for {healthy_count} traders")
        
        # Alert system summary
        alert_summary = self.alert_system.get_alert_summary()
        report.append(f"\n{'='*70}")
        report.append("ALERT SUMMARY")
        report.append('='*70)
        report.append(f"Total Alerts Generated: {alert_summary['total_alerts']}")
        report.append(f"  Critical: {alert_summary['critical']}")
        report.append(f"  Warning: {alert_summary['warning']}")
        report.append(f"  Requires Action: {alert_summary['requires_action']}")
        
        report_text = '\n'.join(report)
        print(report_text)
        
        return report_text
    
    def export_results(self, results_df: pd.DataFrame, output_dir: str = 'data') -> None:
        """Export results to files."""
        import json
        
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Export summary CSV
        summary_path = os.path.join(output_dir, f'risk_summary_{timestamp}.csv')
        results_df.to_csv(summary_path, index=False)
        print(f"\n✓ Summary exported: {summary_path}")
        
        # Export alerts JSON
        alerts_path = os.path.join(output_dir, f'alerts_{timestamp}.json')
        alerts_json = self.alert_system.export_alerts(format='json')
        with open(alerts_path, 'w') as f:
            f.write(alerts_json)
        print(f"✓ Alerts exported: {alerts_path}")
        
        # Export detailed results for critical traders
        critical_traders = results_df[results_df['critical_alerts'] > 0]['trader_id'].tolist()
        
        if critical_traders:
            critical_details = {}
            for trader_id in critical_traders:
                if trader_id in self.results:
                    result = self.results[trader_id]
                    critical_details[trader_id] = {
                        'health_score': result['health_report'].health_score,
                        'status': result['health_report'].status.value,
                        'risk_factors': result['health_report'].risk_factors,
                        'recommendations': result['health_report'].recommendations,
                        'drift_signals_count': len(result['drift_signals']),
                        'risk_signals_count': len(result['risk_signals']),
                        'alerts_count': len(result['alerts'])
                    }
            
            critical_path = os.path.join(output_dir, f'critical_traders_{timestamp}.json')
            with open(critical_path, 'w') as f:
                json.dump(critical_details, f, indent=2)
            print(f"✓ Critical trader details exported: {critical_path}")


def main():
    """Main entry point for the Risk AI Platform."""
    parser = argparse.ArgumentParser(
        description='AI Trader Risk & Behavior Intelligence Platform'
    )
    
    parser.add_argument(
        '--data',
        type=str,
        default='data/sample_trades.csv',
        help='Path to trade data CSV file'
    )
    
    parser.add_argument(
        '--simulate',
        action='store_true',
        help='Generate simulated trader data'
    )
    
    parser.add_argument(
        '--traders',
        type=int,
        default=20,
        help='Number of traders to simulate'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=60,
        help='Number of days to simulate'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='data',
        help='Output directory for results'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize platform
        platform = TradingRiskPlatform()
        
        # Generate simulated data if requested
        if args.simulate:
            print(f"\n{'='*70}")
            print("GENERATING SIMULATED TRADER DATA")
            print('='*70)
            
            simulator = BehavioralTraderSimulator(seed=42)
            simulated_trades = simulator.generate_mixed_population(
                n_traders=args.traders,
                n_days=args.days
            )
            
            sim_path = os.path.join(args.output, 'simulated_traders.csv')
            simulated_trades.to_csv(sim_path, index=False)
            
            print(f"\n✓ Generated {len(simulated_trades)} trades for {args.traders} traders")
            print(f"✓ Saved to: {sim_path}")
            
            # Use simulated data
            data_path = sim_path
        else:
            data_path = args.data
        
        # Load data
        platform.load_data(data_path)
        
        # Analyze all traders
        results_df = platform.analyze_all_traders()
        
        # Generate report
        platform.generate_report(results_df)
        
        # Export results
        platform.export_results(results_df, args.output)
        
        print(f"\n{'='*70}")
        print("✓ ANALYSIS COMPLETE")
        print('='*70)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
