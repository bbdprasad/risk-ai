# risk-ai

# Risk AI - Trading Behavior Risk Analysis System

A comprehensive machine learning system for detecting anomalous trading behavior and calculating risk scores for traders.

## Features

- **Feature Engineering**: Extract meaningful features from trading data
- **Anomaly Detection**: Multiple methods including Isolation Forest, Elliptic Envelope, and statistical outliers
- **Risk Scoring**: Comprehensive risk assessment with weighted components
- **Data Generation**: Synthetic trader and trade data generation for testing
- **End-to-End Pipeline**: Complete automated risk analysis workflow

## Project Structure

```
risk_ai/
│
├── data/                           # Data directory
│   └── sample_trades.csv          # Sample trade data
│
├── features/                       # Feature engineering
│   └── feature_engine.py          # Extract and transform features
│
├── models/                         # Machine learning models
│   └── anomaly_detection.py       # Anomaly detection algorithms
│
├── scoring/                        # Risk scoring
│   └── risk_score.py              # Calculate risk scores
│
├── simulation/                     # Data generation
│   └── generate_fake_traders.py   # Generate synthetic data
│
├── main.py                         # Main application entry point
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## Installation

1. Clone or download this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Quick Start

### Run with sample data

```bash
python main.py
```

### Generate and analyze synthetic data

```bash
python main.py --generate --traders 50 --days 30
```

### Specify custom data file

```bash
python main.py --data path/to/your/trades.csv
```

## Usage

### Command Line Options

```bash
python main.py [options]
```

**Options:**
- `--data PATH`: Path to trade data CSV file (default: `data/sample_trades.csv`)
- `--generate`: Generate sample data before analysis
- `--traders N`: Number of traders to generate (default: 30)
- `--days N`: Number of days to simulate (default: 14)
- `--method METHOD`: Anomaly detection method (default: `ensemble`)
  - `ensemble`: Voting from multiple methods
  - `isolation_forest`: Isolation Forest algorithm
  - `elliptic_envelope`: Gaussian outlier detection
  - `statistical`: Z-score based detection
- `--contamination FLOAT`: Expected proportion of anomalies (default: 0.1)
- `--output PATH`: Path to save results (default: `data/risk_analysis_results.csv`)
- `--top N`: Number of top risk traders to display (default: 10)

### Examples

**Generate 100 traders over 60 days and analyze:**
```bash
python main.py --generate --traders 100 --days 60 --method ensemble --top 20
```

**Analyze existing data with specific method:**
```bash
python main.py --data data/my_trades.csv --method isolation_forest --contamination 0.15
```

## Input Data Format

Trade data should be a CSV file with the following columns:

| Column | Type | Description |
|--------|------|-------------|
| `trade_id` | string | Unique trade identifier |
| `trader_id` | string | Unique trader identifier |
| `timestamp` | datetime | Trade timestamp |
| `asset` | string | Asset/security symbol |
| `quantity` | int | Number of units traded |
| `price` | float | Price per unit |
| `trade_type` | string | BUY or SELL |
| `market` | string | Trading market |
| `region` | string | Geographic region |
| `trader_experience` | int | Years of experience |

## Risk Scoring Components

The system calculates risk scores based on five weighted components:

1. **Volume Risk (20%)**: Based on total trading volume
2. **Volatility Risk (25%)**: Based on price and trade size volatility
3. **Concentration Risk (20%)**: Based on asset diversification
4. **Anomaly Risk (25%)**: Based on anomaly detection results
5. **Experience Risk (10%)**: Based on trader experience level

**Risk Levels:**
- **Low Risk**: Score < 30
- **Medium Risk**: Score 30-60
- **High Risk**: Score 60-85
- **Critical Risk**: Score > 85

## Module Usage

### Feature Engine

```python
from features.feature_engine import FeatureEngine

engine = FeatureEngine()
trades_df, trader_features = engine.generate_all_features("data/trades.csv")
```

### Anomaly Detection

```python
from models.anomaly_detection import AnomalyDetector

detector = AnomalyDetector(contamination=0.1)
results = detector.detect_anomalies(
    trader_features,
    feature_columns=['total_volume', 'avg_trade_size'],
    method='ensemble'
)
```

### Risk Scoring

```python
from scoring.risk_score import RiskScorer

scorer = RiskScorer()
results = scorer.calculate_composite_risk_score(trader_features)
results = scorer.assign_risk_level(results)
report = scorer.generate_risk_report(results)
```

### Data Generation

```python
from simulation.generate_fake_traders import FakeTraderGenerator

generator = FakeTraderGenerator(seed=42)
traders_df, trades_df = generator.generate_dataset(
    n_traders=50,
    n_days=30,
    trades_per_day_range=(2, 8)
)
```

## Output

The pipeline generates:

1. **Console Report**: Summary statistics and top risk traders
2. **CSV Results**: Complete results with risk scores and classifications
3. **Risk Distribution**: Breakdown by risk level

Sample output:
```
============================================================
RISK ASSESSMENT REPORT
============================================================

Total Traders Analyzed: 30
Average Risk Score: 45.23
Risk Score Range: 12.34 - 89.56
Standard Deviation: 18.92

Risk Level Distribution:
  Low Risk: 8 (26.7%)
  Medium Risk: 15 (50.0%)
  High Risk: 5 (16.7%)
  Critical Risk: 2 (6.7%)
```

## Anomaly Detection Methods

### Ensemble (Recommended)
Combines multiple methods using majority voting for robust detection.

### Isolation Forest
Fast, tree-based method that isolates anomalies by random partitioning.

### Elliptic Envelope
Assumes Gaussian distribution and detects outliers using Mahalanobis distance.

### Statistical
Z-score based method using standard deviation thresholds.

## Performance Considerations

- **Small datasets** (< 100 traders): All methods perform well
- **Large datasets** (> 1000 traders): Isolation Forest is fastest
- **Highly dimensional data**: Consider using PCA for preprocessing
- **Real-time monitoring**: Use Isolation Forest with pre-fitted model

## Requirements

- Python 3.7+
- pandas
- numpy
- scikit-learn

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Support

For questions or issues, please open an issue on the repository.

---

**Note**: This system is designed for educational and demonstration purposes. For production use in financial environments, additional validation, testing, and regulatory compliance measures are required.
