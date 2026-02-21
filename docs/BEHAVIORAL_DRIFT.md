# Behavioral Drift Detection

## Purpose
Detect when a trader deviates from their historical patterns, which often precedes blow-ups.

## Key Concept
Every trader has their own "normal" behavior. We detect drift from **their baseline**, not from other traders.

---

## Detected Patterns

### 1. Position Size Drift
**What it detects**: Trader increasing or decreasing position sizes vs their historical average

**Method**:
- Compute rolling baselines (5d, 20d, 60d windows)
- Calculate Z-score: `(current_size - baseline_mean) / baseline_std`
- Flag if |Z| > 2.0 (warning) or > 3.0 (critical)

**Why it matters**: Gradual size increases often precede blow-ups

---

### 2. Trade Frequency Changes
**What it detects**: Sudden increase or decrease in trading frequency

**Method**:
- Track daily trade counts
- Compare recent 5-day average to 20-60 day baseline
- Flag significant deviation

**Why it matters**: 
- Increased frequency → Overtrading, desperation
- Decreased frequency → Loss of confidence

---

### 3. Revenge Trading
**What it detects**: Position size increases after losses

**Method**:
- Compare avg size after losses vs avg size after wins
- Flag if size is >30% larger after losses

**Why it matters**: Classic psychological trap leading to account blow-ups

**Signal**: CRITICAL priority

---

### 4. Overconfidence
**What it detects**: Position size increases after winning streaks

**Method**:
- Detect 2+ consecutive wins
- Check if next position is >40% larger than average

**Why it matters**: Overconfidence leads to oversizing and eventual large loss

---

## Statistical Framework

### Z-Score Calculation
```
Z = (current_value - baseline_mean) / baseline_std
```

### Thresholds
- **Normal**: |Z| < 2.0 (within 2 standard deviations)
- **Warning**: 2.0 ≤ |Z| < 3.0
- **Critical**: |Z| ≥ 3.0

### Rolling Windows
- **5-day**: Recent behavior
- **20-day**: Medium-term (monthly cycle)
- **60-day**: Long-term baseline

---

## Output

### DriftSignal Object
```python
{
    'metric': str,              # e.g., 'position_size', 'revenge_trading'
    'current_value': float,     # Current metric value
    'baseline_value': float,    # Historical baseline
    'z_score': float,           # Deviation score
    'severity': str,            # 'normal', 'warning', 'critical'
    'message': str              # Human-readable explanation
}
```

---

## Usage Example

```python
from models.behavioral_drift import BehavioralDriftDetector

# Initialize
detector = BehavioralDriftDetector(
    z_warning=2.0,
    z_critical=3.0
)

# Detect all drift signals
signals = detector.detect_all_drift_signals(trades_df, 'TR001')

# Check for critical issues
critical = [s for s in signals if s.severity == 'critical']
if critical:
    print("⚠️ CRITICAL DRIFT DETECTED")
    for signal in critical:
        print(signal.message)
```

---

## Real-World Scenarios

### Scenario 1: Gradual Position Size Creep
```
Day 1-30:  Avg size = 100 contracts
Day 31-40: Avg size = 150 contracts (↑50%)
Day 41-45: Avg size = 250 contracts (↑150%)

→ DETECT: Position size drift (Z=3.5) → CRITICAL
```

### Scenario 2: Revenge Trading Pattern
```
Trade 1: Loss $500, next size = 100
Trade 2: Loss $800, next size = 150 (+50%)
Trade 3: Loss $600, next size = 200 (+100%)

→ DETECT: Revenge trading → CRITICAL
```

### Scenario 3: Win Streak Overconfidence
```
Trade 1: Win $200
Trade 2: Win $300
Trade 3: Size increases to 300 (3x normal)

→ DETECT: Overconfidence → WARNING/CRITICAL
```

---

## False Positive Mitigation

### 1. Minimum Data Requirement
- Need at least 10 trades for detection
- Need at least 20 trades for frequency analysis

### 2. Baseline Stability
- Exclude first 10 trades from baseline
- Use 60-day window for stable baseline

### 3. Context Matters
- Large size after loss ≠ always bad
- Could be based on better setup
- Alert allows human judgment

---

## Integration Points

### Input
- Trade history DataFrame with:
  - `trader_id`
  - `timestamp`
  - `quantity`
  - `pnl`

### Output
- List of `DriftSignal` objects
- Summary statistics
- Integration with Alert System

---

## Performance Metrics

### Target Performance
- **Detection Rate**: >85% of revenge trading patterns
- **False Positive Rate**: <15%
- **Latency**: <1 second per trader

### Validation
Test against simulated trader behaviors:
- ✅ Detects revenge trading
- ✅ Detects position creep
- ✅ Detects overconfidence
- ✅ Ignores normal variance

---

## Next Steps

1. Add change-point detection (structural breaks)
2. Implement CUSUM algorithm for drift detection
3. Add pattern matching for specific behaviors
4. Machine learning enhancement (optional)

---

## References

- Statistical Process Control (SPC)
- CUSUM Charts
- EWMA Control Charts
- Behavioral Finance Research
