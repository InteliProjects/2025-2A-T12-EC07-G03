import pickle
import os
import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime
from typing import Dict, List, Union, Optional, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelLoader:
    """Handles model loading operations."""
    
    @staticmethod
    def load_model(model_path: str) -> Any:
        """Load a pickled model from file.
        
        Args:
            model_path: Path to the model file.
            
        Returns:
            Loaded model object.
            
        Raises:
            FileNotFoundError: If model file doesn't exist.
            Exception: If model loading fails.
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at: {model_path}")
        
        try:
            with open(model_path, 'rb') as file:
                model = pickle.load(file)
            logger.info(f"Model loaded successfully from: {model_path}")
            return model
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise


class FeatureManager:
    """Manages feature information and preprocessing."""
    
    EXPECTED_FEATURES = [
        'Auto', 'Bat_V', 'Char_V', 'Cool_T', 'Eng_RPM', 'Fuel_Con', 'Fuel_L', 'Man',
        'Oil_L', 'Oil_P', 'Recalque', 'Starts_N', 'Stop', 'Succao', 'running',
        'minutes_running', 'Bat_V_variation', 'Char_V_variation', 'Cool_T_variation',
        'Eng_RPM_variation', 'Fuel_Con_variation', 'Fuel_L_variation', 'Oil_L_variation',
        'Oil_P_variation', 'Bat_V_variation_percentage', 'Char_V_variation_percentage',
        'Cool_T_variation_percentage', 'Eng_RPM_variation_percentage', 'Fuel_Con_variation_percentage',
        'Fuel_L_variation_percentage', 'Oil_L_variation_percentage', 'Oil_P_variation_percentage',
        'Hydraulic_Head', 'Head_per_RPM', 'Head_trend_per_minutes', 'OilP_per_RPM',
        'CoolT_per_RPM', 'Fuel_rate', 'Fuel_efficiency'
    ]
    
    EXCLUDED_COLUMNS = ['timestamp', 'motor_pump']
    
    @classmethod
    def get_expected_features(cls, model: Any) -> List[str]:
        """Get expected features from model or return default list.
        
        Args:
            model: The loaded model object.
            
        Returns:
            List of expected feature names.
        """
        if hasattr(model, 'feature_names_in_'):
            return list(model.feature_names_in_)
        elif hasattr(model, 'get_booster') and model.get_booster().feature_names:
            return list(model.get_booster().feature_names)
        else:
            return cls.EXPECTED_FEATURES
    
    @classmethod
    def get_feature_count(cls, model: Any) -> Optional[int]:
        """Get number of features from model.
        
        Args:
            model: The loaded model object.
            
        Returns:
            Number of features or None if not available.
        """
        if hasattr(model, 'n_features_in_'):
            return model.n_features_in_
        elif hasattr(model, 'num_feature'):
            return model.num_feature
        return None


class DataProcessor:
    """Handles data preprocessing operations."""
    
    def __init__(self, feature_manager: FeatureManager):
        self.feature_manager = feature_manager
    
    def preprocess_json_data(self, json_data: Union[str, Dict, List], expected_features: List[str]) -> pd.DataFrame:
        """Process JSON data for model prediction.
        
        Args:
            json_data: Input data in JSON format.
            expected_features: List of expected feature names.
            
        Returns:
            Preprocessed DataFrame ready for prediction.
            
        Raises:
            ValueError: If data processing fails.
        """
        try:
            data = self._parse_json_data(json_data)
            df = pd.DataFrame(data)
            df = self._remove_excluded_columns(df)
            df = self._align_features(df, expected_features)
            df = self._convert_data_types(df)
            
            logger.info(f"Data preprocessed successfully: {len(df)} samples, {len(df.columns)} features")
            return df
            
        except Exception as e:
            logger.error(f"Error preprocessing data: {str(e)}")
            raise ValueError(f"Data preprocessing failed: {str(e)}")
    
    def _parse_json_data(self, json_data: Union[str, Dict, List]) -> List[Dict]:
        """Parse JSON data to list of dictionaries."""
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data
        
        if isinstance(data, dict):
            data = [data]
        
        return data
    
    def _remove_excluded_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove excluded columns from DataFrame."""
        for col in self.feature_manager.EXCLUDED_COLUMNS:
            if col in df.columns:
                df = df.drop(columns=[col])
                logger.info(f"Removed column: {col}")
        return df
    
    def _align_features(self, df: pd.DataFrame, expected_features: List[str]) -> pd.DataFrame:
        """Align DataFrame features with expected features."""
        missing_features = set(expected_features) - set(df.columns)
        extra_features = set(df.columns) - set(expected_features)
        
        if missing_features:
            logger.warning(f"Missing features filled with 0.0: {missing_features}")
            for feature in missing_features:
                df[feature] = 0.0
        
        if extra_features:
            logger.warning(f"Extra features removed: {extra_features}")
            df = df.drop(columns=list(extra_features))
        
        return df[expected_features]
    
    def _convert_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert DataFrame columns to numeric types."""
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    df[col] = pd.to_numeric(df[col])
                except Exception:
                    logger.warning(f"Could not convert column {col} to numeric")
        return df


class PredictionResult:
    """Encapsulates prediction results."""
    
    def __init__(self, sample_idx: int, prediction: int, prob_normal: float, 
                 prob_failure: float, threshold: float):
        self.sample_idx = sample_idx
        self.prediction = prediction
        self.prob_normal = prob_normal
        self.prob_failure = prob_failure
        self.threshold = threshold
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format.
        
        Returns:
            Dictionary representation of the prediction result.
        """
        status = "ALERT: PRE-FAILURE" if self.prediction == 1 else "NORMAL OPERATION"
        risk_level = self._calculate_risk_level()
        
        return {
            'sample': self.sample_idx + 1,
            'prediction': int(self.prediction),
            'status': status,
            'probability_normal': float(round(self.prob_normal, 4)),
            'probability_pre_failure': float(round(self.prob_failure, 4)),
            'risk_level': risk_level,
            'threshold_used': float(self.threshold)
        }
    
    def _calculate_risk_level(self) -> str:
        """Calculate risk level based on failure probability."""
        if self.prediction == 1:
            return "HIGH" if self.prob_failure > 0.8 else "MEDIUM"
        else:
            return "LOW" if self.prob_failure < 0.3 else "LOW-MEDIUM"


