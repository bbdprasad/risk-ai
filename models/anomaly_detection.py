"""
Anomaly Detection Module for Risk AI
Detects unusual trading patterns and behaviors using multiple techniques.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.covariance import EllipticEnvelope

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Multi-method anomaly detection for trading behavior analysis.
    """
    
    def __init__(self, contamination: float = 0.1):
        """
        Initialize anomaly detector.
        
        Args:
            contamination: Expected proportion of anomalies (default: 10%)
        """
        self.contamination = contamination
        self.scaler = StandardScaler()
        self.models = {}
        self.feature_columns = []
        
    def prepare_data(self, df: pd.DataFrame, feature_columns: List[str]) -> np.ndarray:
        """
        Prepare and normalize data for anomaly detection.
        
        Args:
            df: DataFrame with features
            feature_columns: List of column names to use as features
            
        Returns:
            Normalized feature array
        """
        self.feature_columns = feature_columns
        
        # Handle missing values
        df_clean = df[feature_columns].fillna(df[feature_columns].median())
        
        # Normalize features
        X = self.scaler.fit_transform(df_clean)
        
        return X
    
    def fit_isolation_forest(self, X: np.ndarray) -> None:
        """
        Fit Isolation Forest model.
        
        Isolation Forest works by randomly partitioning data and 
        identifying anomalies as points that are isolated quickly.
        """
        model = IsolationForest(
            contamination=self.contamination,
            random_state=42,
            n_estimators=100
        )
        model.fit(X)
        self.models['isolation_forest'] = model
        
    def fit_elliptic_envelope(self, X: np.ndarray) -> None:
        """
        Fit Elliptic Envelope (Gaussian) model.
        
        Assumes features follow a Gaussian distribution and 
        detects outliers based on Mahalanobis distance.
        """
        model = EllipticEnvelope(
            contamination=self.contamination,
            random_state=42
        )
        model.fit(X)
        self.models['elliptic_envelope'] = model
        
    def statistical_outlier_detection(self, X: np.ndarray, 
                                     threshold: float = 3.0) -> np.ndarray:
        """
        Detect outliers using statistical methods (Z-score).
        
        Args:
            X: Feature array
            threshold: Number of standard deviations for outlier threshold
            
        Returns:
            Array of anomaly predictions (-1 for anomaly, 1 for normal)
        """
        # Calculate Z-scores
        z_scores = np.abs((X - X.mean(axis=0)) / X.std(axis=0))
        
        # Flag as anomaly if any feature exceeds threshold
        is_outlier = (z_scores > threshold).any(axis=1)
        
        # Convert to sklearn convention: -1 for anomaly, 1 for normal
        predictions = np.where(is_outlier, -1, 1)
        
        return predictions
    
    def fit_all_models(self, X: np.ndarray) -> None:
        """Fit all anomaly detection models."""
        logger.info("Fitting Isolation Forest...")
        self.fit_isolation_forest(X)

        logger.info("Fitting Elliptic Envelope...")
        self.fit_elliptic_envelope(X)

        logger.info("All models fitted successfully.")
    
    def predict(self, X: np.ndarray, method: str = 'ensemble') -> np.ndarray:
        """
        Predict anomalies using specified method.
        
        Args:
            X: Feature array
            method: Detection method ('isolation_forest', 'elliptic_envelope', 
                   'statistical', or 'ensemble')
                   
        Returns:
            Array of predictions (-1 for anomaly, 1 for normal)
        """
        if method == 'ensemble':
            return self._ensemble_predict(X)
        elif method == 'statistical':
            return self.statistical_outlier_detection(X)
        elif method in self.models:
            return self.models[method].predict(X)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def _ensemble_predict(self, X: np.ndarray) -> np.ndarray:
        """
        Ensemble prediction using voting from all models.
        
        Args:
            X: Feature array
            
        Returns:
            Array of predictions (-1 for anomaly, 1 for normal)
        """
        predictions = []
        
        # Get predictions from all models
        if 'isolation_forest' in self.models:
            predictions.append(self.models['isolation_forest'].predict(X))
        
        if 'elliptic_envelope' in self.models:
            predictions.append(self.models['elliptic_envelope'].predict(X))
        
        # Statistical method
        predictions.append(self.statistical_outlier_detection(X))
        
        # Stack predictions and use majority voting
        predictions = np.array(predictions)
        
        # Majority vote: -1 if at least 2 models predict anomaly
        ensemble_pred = np.where(
            (predictions == -1).sum(axis=0) >= 2, -1, 1
        )
        
        return ensemble_pred
    
    def get_anomaly_scores(self, X: np.ndarray, 
                          method: str = 'isolation_forest') -> np.ndarray:
        """
        Get anomaly scores (not binary predictions).
        
        Higher absolute scores indicate more anomalous behavior.
        
        Args:
            X: Feature array
            method: Model to use for scoring
            
        Returns:
            Array of anomaly scores
        """
        if method == 'isolation_forest' and method in self.models:
            # Negative score_samples for Isolation Forest
            return -self.models[method].score_samples(X)
        elif method == 'elliptic_envelope' and method in self.models:
            return -self.models[method].score_samples(X)
        else:
            raise ValueError(f"Scoring not available for method: {method}")
    
    def detect_anomalies(self, df: pd.DataFrame, 
                        feature_columns: List[str],
                        method: str = 'ensemble') -> pd.DataFrame:
        """
        Complete anomaly detection pipeline.
        
        Args:
            df: DataFrame with features
            feature_columns: List of columns to use
            method: Detection method
            
        Returns:
            DataFrame with anomaly predictions and scores
        """
        # Prepare data
        X = self.prepare_data(df, feature_columns)
        
        # Fit models if not already fitted
        if not self.models:
            self.fit_all_models(X)
        
        # Predict anomalies
        predictions = self.predict(X, method=method)
        
        # Get anomaly scores
        try:
            scores = self.get_anomaly_scores(X, method='isolation_forest')
        except Exception:
            scores = np.zeros(len(predictions))
        
        # Add results to dataframe
        result_df = df.copy()
        result_df['is_anomaly'] = (predictions == -1).astype(int)
        result_df['anomaly_score'] = scores
        
        return result_df
    
    def get_anomaly_summary(self, df: pd.DataFrame) -> Dict:
        """
        Generate summary statistics for detected anomalies.
        
        Args:
            df: DataFrame with 'is_anomaly' column
            
        Returns:
            Dictionary with summary statistics
        """
        total = len(df)
        anomalies = df['is_anomaly'].sum()
        
        summary = {
            'total_records': total,
            'total_anomalies': anomalies,
            'anomaly_rate': anomalies / total if total > 0 else 0,
            'normal_records': total - anomalies
        }
        
        return summary


if __name__ == "__main__":
    # Example usage
    print("Anomaly Detection Module")
    print("=" * 50)
    
    # Create sample data
    np.random.seed(42)
    n_samples = 100
    
    # Generate normal data
    X_normal = np.random.randn(n_samples, 5)
    
    # Add some anomalies
    X_anomalies = np.random.randn(10, 5) * 3 + 5
    X = np.vstack([X_normal, X_anomalies])
    
    # Create DataFrame
    df = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(5)])
    
    # Detect anomalies
    detector = AnomalyDetector(contamination=0.1)
    result_df = detector.detect_anomalies(
        df, 
        feature_columns=[f'feature_{i}' for i in range(5)],
        method='ensemble'
    )
    
    # Print summary
    summary = detector.get_anomaly_summary(result_df)
    print("\nAnomaly Detection Summary:")
    print(f"Total records: {summary['total_records']}")
    print(f"Anomalies detected: {summary['total_anomalies']}")
    print(f"Anomaly rate: {summary['anomaly_rate']:.2%}")
    
    print("\nTop 5 anomalies by score:")
    print(result_df.nlargest(5, 'anomaly_score')[['anomaly_score', 'is_anomaly']])
