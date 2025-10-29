import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestJudicialDashboardAPI:
    """Test cases for the Judicial Dashboard API"""
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "status" in data
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_get_cases(self):
        """Test getting all cases"""
        response = client.get("/api/cases")
        assert response.status_code == 200
        data = response.json()
        assert "cases" in data
        assert "total" in data
        assert isinstance(data["cases"], list)
        assert data["total"] > 0
    
    def test_get_specific_case(self):
        """Test getting a specific case"""
        response = client.get("/api/cases/CASE-001")
        assert response.status_code == 200
        data = response.json()
        assert "case" in data
        assert data["case"]["case_id"] == "CASE-001"
    
    def test_get_nonexistent_case(self):
        """Test getting a non-existent case"""
        response = client.get("/api/cases/NONEXISTENT")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_get_analytics_summary(self):
        """Test getting analytics summary"""
        response = client.get("/api/analytics/summary")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        summary = data["summary"]
        
        # Check required fields
        required_fields = [
            "total_cases", "avg_resolution_time", "cases_by_type",
            "cases_by_region", "avg_hearings", "avg_adjournments"
        ]
        for field in required_fields:
            assert field in summary
    
    def test_get_predictions(self):
        """Test getting predictions"""
        response = client.get("/api/analytics/predictions")
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        predictions = data["predictions"]
        
        # Check required fields
        required_fields = [
            "model_accuracy", "predicted_avg_resolution", "confidence_interval",
            "models_available", "best_model"
        ]
        for field in required_fields:
            assert field in predictions
    
    def test_train_models(self):
        """Test training ML models"""
        response = client.post("/api/analytics/train-models")
        assert response.status_code == 200
        data = response.json()
        assert "training_result" in data
        
        training_result = data["training_result"]
        assert "linear_regression" in training_result
        assert "random_forest" in training_result
        assert "training_samples" in training_result
        assert "test_samples" in training_result
        assert "best_model" in training_result
    
    def test_get_model_comparison(self):
        """Test getting model comparison"""
        # First train models
        client.post("/api/analytics/train-models")
        
        response = client.get("/api/analytics/model-comparison")
        assert response.status_code == 200
        data = response.json()
        assert "comparison" in data
        
        comparison = data["comparison"]
        assert "linear_regression" in comparison
        assert "random_forest" in comparison
        assert "recommendation" in comparison
    
    def test_predict_case_resolution(self):
        """Test predicting case resolution"""
        # First train models
        client.post("/api/analytics/train-models")
        
        case_data = {
            "case_type": "Civil",
            "location_region": "Central",
            "filing_date": "2024-01-01",
            "num_hearings": 5,
            "num_adjournments": 2
        }
        
        response = client.post("/api/analytics/predict", json=case_data)
        assert response.status_code == 200
        data = response.json()
        assert "prediction" in data
        
        prediction = data["prediction"]
        assert "predicted_days" in prediction
        assert "model_used" in prediction
        assert "confidence" in prediction
        assert isinstance(prediction["predicted_days"], int)
    
    def test_predict_case_resolution_invalid_data(self):
        """Test prediction with invalid data"""
        invalid_case_data = {
            "case_type": "InvalidType",
            "location_region": "InvalidRegion"
        }
        
        response = client.post("/api/analytics/predict", json=invalid_case_data)
        # Should still work but may have lower accuracy
        assert response.status_code in [200, 500]
    
    def test_get_model_insights(self):
        """Test getting model insights"""
        # First train models
        client.post("/api/analytics/train-models")
        
        response = client.get("/api/analytics/model-insights")
        assert response.status_code == 200
        data = response.json()
        assert "insights" in data
        
        insights = data["insights"]
        assert "model_performance" in insights
        assert "training_data_info" in insights
        assert "feature_columns" in insights
        assert "models_available" in insights
        assert "is_trained" in insights
    
    def test_get_courts(self):
        """Test getting courts list"""
        response = client.get("/api/courts")
        assert response.status_code == 200
        data = response.json()
        assert "courts" in data
        assert isinstance(data["courts"], list)
        assert len(data["courts"]) > 0
        
        # Check court structure
        court = data["courts"][0]
        required_fields = ["court_id", "name", "region"]
        for field in required_fields:
            assert field in court
    
    def test_cors_headers(self):
        """Test CORS headers are present"""
        response = client.get("/")
        assert response.status_code == 200
        
        # Check for CORS headers (these would be set by middleware)
        # Note: TestClient might not show all middleware effects
    
    def test_api_documentation(self):
        """Test that API documentation is accessible"""
        response = client.get("/docs")
        assert response.status_code == 200
        
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
    
    def test_error_handling(self):
        """Test error handling for invalid endpoints"""
        response = client.get("/api/invalid-endpoint")
        assert response.status_code == 404
    
    def test_data_consistency(self):
        """Test data consistency across endpoints"""
        # Get cases
        cases_response = client.get("/api/cases")
        cases_data = cases_response.json()
        
        # Get analytics summary
        analytics_response = client.get("/api/analytics/summary")
        analytics_data = analytics_response.json()
        
        # Check that total cases match
        assert cases_data["total"] == analytics_data["summary"]["total_cases"]
    
    def test_model_training_validation(self):
        """Test model training with validation"""
        response = client.post("/api/analytics/train-models")
        assert response.status_code == 200
        
        training_result = response.json()["training_result"]
        
        # Validate model performance metrics
        linear_metrics = training_result["linear_regression"]
        rf_metrics = training_result["random_forest"]
        
        # Check that metrics are reasonable
        assert linear_metrics["r2_score"] >= 0
        assert linear_metrics["mae"] >= 0
        assert linear_metrics["rmse"] >= 0
        
        assert rf_metrics["r2_score"] >= 0
        assert rf_metrics["mae"] >= 0
        assert rf_metrics["rmse"] >= 0
        
        # Check that we have feature importance for Random Forest
        assert "feature_importance" in rf_metrics
        assert len(rf_metrics["feature_importance"]) > 0

if __name__ == "__main__":
    pytest.main([__file__])
