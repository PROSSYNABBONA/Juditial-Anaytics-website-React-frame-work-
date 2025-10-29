import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.services.ml_service import JudicialMLService

class TestJudicialMLService:
    """Test cases for the Judicial ML Service"""
    
    def setup_method(self):
        """Setup test data before each test"""
        self.ml_service = JudicialMLService()
        
        # Create sample test data
        self.sample_data = pd.DataFrame({
            'case_id': ['CASE-001', 'CASE-002', 'CASE-003', 'CASE-004', 'CASE-005'],
            'court_id': ['HC-001', 'MC-001', 'HC-002', 'MC-002', 'HC-001'],
            'location_region': ['Central', 'Northern', 'Central', 'Western', 'Central'],
            'case_type': ['Civil', 'Criminal', 'Land', 'Civil', 'Criminal'],
            'filing_date': [
                '2023-01-15', '2023-02-10', '2023-03-05', '2023-04-20', '2023-05-12'
            ],
            'resolution_date': [
                '2023-06-20', '2023-08-15', '2023-09-12', '2023-10-25', '2023-11-18'
            ],
            'num_hearings': [4, 6, 5, 3, 7],
            'num_adjournments': [2, 3, 2, 1, 4],
            'judge_id_hashed': ['JUDGE-001', 'JUDGE-002', 'JUDGE-003', 'JUDGE-004', 'JUDGE-005'],
            'outcome_category': ['Settled', 'Convicted', 'Settled', 'Dismissed', 'Convicted'],
            'time_to_resolution_days': [156, 186, 191, 188, 190]
        })
    
    def test_prepare_features(self):
        """Test feature preparation"""
        df = self.ml_service.prepare_features(self.sample_data.copy())
        
        # Check if new features are created
        assert 'filing_month' in df.columns
        assert 'filing_quarter' in df.columns
        assert 'case_type_encoded' in df.columns
        assert 'region_encoded' in df.columns
        assert 'hearings_per_month' in df.columns
        assert 'adjournment_rate' in df.columns
        
        # Check if feature columns are set
        assert len(self.ml_service.feature_columns) > 0
    
    def test_train_models_success(self):
        """Test successful model training"""
        result = self.ml_service.train_models(self.sample_data)
        
        # Check if training was successful
        assert 'error' not in result
        assert 'linear_regression' in result
        assert 'random_forest' in result
        assert 'training_samples' in result
        assert 'test_samples' in result
        assert 'best_model' in result
        
        # Check if models are trained
        assert self.ml_service.is_trained == True
        assert self.ml_service.linear_model is not None
        assert self.ml_service.random_forest_model is not None
    
    def test_train_models_insufficient_data(self):
        """Test training with insufficient data"""
        small_data = self.sample_data.head(2)  # Only 2 samples
        result = self.ml_service.train_models(small_data)
        
        assert 'error' in result
        assert 'Insufficient data' in result['error']
    
    def test_predict_resolution_time(self):
        """Test case resolution time prediction"""
        # First train the models
        self.ml_service.train_models(self.sample_data)
        
        # Test prediction
        case_data = {
            'case_type': 'Civil',
            'location_region': 'Central',
            'filing_date': '2024-01-01',
            'num_hearings': 5,
            'num_adjournments': 2
        }
        
        prediction = self.ml_service.predict_resolution_time(case_data)
        
        assert 'error' not in prediction
        assert 'predicted_days' in prediction
        assert 'model_used' in prediction
        assert 'confidence' in prediction
        assert isinstance(prediction['predicted_days'], int)
    
    def test_predict_resolution_time_not_trained(self):
        """Test prediction without trained models"""
        case_data = {
            'case_type': 'Civil',
            'location_region': 'Central',
            'filing_date': '2024-01-01',
            'num_hearings': 5,
            'num_adjournments': 2
        }
        
        prediction = self.ml_service.predict_resolution_time(case_data)
        
        assert 'error' in prediction
        assert 'Model not trained' in prediction['error']
    
    def test_get_model_insights(self):
        """Test getting model insights"""
        # Train models first
        self.ml_service.train_models(self.sample_data)
        
        insights = self.ml_service.get_model_insights()
        
        assert 'error' not in insights
        assert 'model_performance' in insights
        assert 'training_data_info' in insights
        assert 'feature_columns' in insights
        assert 'models_available' in insights
        assert 'is_trained' in insights
    
    def test_compare_models(self):
        """Test model comparison"""
        # Train models first
        self.ml_service.train_models(self.sample_data)
        
        comparison = self.ml_service.compare_models()
        
        assert 'error' not in comparison
        assert 'linear_regression' in comparison
        assert 'random_forest' in comparison
        assert 'recommendation' in comparison
        
        # Check if performance metrics are present
        linear_metrics = comparison['linear_regression']
        rf_metrics = comparison['random_forest']
        
        assert 'r2_score' in linear_metrics
        assert 'mae' in linear_metrics
        assert 'rmse' in linear_metrics
        assert 'r2_score' in rf_metrics
        assert 'mae' in rf_metrics
        assert 'rmse' in rf_metrics
    
    def test_model_performance_metrics(self):
        """Test that model performance metrics are reasonable"""
        result = self.ml_service.train_models(self.sample_data)
        
        # Check linear regression metrics
        linear_metrics = result['linear_regression']
        assert linear_metrics['r2_score'] >= 0  # R² should be non-negative
        assert linear_metrics['mae'] >= 0  # MAE should be non-negative
        assert linear_metrics['rmse'] >= 0  # RMSE should be non-negative
        
        # Check random forest metrics
        rf_metrics = result['random_forest']
        assert rf_metrics['r2_score'] >= 0
        assert rf_metrics['mae'] >= 0
        assert rf_metrics['rmse'] >= 0
        assert 'feature_importance' in rf_metrics
        
        # Check feature importance
        feature_importance = rf_metrics['feature_importance']
        assert len(feature_importance) > 0
        assert all(importance >= 0 for importance in feature_importance.values())
    
    def test_feature_engineering(self):
        """Test feature engineering calculations"""
        df = self.ml_service.prepare_features(self.sample_data.copy())
        
        # Test hearings_per_month calculation
        for idx, row in df.iterrows():
            if row['time_to_resolution_days'] > 0:
                expected_hearings_per_month = row['num_hearings'] / (row['time_to_resolution_days'] / 30)
                assert abs(row['hearings_per_month'] - expected_hearings_per_month) < 0.01
        
        # Test adjournment_rate calculation
        for idx, row in df.iterrows():
            if row['num_hearings'] > 0:
                expected_adjournment_rate = row['num_adjournments'] / row['num_hearings']
                assert abs(row['adjournment_rate'] - expected_adjournment_rate) < 0.01
    
    def test_data_validation(self):
        """Test data validation and error handling"""
        # Test with missing required columns
        incomplete_data = self.sample_data.drop(columns=['case_type'])
        
        with pytest.raises(KeyError):
            self.ml_service.prepare_features(incomplete_data)
        
        # Test with invalid date format
        invalid_data = self.sample_data.copy()
        invalid_data['filing_date'] = 'invalid-date'
        
        with pytest.raises(ValueError):
            self.ml_service.prepare_features(invalid_data)
    
    def test_model_save_load(self):
        """Test model saving and loading"""
        # Train models
        self.ml_service.train_models(self.sample_data)
        
        # Save models
        save_result = self.ml_service.save_models("test_models")
        assert 'error' not in save_result
        
        # Create new service instance and load models
        new_service = JudicialMLService()
        load_result = new_service.load_models("test_models")
        
        assert 'error' not in load_result
        assert new_service.is_trained == True
        assert new_service.linear_model is not None
        assert new_service.random_forest_model is not None

if __name__ == "__main__":
    pytest.main([__file__])
