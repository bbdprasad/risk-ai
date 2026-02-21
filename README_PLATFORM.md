# AI Trader Risk & Behavior Intelligence Platform

## 🎯 **What This Is**

A **blow-up prevention system** for proprietary trading firms. Not trading predictions—behavioral risk detection.

### We Detect:
- ✅ Revenge trading (**increases size after losses**)
- ✅ Overconfidence (**increases size after wins**)
- ✅ Risk creep (**gradual leverage increases**)
- ✅ Loss acceleration (**losses getting bigger**)
- ✅ Behavioral drift (**deviation from trader's patterns**)

### We Provide:
- 🔴 **Critical alerts** for immediate intervention
- 📊 **Trader health scores** (0-100)
- 📈 **Risk escalation monitoring**
- 🎯 **Actionable recommendations**

---

## 🏗️ **System Architecture**

```
Trade Data → 4 Core Modules → Alert Generation → Dashboard
```

### The 4 Core Modules:

#### 1. **Behavioral Drift Detection** (`models/behavioral_drift.py`)
Detects deviation from trader's historical patterns:
- Position size changes
- Frequency shifts
- **Revenge trading** (size ↑ after losses)
- **Overconfidence** (size ↑ after wins)

#### 2. **Risk Escalation Monitor** (`models/risk_escalation.py`)
Detects structural risk build-up:
- Loss acceleration
- Drawdown depth & duration
- Leverage creep
- Correlation risk
- Volatility mismatch

#### 3. **Trader Health Score** (`scoring/trader_health.py`)
Composite score (0-100) from 4 components:
- Risk discipline (30%)
- Behavioral stability (30%)
- Exposure control (20%)
- Performance consistency (20%)

#### 4. **Alert System** (`alerts/alert_system.py`)
Generates rare, high-signal alerts:
- **CRITICAL**: Immediate action required
- **WARNING**: Supervision recommended
- **INFO**: Log for monitoring

**Alert triggers**:
- 3+ anomaly signals fire simultaneously
- OR critical risk indicator detected
- OR health score < 40

---

## 🚀 **Quick Start**

### Installation

```bash
# Clone repository
cd risk_ai

# Install dependencies
pip install -r requirements.txt
```

### Run Analysis

#### With Simulated Data (Recommended for testing):
```bash
python platform_main.py --simulate --traders 20 --days 60
```

#### With Your Own Data:
```bash
python platform_main.py --data path/to/your/trades.csv
```

### Expected Output:
```
=============================================================
RISK INTELLIGENCE REPORT
=============================================================

OVERVIEW
Total Traders Analyzed: 20
Traders with Alerts: 6 (30.0%)
Critical Risk Traders: 3
Immediate Action Required: 3

⚠️  CRITICAL RISK TRADERS - IMMEDIATE ATTENTION
  
[CRITICAL] SIM005
  Health Score: 28.4/100
  → Revenge Trading Detected
  → Multiple Risk Indicators - High Blow-Up Risk
```

---

## 📊 **Required Data Format**

Your trade data must have these columns:

```csv
trade_id,trader_id,timestamp,symbol,side,quantity,price,entry_price,exit_price,pnl,account_equity
T001,TR001,2026-01-01 09:30:00,AAPL,long,100,175.50,175.50,176.00,50,100500
```

### Required Fields:

| Field | Type | Description |
|-------|------|-------------|
| `trade_id` | str | Unique trade identifier |
| `trader_id` | str | Trader identifier |
| `timestamp` | datetime | Trade execution time |
| `symbol` | str | Asset traded |
| `side` | str | 'long' or 'short' |
| `quantity` | float | Position size |
| `price` | float | Trade price |
| `entry_price` | float | Entry price |
| `exit_price` | float | Exit price |
| `pnl` | float | Realized P&L |
| `account_equity` | float | Account value after trade |

---

## 🧪 **Testing with Simulations**

The system includes 5 behavioral trader types:

### 1. **Disciplined Trader** (50% - Healthy baseline)
- Consistent sizing
- Respects stops
- Stable win rate
- **Expected**: ✅ Healthy score (80-100)

### 2. **Revenge Trader** (20% - CRITICAL)
- Increases size after losses
- Chasing behavior
- **Expected**: 🔴 Critical alerts for revenge trading

### 3. **Overconfident Trader** (15% - Warning)
- Increases size after win streaks
- Takes excessive risk
- **Expected**: ⚠️ Warning alerts for overconfidence

### 4. **Risk Creep Trader** (10% - Warning)
- Gradual leverage increase
- Slow position size growth
- **Expected**: ⚠️ Alerts for leverage creep

### 5. **Erratic Trader** (5% - Warning)
- Highly variable behavior
- Inconsistent patterns
- **Expected**: ⚠️ Behavioral instability alerts

### Generate Test Data:

```bash
# Generate 20 traders, 60 days of trading
python platform_main.py --simulate --traders 20 --days 60
```

### Validation:
✅ System should detect 100% of revenge traders  
✅ System should detect 90%+ of risk creep traders  
✅ System should flag <10% of disciplined traders  

---

## 📈 **Health Score Interpretation**

### 🟢 **Healthy (80-100)**
- All metrics within normal ranges
- No behavioral concerns
- **Action**: Continue monitoring

### 🟡 **Caution (60-79)**
- Minor deviations detected
- Increased monitoring recommended
- **Action**: Watch closely

### 🟠 **Warning (40-59)**
- Significant issues present
- Intervention recommended
- **Action**: Supervisor review + position size reduction

### 🔴 **Critical (0-39)**
- Multiple risk factors
- High blow-up probability
- **Action**: IMMEDIATE intervention, possible trading suspension

---

## 🚨 **Alert Types**

### Critical Alerts (Immediate Action):
1. **Revenge Trading Detected**
   - Trader increasing size after losses
   - High blow-up risk
   
2. **Multiple Risk Indicators**
   - 3+ signals firing simultaneously
   - Structural risk break
   
3. **Critical Drawdown**
   - Account down >20%
   - Sustained losses

### Warning Alerts (Supervision):
1. **Behavioral Drift**
   - Pattern deviation from baseline
   
2. **Elevated Risk**
   - 2+ risk escalation signals
   
3. **Health Decline**
   - Score dropping below 60

---

## 🛠️ **Command Line Options**

```bash
python platform_main.py [options]
```

### Options:

| Flag | Description | Default |
|------|-------------|---------|
| `--data PATH` | Path to trade data CSV | `data/sample_trades.csv` |
| `--simulate` | Generate simulated data | False |
| `--traders N` | Number of traders to simulate | 20 |
| `--days N` | Trading days to simulate | 60 |
| `--output DIR` | Output directory for results | `data` |

### Examples:

```bash
# Analyze existing data
python platform_main.py --data trades.csv

# Generate and analyze 50 traders over 90 days
python platform_main.py --simulate --traders 50 --days 90

# Save results to specific directory
python platform_main.py --simulate --output results/
```

---

## 📁 **Project Structure**

```
risk_ai/
├── models/                      # Risk detection models
│   ├── behavioral_drift.py      # Behavioral pattern detection
│   ├── risk_escalation.py       # Risk build-up monitoring
│   └── anomaly_detection.py     # Statistical anomaly detection
│
├── scoring/                     # Risk scoring
│   ├── trader_health.py         # Health score calculation
│   └── risk_score.py            # Legacy risk scoring
│
├── alerts/                      # Alert system
│   └── alert_system.py          # Alert generation & management
│
├── simulation/                  # Data generation
│   ├── behavioral_simulator.py  # Behavioral trader simulation
│   └── generate_fake_traders.py # Legacy trader generation
│
├── docs/                        # Documentation
│   ├── BEHAVIORAL_DRIFT.md      # Drift detection explained
│   └── RISK_ESCALATION.md       # Risk monitoring explained
│
├── data/                        # Data directory
│   ├── sample_trades.csv        # Sample data
│   └── simulated_traders.csv    # Generated simulations
│
├── platform_main.py             # ⭐ MAIN PLATFORM ENTRY POINT
├── main.py                      # Legacy pipeline
├── ARCHITECTURE.md              # System architecture
├── AI_Trader_Risk_Platform.md   # Product vision
└── README_PLATFORM.md           # This file
```

---

## 🔬 **How It Works**

### Analysis Pipeline:

```
1. Load Trade Data
   ↓
2. For Each Trader:
   ├─→ Behavioral Drift Detection
   ├─→ Risk Escalation Monitoring  
   ├─→ Health Score Calculation
   └─→ Alert Generation (if needed)
   ↓
3. Generate Report
   ↓
4. Export Results (CSV + JSON)
```

### Example: Detecting Revenge Trading

```python
# Trader has recent losses
trades[-5:] → all negative P&L

# System checks: is position size increasing?
avg_size_after_loss = 250
avg_normal_size = 100

# Calculate increase
increase_ratio = 250 / 100 = 2.5x

# Flag if ratio > 1.3
if increase_ratio > 1.3:
    ALERT: "Revenge Trading Detected"
    SEVERITY: CRITICAL
    ACTION: "Reduce position sizes immediately"
```

---

## 💼 **Use Cases**

### Prop Trading Firm
**Problem**: Traders blow up accounts, lose firm capital  
**Solution**: Early detection of revenge trading & risk escalation  
**Result**: Prevent blow-ups before they happen

### Hedge Fund Risk Management
**Problem**: Need to monitor 50+ traders daily  
**Solution**: Automated health scoring & rare high-signal alerts  
**Result**: Focus attention on high-risk traders only

### Trader Education
**Problem**: Junior traders lack risk awareness  
**Solution**: Real-time feedback on behavioral patterns  
**Result**: Faster learning, better risk discipline

---

## 📊 **Performance Metrics**

### System Targets:
- ✅ **Detection Rate**: >85% of critical behaviors
- ✅ **False Positive Rate**: <10% of alerts
- ✅ **Alert Rate**: <5% of traders flagged daily
- ✅ **Latency**: <5 seconds per trader analysis

### Validated Against:
- Simulated revenge traders
- Simulated risk creep patterns
- Simulated overconfidence behavior
- Normal variance baseline

---

## 🔒 **Compliance & Legal**

### What We ARE:
- ✅ Risk analytics software
- ✅ Behavioral monitoring tool
- ✅ Decision support system

### What We ARE NOT:
- ❌ Providing financial advice
- ❌ Generating buy/sell signals
- ❌ Managing capital
- ❌ Regulated investment advisor

**Positioning**: Risk analytics SaaS—clearer regulatory path

---

## 💰 **Pricing Strategy**

### Pilot Program:
- **$1,500/month** per firm
- Up to 10 traders
- Basic support

### Full Integration:
- **$3,000-8,000/month** per firm
- Unlimited traders
- Premium support
- Custom thresholds

### Enterprise:
- Custom pricing
- Multi-firm deployments
- White-label options
- API access

---

## 🚀 **Roadmap**

### ✅ Phase 1 - MVP (Complete)
- ✅ Behavioral drift detection
- ✅ Risk escalation monitoring
- ✅ Health score calculation
- ✅ Alert system
- ✅ Simulated data validation

### 🔄 Phase 2 - Current (In Progress)
- Dashboard UI (Streamlit)
- Real-time monitoring
- Historical trend analysis
- PDF report generation

### 📋 Phase 3 - Future
- Multi-firm SaaS platform
- API endpoints
- Webhook integrations
- Custom alerting (Slack, email)
- Advanced ML models

---

## 📞 **Support & Contact**

### Documentation:
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [BEHAVIORAL_DRIFT.md](docs/BEHAVIORAL_DRIFT.md) - Drift detection
- [RISK_ESCALATION.md](docs/RISK_ESCALATION.md) - Risk monitoring

### Issues:
- Report bugs via GitHub Issues
- Feature requests welcome

---

## 🏆 **The Moat**

Long-term defensibility:

### 1. **Proprietary Data**
- Behavioral patterns across traders
- Risk thresholds per firm
- Historical blow-up signatures

### 2. **Domain Expertise**
- Trading psychology integration
- Risk management frameworks
- Firm-specific customization

### 3. **Network Effects**
- More traders → better detection
- More firms → better benchmarking
- More data → better models

### 4. **Integration Depth**
Once embedded in firm workflow → difficult to replace

---

## ⚡ **Quick Start Examples**

### Example 1: Basic Analysis
```bash
python platform_main.py --data your_trades.csv
```

### Example 2: Test with Simulations
```bash
python platform_main.py --simulate --traders 30 --days 60
```

### Example 3: Production Run
```bash
python platform_main.py \
  --data production_trades.csv \
  --output reports/$(date +%Y%m%d)
```

---

## 📈 **Success Metrics**

### Product KPIs:
- Blow-ups prevented
- Early warning accuracy
- Alert relevance (low false positives)
- Time to detection

### Business KPIs:
- Firms using platform
- Monthly recurring revenue
- Customer retention
- Net promoter score

---

## 🎓 **Next Steps**

1. **Try it**: Run with simulated data
2. **Test it**: Use your firm's historical data
3. **Validate it**: Check if it catches known blow-ups
4. **Deploy it**: Integrate into monitoring workflow
5. **Scale it**: Add more traders & firms

---

**Built for prop firms. Built to prevent blow-ups. Built to save capital.**

🚀 **Start preventing blow-ups today.**
