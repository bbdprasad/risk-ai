# Risk Escalation Monitor

## Purpose
Detect structural risk build-up before it becomes catastrophic. This is NOT about predicting market moves—it's about detecting when a trader's risk profile is deteriorating.

---

## Core Risk Categories

### 1. Loss Acceleration
**What it detects**: Losses getting bigger and more frequent

**Method**:
- Compare recent 10-trade avg loss vs historical avg loss
- Calculate acceleration factor: `recent_loss / historical_loss`
- Flag if acceleration ≥ 1.5x

**Why it matters**: Accelerating losses indicate loss of control

**Thresholds**:
- Elevated: 1.5x acceleration
- Dangerous: 2.0x acceleration
- Critical: 3.0x+ acceleration

---

### 2. Drawdown Monitoring
**What it detects**: Account equity decline from peak

**Method**:
```python
running_max = equity.expanding().max()
drawdown = (equity - running_max) / running_max
max_drawdown = abs(drawdown.min())
```

**Why it matters**: Deep drawdowns → psychological pressure → worse decisions

**Thresholds**:
- Warning: 10% drawdown
- Dangerous: 15% drawdown
- Critical: 20%+ drawdown

---

### 3. Leverage Creep
**What it detects**: Gradual increase in effective leverage

**Method**:
```python
leverage = position_value / account_equity
recent_leverage = last_10_trades.mean()
historical_leverage = all_trades.mean()
increase_factor = recent / historical
```

**Why it matters**: High leverage amplifies losses catastrophically

**Thresholds**:
- Warning: 3x leverage
- Dangerous: 5x leverage
- Critical: 7x+ leverage

---

### 4. Correlation Risk
**What it detects**: Concentrated exposure to correlated assets

**Method**:
- Calculate Herfindahl concentration index
- `concentration = sum(weight^2)` across positions
- Check sector/asset clustering

**Why it matters**: Correlated positions = magnified drawdowns

**Thresholds**:
- Elevated: 50% concentration
- Dangerous: 70%+ concentration

---

### 5. Volatility Mismatch
**What it detects**: Trader not adjusting to volatility regime changes

**Method**:
```python
recent_volatility = recent_pnl.std()
historical_volatility = historical_pnl.std()
vol_increase = recent / historical

# Check if size adjusted
if vol_increase > 1.5 and size_change < 0.9:
    # Flag: volatility up but size not reduced
```

**Why it matters**: Market volatility ↑ but position size unchanged = disaster

---

## Risk Signal Structure

```python
RiskSignal(
    category: str,           # 'loss_acceleration', 'drawdown', etc.
    metric: str,             # Specific metric name
    current_value: float,    # Current reading
    threshold: float,        # Warning threshold
    risk_level: str,         # 'safe', 'elevated', 'dangerous', 'critical'
    message: str             # Human-readable explanation
)
```

---

## Risk Level Definitions

### Safe
- All metrics within normal ranges
- No immediate concerns
- Continue monitoring

### Elevated
- 1 risk indicator above warning threshold
- Increased monitoring recommended
- No immediate action

### Dangerous
- 2+ risk indicators elevated
- OR 1 critical indicator
- Intervention recommended

### Critical
- Multiple critical indicators
- OR extreme single indicator
- Immediate action required

---

## Real-World Scenarios

### Scenario 1: The Slow Bleed
```
Week 1: -$500 avg loss per day
Week 2: -$1,200 avg loss per day (2.4x)
Week 3: -$2,800 avg loss per day (5.6x)

→ DETECT: Loss acceleration (Dangerous → Critical)
→ ACTION: Stop trading immediately
```

### Scenario 2: Leverage Death Spiral
```
Month 1: 2.5x leverage, equity $100k
Month 2: 4.0x leverage, equity $85k (↓15%)
Month 3: 6.5x leverage, equity $68k (↓32%)

→ DETECT: Leverage creep + drawdown
→ ACTION: Force deleverage
```

### Scenario 3: Volatility Trap
```
VIX was 15 (calm) → now 35 (volatile)
Trader still using 100 contracts (unchanged)

→ DETECT: Volatility mismatch
→ ACTION: Reduce size by 50%+
```

---

## Monitoring Workflow

### Step 1: Calculate Metrics
```python
monitor = RiskEscalationMonitor()

# Run all checks
signals = monitor.monitor_all_risks(trades_df, trader_id)
```

### Step 2: Assess Overall Risk
```python
summary = monitor.get_risk_summary()

# summary = {
#   'total_signals': 3,
#   'critical': 1,
#   'dangerous': 2,
#   'overall_risk': 'critical'
# }
```

### Step 3: Take Action
```python
if summary['overall_risk'] == 'critical':
    # Immediate intervention
    send_alert()
    restrict_trading()
    schedule_review()
```

---

## Integration with Other Modules

### Feeds Into:
1. **Trader Health Score**: Risk signals lower health score
2. **Alert System**: Critical risks trigger immediate alerts
3. **Dashboard**: Visual risk heatmaps

### Receives From:
1. **Feature Engine**: Computed metrics
2. **Trade Data**: Raw trade information
3. **Market Data**: Volatility indicators (optional)

---

## False Positive Prevention

### 1. Minimum Data
- Need 20+ trades for loss acceleration
- Need 30+ trades for volatility analysis

### 2. Context Awareness
- Compare to trader's own history (not others)
- Account for strategy changes
- Consider market regime

### 3. Multi-Factor Validation
- Single elevated metric ≠ alert
- Need multiple signals OR critical single signal

---

## Performance Requirements

### Latency
- <2 seconds per trader analysis
- Real-time monitoring for active traders

### Accuracy
- >90% detection of critical risk scenarios
- <10% false positive rate on dangerous alerts

---

## Calibration

### Per-Firm Tuning
Different firms have different risk tolerances:

**Conservative Prop Firm**:
- Drawdown warning: 5%
- Leverage limit: 2x

**Aggressive Hedge Fund**:
- Drawdown warning: 15%
- Leverage limit: 5x

**System allows custom thresholds**

---

## Alert Priority

Risk escalation signals are **HIGH PRIORITY** in alert system:

1. Critical risk signal → Immediate alert
2. Multiple dangerous signals → Warning alert
3. Single elevated signal → Log only

---

## Validation Tests

The system must pass these simulations:

✅ **Test 1**: Detect 2x loss acceleration
✅ **Test 2**: Detect 20% drawdown
✅ **Test 3**: Detect leverage >5x
✅ **Test 4**: Detect concentrated positions
✅ **Test 5**: Detect volatility mismatch

---

## Future Enhancements

1. **Correlation Matrix**: Actual correlation calculation between positions
2. **Sector Risk**: Map symbols to sectors
3. **Greeks Analysis**: Options exposure (delta, gamma, vega)
4. **VAR Calculation**: Value at Risk estimation
5. **Stress Testing**: What-if scenarios

---

## References

- Risk Management Frameworks
- Basel III Capital Requirements
- Hedge Fund Risk Management
- Behavioral Risk Literature
