"""
Alert System Module
Generates high-signal, rare alerts for trader blow-up prevention.

Alert Philosophy:
- Rare but meaningful
- Multi-signal validation
- Actionable recommendations
- Clear severity levels
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertCategory(Enum):
    """Alert categories."""
    BEHAVIORAL_DRIFT = "behavioral_drift"
    RISK_ESCALATION = "risk_escalation"
    HEALTH_DECLINE = "health_decline"
    MULTI_SIGNAL = "multi_signal"


@dataclass
class Alert:
    """Container for trader alert."""
    alert_id: str
    trader_id: str
    timestamp: datetime
    severity: AlertSeverity
    category: AlertCategory
    title: str
    message: str
    evidence: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    requires_action: bool = False
    
    def to_dict(self) -> Dict:
        """Convert alert to dictionary."""
        return {
            'alert_id': self.alert_id,
            'trader_id': self.trader_id,
            'timestamp': self.timestamp.isoformat(),
            'severity': self.severity.value,
            'category': self.category.value,
            'title': self.title,
            'message': self.message,
            'evidence': self.evidence,
            'recommendations': self.recommendations,
            'requires_action': self.requires_action
        }


class AlertSystem:
    """
    Intelligent alert generation system.
    
    Criteria for alerts:
    - 3+ anomaly signals fire simultaneously
    - OR structural risk break detected
    - OR health score drops below critical threshold
    
    Alert rate target: < 5% of traders flagged per day
    """
    
    def __init__(self,
                 health_critical_threshold: float = 40,
                 multi_signal_threshold: int = 3):
        """
        Initialize alert system.
        
        Args:
            health_critical_threshold: Health score below which to alert
            multi_signal_threshold: Number of signals to trigger multi-signal alert
        """
        self.health_critical_threshold = health_critical_threshold
        self.multi_signal_threshold = multi_signal_threshold
        self.alert_counter = 0
        self.alerts = []
    
    def _generate_alert_id(self) -> str:
        """Generate unique alert ID."""
        self.alert_counter += 1
        return f"ALT{datetime.now().strftime('%Y%m%d')}{self.alert_counter:04d}"
    
    def evaluate_health_score(self,
                             trader_id: str,
                             health_report) -> List[Alert]:
        """
        Evaluate health score and generate alerts if needed.
        
        Args:
            trader_id: Trader identifier
            health_report: HealthReport from TraderHealthScorer
            
        Returns:
            List of generated alerts
        """
        alerts = []
        
        from scoring.trader_health import HealthStatus
        
        # Critical health status
        if health_report.status == HealthStatus.CRITICAL:
            alert = Alert(
                alert_id=self._generate_alert_id(),
                trader_id=trader_id,
                timestamp=datetime.now(),
                severity=AlertSeverity.CRITICAL,
                category=AlertCategory.HEALTH_DECLINE,
                title="Critical Health Score - Immediate Intervention Required",
                message=f"Trader health score dropped to {health_report.health_score:.1f}/100",
                evidence=[
                    f"Health Score: {health_report.health_score:.1f}",
                    *[f"Risk Factor: {rf}" for rf in health_report.risk_factors]
                ],
                recommendations=health_report.recommendations,
                requires_action=True
            )
            alerts.append(alert)
        
        # Warning status with multiple risk factors
        elif health_report.status == HealthStatus.WARNING and len(health_report.risk_factors) >= 2:
            alert = Alert(
                alert_id=self._generate_alert_id(),
                trader_id=trader_id,
                timestamp=datetime.now(),
                severity=AlertSeverity.WARNING,
                category=AlertCategory.HEALTH_DECLINE,
                title="Declining Health Score - Supervision Recommended",
                message=f"Trader health declining: {health_report.health_score:.1f}/100 with {len(health_report.risk_factors)} risk factors",
                evidence=[
                    f"Health Score: {health_report.health_score:.1f}",
                    *[f"Risk Factor: {rf}" for rf in health_report.risk_factors]
                ],
                recommendations=health_report.recommendations[:3],
                requires_action=True
            )
            alerts.append(alert)
        
        return alerts
    
    def evaluate_behavioral_drift(self,
                                  trader_id: str,
                                  drift_signals: List) -> List[Alert]:
        """
        Evaluate behavioral drift signals.
        
        Args:
            trader_id: Trader identifier
            drift_signals: List of DriftSignal from BehavioralDriftDetector
            
        Returns:
            List of generated alerts
        """
        alerts = []
        
        if not drift_signals:
            return alerts
        
        from models.behavioral_drift import DriftSeverity
        
        # Count signals by severity
        critical_signals = [s for s in drift_signals if s.severity == DriftSeverity.CRITICAL]
        warning_signals = [s for s in drift_signals if s.severity == DriftSeverity.WARNING]
        
        # Critical: Any revenge trading or multiple critical signals
        revenge_signals = [s for s in critical_signals if 'revenge' in s.metric.lower()]
        
        if revenge_signals:
            alert = Alert(
                alert_id=self._generate_alert_id(),
                trader_id=trader_id,
                timestamp=datetime.now(),
                severity=AlertSeverity.CRITICAL,
                category=AlertCategory.BEHAVIORAL_DRIFT,
                title="Revenge Trading Detected",
                message="Trader increasing position size after losses - high blow-up risk",
                evidence=[s.message for s in revenge_signals],
                recommendations=[
                    "Reduce position sizes immediately",
                    "Consider trading pause after losses",
                    "Review emotional state before next trade"
                ],
                requires_action=True
            )
            alerts.append(alert)
        
        # Multiple critical drift signals
        elif len(critical_signals) >= 2:
            alert = Alert(
                alert_id=self._generate_alert_id(),
                trader_id=trader_id,
                timestamp=datetime.now(),
                severity=AlertSeverity.CRITICAL,
                category=AlertCategory.BEHAVIORAL_DRIFT,
                title="Severe Behavioral Drift Detected",
                message=f"{len(critical_signals)} critical behavioral deviations from normal pattern",
                evidence=[s.message for s in critical_signals],
                recommendations=[
                    "Review recent trading decisions",
                    "Return to proven trading plan",
                    "Consider position size reduction"
                ],
                requires_action=True
            )
            alerts.append(alert)
        
        # Multiple warning signals
        elif len(warning_signals) >= self.multi_signal_threshold:
            alert = Alert(
                alert_id=self._generate_alert_id(),
                trader_id=trader_id,
                timestamp=datetime.now(),
                severity=AlertSeverity.WARNING,
                category=AlertCategory.BEHAVIORAL_DRIFT,
                title="Pattern Deviation Detected",
                message=f"Trading pattern deviating from historical baseline",
                evidence=[s.message for s in warning_signals],
                recommendations=[
                    "Monitor trading patterns closely",
                    "Verify strategy alignment",
                    "Consider reducing frequency"
                ],
                requires_action=False
            )
            alerts.append(alert)
        
        return alerts
    
    def evaluate_risk_escalation(self,
                                trader_id: str,
                                risk_signals: List) -> List[Alert]:
        """
        Evaluate risk escalation signals.
        
        Args:
            trader_id: Trader identifier
            risk_signals: List of RiskSignal from RiskEscalationMonitor
            
        Returns:
            List of generated alerts
        """
        alerts = []
        
        if not risk_signals:
            return alerts
        
        from models.risk_escalation import RiskLevel
        
        # Count signals by risk level
        critical_risks = [s for s in risk_signals if s.risk_level == RiskLevel.CRITICAL]
        dangerous_risks = [s for s in risk_signals if s.risk_level == RiskLevel.DANGEROUS]
        
        # Critical: Any critical risk or multiple dangerous risks
        if critical_risks:
            alert = Alert(
                alert_id=self._generate_alert_id(),
                trader_id=trader_id,
                timestamp=datetime.now(),
                severity=AlertSeverity.CRITICAL,
                category=AlertCategory.RISK_ESCALATION,
                title="Critical Risk Level - Immediate Action Required",
                message=f"{len(critical_risks)} critical risk indicator(s) detected",
                evidence=[s.message for s in critical_risks],
                recommendations=[
                    "Close or reduce positions immediately",
                    "Suspend new trades until risk assessment",
                    "Review leverage and exposure"
                ],
                requires_action=True
            )
            alerts.append(alert)
        
        elif len(dangerous_risks) >= 2:
            alert = Alert(
                alert_id=self._generate_alert_id(),
                trader_id=trader_id,
                timestamp=datetime.now(),
                severity=AlertSeverity.WARNING,
                category=AlertCategory.RISK_ESCALATION,
                title="Elevated Risk - Intervention Recommended",
                message=f"Multiple risk escalation signals: {', '.join(s.category for s in dangerous_risks)}",
                evidence=[s.message for s in dangerous_risks],
                recommendations=[
                    "Reduce position sizes",
                    "Increase diversification",
                    "Review risk management rules"
                ],
                requires_action=True
            )
            alerts.append(alert)
        
        return alerts
    
    def evaluate_multi_signal(self,
                            trader_id: str,
                            drift_signals: List,
                            risk_signals: List,
                            health_report) -> List[Alert]:
        """
        Evaluate combined signals for multi-factor alert.
        
        Args:
            trader_id: Trader identifier
            drift_signals: Behavioral drift signals
            risk_signals: Risk escalation signals
            health_report: Health report
            
        Returns:
            List of generated alerts
        """
        alerts = []
        
        # Count total concerning signals
        total_signals = len(drift_signals) + len(risk_signals)
        
        # Multi-signal alert if 3+ signals and health below 60
        if total_signals >= self.multi_signal_threshold and health_report.health_score < 60:
            alert = Alert(
                alert_id=self._generate_alert_id(),
                trader_id=trader_id,
                timestamp=datetime.now(),
                severity=AlertSeverity.CRITICAL,
                category=AlertCategory.MULTI_SIGNAL,
                title="Multiple Risk Indicators - High Blow-Up Risk",
                message=f"{total_signals} risk signals detected with health score {health_report.health_score:.1f}",
                evidence=[
                    f"Health Score: {health_report.health_score:.1f}",
                    f"Behavioral Drift Signals: {len(drift_signals)}",
                    f"Risk Escalation Signals: {len(risk_signals)}",
                    *[f"- {s.message}" for s in (drift_signals + risk_signals)[:5]]
                ],
                recommendations=[
                    "IMMEDIATE: Stop trading and review all positions",
                    "Schedule risk management review",
                    "Consider temporary account restriction",
                    "Mandatory cool-down period recommended"
                ],
                requires_action=True
            )
            alerts.append(alert)
        
        return alerts
    
    def generate_alerts(self,
                       trader_id: str,
                       health_report,
                       drift_signals: List = None,
                       risk_signals: List = None) -> List[Alert]:
        """
        Generate all applicable alerts for a trader.
        
        Args:
            trader_id: Trader identifier
            health_report: HealthReport from TraderHealthScorer
            drift_signals: Optional behavioral drift signals
            risk_signals: Optional risk escalation signals
            
        Returns:
            List of all generated alerts
        """
        all_alerts = []
        
        drift_signals = drift_signals or []
        risk_signals = risk_signals or []
        
        # Health score alerts
        all_alerts.extend(
            self.evaluate_health_score(trader_id, health_report)
        )
        
        # Behavioral drift alerts
        all_alerts.extend(
            self.evaluate_behavioral_drift(trader_id, drift_signals)
        )
        
        # Risk escalation alerts
        all_alerts.extend(
            self.evaluate_risk_escalation(trader_id, risk_signals)
        )
        
        # Multi-signal alerts (most severe)
        all_alerts.extend(
            self.evaluate_multi_signal(trader_id, drift_signals, risk_signals, health_report)
        )
        
        # Store alerts
        self.alerts.extend(all_alerts)
        
        return all_alerts
    
    def get_alert_summary(self) -> Dict:
        """Get summary of all alerts."""
        if not self.alerts:
            return {
                'total_alerts': 0,
                'critical': 0,
                'warning': 0,
                'info': 0,
                'requires_action': 0
            }
        
        return {
            'total_alerts': len(self.alerts),
            'critical': sum(1 for a in self.alerts if a.severity == AlertSeverity.CRITICAL),
            'warning': sum(1 for a in self.alerts if a.severity == AlertSeverity.WARNING),
            'info': sum(1 for a in self.alerts if a.severity == AlertSeverity.INFO),
            'requires_action': sum(1 for a in self.alerts if a.requires_action)
        }
    
    def export_alerts(self, format: str = 'json') -> str:
        """Export alerts to specified format."""
        if format == 'json':
            import json
            return json.dumps([a.to_dict() for a in self.alerts], indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")


if __name__ == "__main__":
    # Example usage
    print("Alert System")
    print("=" * 60)
    
    from models.behavioral_drift import DriftSignal, DriftSeverity
    from models.risk_escalation import RiskSignal, RiskLevel
    from scoring.trader_health import HealthReport, HealthStatus
    
    # Create sample health report
    health_report = HealthReport(
        trader_id='TR001',
        health_score=35,
        status=HealthStatus.CRITICAL,
        component_scores={
            'risk_discipline': 40,
            'behavioral_stability': 25,
            'exposure_control': 30,
            'performance_consistency': 45
        },
        risk_factors=['Behavioral instability', 'Exposure issues'],
        recommendations=['Reduce size', 'Take break']
    )
    
    # Create sample drift signals
    drift_signals = [
        DriftSignal(
            metric='revenge_trading',
            current_value=250,
            baseline_value=100,
            z_score=4.5,
            severity=DriftSeverity.CRITICAL,
            message='Position size 150% larger after losses'
        )
    ]
    
    # Create sample risk signals
    risk_signals = [
        RiskSignal(
            category='drawdown',
            metric='max_drawdown',
            current_value=0.25,
            threshold=0.20,
            risk_level=RiskLevel.CRITICAL,
            message='Drawdown at 25% for 10 days'
        )
    ]
    
    # Generate alerts
    alert_system = AlertSystem()
    alerts = alert_system.generate_alerts(
        'TR001',
        health_report,
        drift_signals,
        risk_signals
    )
    
    print(f"\nGenerated {len(alerts)} alert(s):\n")
    
    for alert in alerts:
        print(f"[{alert.severity.value.upper()}] {alert.title}")
        print(f"Category: {alert.category.value}")
        print(f"Message: {alert.message}")
        print(f"Evidence:")
        for evidence in alert.evidence:
            print(f"  - {evidence}")
        print(f"Recommendations:")
        for rec in alert.recommendations[:3]:
            print(f"  - {rec}")
        print(f"Action Required: {'YES' if alert.requires_action else 'NO'}")
        print("-" * 60)
    
    summary = alert_system.get_alert_summary()
    print(f"\nAlert Summary:")
    print(f"  Total: {summary['total_alerts']}")
    print(f"  Critical: {summary['critical']}")
    print(f"  Warning: {summary['warning']}")
    print(f"  Requires Action: {summary['requires_action']}")