class ModelInference:
    """Main class for model inference operations."""
    
    def __init__(self, model_path: str = "models/xgb_best_model.pkl"):
        """Initialize ModelInference with model loading.
        
        Args:
            model_path: Path to the model file.
        """
        self.model_path = model_path
        self.model = ModelLoader.load_model(model_path)
        self.feature_manager = FeatureManager()
        self.data_processor = DataProcessor(self.feature_manager)
        self.expected_features = self.feature_manager.get_expected_features(self.model)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get essential model information.
        
        Returns:
            Dictionary containing model information.
        """
        if self.model is None:
            logger.error("Model not loaded")
            return {}
        
        try:
            info = {
                'model_type': type(self.model).__name__,
                'library': getattr(self.model, '__module__', 'Unknown').split('.')[0],
                'num_features': self.feature_manager.get_feature_count(self.model),
                'feature_names': self.expected_features,
                'file_size_mb': round(os.path.getsize(self.model_path) / (1024*1024), 2),
                'last_modified': datetime.fromtimestamp(
                    os.path.getmtime(self.model_path)
                ).strftime('%Y-%m-%d %H:%M:%S')
            }
            
            if hasattr(self.model, '__dict__'):
                model_attrs = self.model.__dict__
                key_params = {}
                
                important_attrs = [
                    'n_estimators', 'max_depth', 'learning_rate', 'random_state',
                    'objective', 'subsample', 'scale_pos_weight', 'eval_metric',
                    'n_classes_'
                ]
                
                for attr in important_attrs:
                    if attr in model_attrs and model_attrs[attr] is not None:
                        key_params[attr] = model_attrs[attr]
                
                if key_params:
                    info['key_parameters'] = key_params
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting model info: {str(e)}")
            return {'model_type': type(self.model).__name__}
    
    def predict_failure(self, json_data: Union[str, Dict, List], threshold: float = 0.5) -> Dict[str, Any]:
        """Predict equipment failures from JSON data.
        
        Args:
            json_data: Equipment data in JSON format.
            threshold: Decision threshold for classification.
            
        Returns:
            Dictionary containing prediction results.
        """
        try:
            df = self.data_processor.preprocess_json_data(json_data, self.expected_features)
            predictions = self.model.predict(df)
            probabilities = self.model.predict_proba(df)
            
            results = []
            for i in range(len(df)):
                result = PredictionResult(
                    sample_idx=i,
                    prediction=predictions[i],
                    prob_normal=probabilities[i][0],
                    prob_failure=probabilities[i][1],
                    threshold=threshold
                )
                results.append(result.to_dict())
            
            alerts_count = sum(1 for r in results if r['prediction'] == 1)
            
            return {
                'success': True,
                'total_samples': len(results),
                'alerts_detected': alerts_count,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'results': []
            }
    
    def predict(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """Make predictions using the loaded model.
        
        Args:
            X: Input data for prediction.
            
        Returns:
            Array of predictions.
            
        Raises:
            ValueError: If model is not loaded.
        """
        if self.model is None:
            raise ValueError("Model not loaded")
        
        try:
            return self.model.predict(X)
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            raise
    
    def predict_proba(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """Get prediction probabilities.
        
        Args:
            X: Input data for prediction.
            
        Returns:
            Array of prediction probabilities.
            
        Raises:
            ValueError: If model is not loaded.
            AttributeError: If model doesn't support predict_proba.
        """
        if self.model is None:
            raise ValueError("Model not loaded")
        
        if not hasattr(self.model, 'predict_proba'):
            raise AttributeError("Model doesn't support predict_proba")
        
        try:
            return self.model.predict_proba(X)
        except Exception as e:
            logger.error(f"Probability prediction error: {str(e)}")
            raise


def create_sample_data() -> List[Dict[str, float]]:
    """Create sample data for testing.
    
    Returns:
        List of sample data dictionaries.
    """
    return [
      {
        "Auto": -6.136641040606146,
        "Bat_V": 1.7820387778030309,
        "Char_V": 2.817622250940789,
        "Cool_T": 2.2753518934317536,
        "Eng_RPM": 1.026317757091238,
        "Fuel_Con": 6.787985741330217,
        "Fuel_L": 1.2271727785753883,
        "Man": 9.05046125354941,
        "Oil_L": -4.340646092324506,
        "Oil_P": 2.8523096381279585,
        "Recalque": 4.167754852775574,
        "Starts_N": -1.7061564630330222,
        "Stop": -0.11814871443081106,
        "Succao": 3.530457108490094,
        "running": 1.1737351169999917,
        "minutes_running": 0.0,
        "Bat_V_variation": 0.0,
        "Char_V_variation": 0.0,
        "Cool_T_variation": 0.0,
        "Eng_RPM_variation": 0.0,
        "Fuel_Con_variation": 0.0,
        "Fuel_L_variation": 0.0,
        "Oil_L_variation": 0.0,
        "Oil_P_variation": 0.0,
        "Bat_V_variation_percentage": 0.0,
        "Char_V_variation_percentage": 0.0,
        "Cool_T_variation_percentage": 0.0,
        "Eng_RPM_variation_percentage": 0.0,
        "Fuel_Con_variation_percentage": 0.0,
        "Fuel_L_variation_percentage": 0.0,
        "Oil_L_variation_percentage": 0.0,
        "Oil_P_variation_percentage": 0.0,
        "Hydraulic_Head": 0.6372977442854801,
        "Head_per_RPM": 0.620955586008462,
        "Head_trend_per_minutes": 0.0,
        "OilP_per_RPM": 2.7791681654343554,
        "CoolT_per_RPM": 2.2170052868231513,
        "Fuel_rate": 0.0,
        "Fuel_efficiency": 0.0
      }
    ]


def main():
    """Main function demonstrating ModelInference usage."""
    logger.info("Starting XGBoost Failure Prediction Model...")
    
    try:
        model_inference = ModelInference()
        
        info = model_inference.get_model_info()
        logger.info(f"Model loaded: {info.get('model_type')} with {info.get('num_features')} features")
        
        sample_data = create_sample_data()
        result = model_inference.predict_failure(sample_data)
        
        if result['success']:
            logger.info(f"Test completed: {result['total_samples']} samples, {result['alerts_detected']} alerts")
        else:
            logger.error(f"Test failed: {result['error']}")
            
    except Exception as e:
        logger.error(f"Application error: {str(e)}")


if __name__ == "__main__":
    main()
