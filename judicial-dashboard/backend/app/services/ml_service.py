import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
import joblib
from typing import Dict, List, Tuple
import os
import json
from datetime import datetime
from pathlib import Path

class JudicialMLService:
    def __init__(self):
        self.linear_model = None
        self.random_forest_model = None
        self.feature_columns = []
        self.is_trained = False
        self.model_performance = {}
        self.training_data_info = {}
        
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for ML model"""
        # Create feature columns
        df['filing_month'] = pd.to_datetime(df['filing_date']).dt.month
        df['filing_quarter'] = pd.to_datetime(df['filing_date']).dt.quarter
        df['case_type_encoded'] = pd.Categorical(df['case_type']).codes
        df['region_encoded'] = pd.Categorical(df['location_region']).codes
        
        # Feature engineering
        df['hearings_per_month'] = df['num_hearings'] / (df['time_to_resolution_days'] / 30)
        df['adjournment_rate'] = df['num_adjournments'] / df['num_hearings']
        
        self.feature_columns = [
            'case_type_encoded', 'region_encoded', 'filing_month', 
            'filing_quarter', 'num_hearings', 'num_adjournments',
            'hearings_per_month', 'adjournment_rate'
        ]
        
        return df

    def load_dataset(self, file_path: str) -> pd.DataFrame:
        """Load CSV or Excel dataset and normalize columns."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Dataset not found: {file_path}")

        if path.suffix.lower() in [".xlsx", ".xls"]:
            df = pd.read_excel(file_path)
        elif path.suffix.lower() in [".csv"]:
            df = pd.read_csv(file_path)
        else:
            raise ValueError("Unsupported file type. Use .csv or .xlsx")

        # Normalize expected columns (case-insensitive match)
        rename_map = {}
        cols_lower = {c.lower(): c for c in df.columns}

        expected = {
            'case_id', 'court_id', 'location_region', 'case_type',
            'filing_date', 'resolution_date', 'num_hearings', 'num_adjournments',
            'judge_id_hashed', 'outcome_category', 'time_to_resolution_days'
        }
        for col in expected:
            if col in df.columns:
                continue
            if col in cols_lower:
                rename_map[cols_lower[col]] = col

        if rename_map:
            df = df.rename(columns=rename_map)

        # Convert dates
        if 'filing_date' in df.columns:
            df['filing_date'] = pd.to_datetime(df['filing_date'], errors='coerce').dt.date
        if 'resolution_date' in df.columns:
            df['resolution_date'] = pd.to_datetime(df['resolution_date'], errors='coerce').dt.date

        # If time_to_resolution_days missing but dates exist, compute
        if 'time_to_resolution_days' not in df.columns and {
            'filing_date', 'resolution_date'
        }.issubset(df.columns):
            delta = pd.to_datetime(df['resolution_date']) - pd.to_datetime(df['filing_date'])
            df['time_to_resolution_days'] = (delta.dt.days).where(~delta.isna(), None)

        return df
    
    def train_models(self, df: pd.DataFrame) -> Dict:
        """Train both Linear Regression and Random Forest models as specified in objectives"""
        # Prepare data
        df = self.prepare_features(df)
        
        # Remove rows with missing target values
        df = df.dropna(subset=['time_to_resolution_days'])
        
        if len(df) < 10:
            return {"error": "Insufficient data for training"}
        
        # Store training data info
        self.training_data_info = {
            "total_samples": len(df),
            "date_range": {
                "start": df['filing_date'].min(),
                "end": df['filing_date'].max()
            },
            "case_types": df['case_type'].value_counts().to_dict(),
            "regions": df['location_region'].value_counts().to_dict()
        }
        
        # Prepare features and target
        X = df[self.feature_columns]
        y = df['time_to_resolution_days']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train Linear Regression Model
        self.linear_model = LinearRegression()
        self.linear_model.fit(X_train, y_train)
        linear_pred = self.linear_model.predict(X_test)
        
        # Train Random Forest Model
        self.random_forest_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.random_forest_model.fit(X_train, y_train)
        rf_pred = self.random_forest_model.predict(X_test)
        
        # Evaluate both models
        linear_mae = mean_absolute_error(y_test, linear_pred)
        linear_r2 = r2_score(y_test, linear_pred)
        linear_mse = mean_squared_error(y_test, linear_pred)
        
        rf_mae = mean_absolute_error(y_test, rf_pred)
        rf_r2 = r2_score(y_test, rf_pred)
        rf_mse = mean_squared_error(y_test, rf_pred)
        
        # Store performance metrics
        self.model_performance = {
            "linear_regression": {
                "mae": linear_mae,
                "r2_score": linear_r2,
                "mse": linear_mse,
                "rmse": np.sqrt(linear_mse)
            },
            "random_forest": {
                "mae": rf_mae,
                "r2_score": rf_r2,
                "mse": rf_mse,
                "rmse": np.sqrt(rf_mse),
                "feature_importance": dict(zip(self.feature_columns, self.random_forest_model.feature_importances_))
            }
        }
        
        self.is_trained = True
        
        return {
            "linear_regression": {
                "mae": linear_mae,
                "r2_score": linear_r2,
                "rmse": np.sqrt(linear_mse)
            },
            "random_forest": {
                "mae": rf_mae,
                "r2_score": rf_r2,
                "rmse": np.sqrt(rf_mse),
                "feature_importance": dict(zip(self.feature_columns, self.random_forest_model.feature_importances_))
            },
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "best_model": "random_forest" if rf_r2 > linear_r2 else "linear_regression"
        }
    
    def predict_resolution_time(self, case_data: Dict, model_type: str = "best") -> Dict:
        """Predict resolution time for a new case using specified model"""
        if not self.is_trained:
            return {"error": "Model not trained"}
        
        # Convert case data to DataFrame
        df = pd.DataFrame([case_data])
        df = self.prepare_features(df)
        
        # Make prediction
        X = df[self.feature_columns]
        
        # Determine which model to use
        if model_type == "best":
            model_type = self.model_performance.get("best_model", "random_forest")
        
        if model_type == "linear_regression" and self.linear_model:
            prediction = self.linear_model.predict(X)[0]
            model_name = "Linear Regression"
        elif model_type == "random_forest" and self.random_forest_model:
            prediction = self.random_forest_model.predict(X)[0]
            model_name = "Random Forest"
            feature_importance = dict(zip(self.feature_columns, self.random_forest_model.feature_importances_))
        else:
            return {"error": "Model not available"}
        
        # Calculate confidence based on model performance
        model_perf = self.model_performance.get(model_type, {})
        confidence = model_perf.get("r2_score", 0.5)
        
        result = {
            "predicted_days": int(prediction),
            "model_used": model_name,
            "confidence": round(confidence, 3),
            "prediction_date": datetime.now().isoformat()
        }
        
        if model_type == "random_forest":
            result["feature_importance"] = feature_importance
        
        return result
    
    def get_model_insights(self) -> Dict:
        """Get insights from the trained models"""
        if not self.is_trained:
            return {"error": "Models not trained"}
        
        return {
            "model_performance": self.model_performance,
            "training_data_info": self.training_data_info,
            "feature_columns": self.feature_columns,
            "models_available": ["linear_regression", "random_forest"],
            "is_trained": True,
            "training_date": datetime.now().isoformat()
        }
    
    def compare_models(self) -> Dict:
        """Compare performance of Linear Regression vs Random Forest"""
        if not self.is_trained:
            return {"error": "Models not trained"}
        
        linear_perf = self.model_performance.get("linear_regression", {})
        rf_perf = self.model_performance.get("random_forest", {})
        
        return {
            "linear_regression": {
                "r2_score": linear_perf.get("r2_score", 0),
                "mae": linear_perf.get("mae", 0),
                "rmse": linear_perf.get("rmse", 0)
            },
            "random_forest": {
                "r2_score": rf_perf.get("r2_score", 0),
                "mae": rf_perf.get("mae", 0),
                "rmse": rf_perf.get("rmse", 0)
            },
            "recommendation": "Random Forest" if rf_perf.get("r2_score", 0) > linear_perf.get("r2_score", 0) else "Linear Regression"
        }
    
    def save_models(self, base_filepath: str):
        """Save trained models"""
        if self.is_trained:
            if self.linear_model:
                joblib.dump(self.linear_model, f"{base_filepath}_linear.joblib")
            if self.random_forest_model:
                joblib.dump(self.random_forest_model, f"{base_filepath}_random_forest.joblib")
            
            # Save model metadata
            metadata = {
                "model_performance": self.model_performance,
                "training_data_info": self.training_data_info,
                "feature_columns": self.feature_columns,
                "training_date": datetime.now().isoformat()
            }
            
            with open(f"{base_filepath}_metadata.json", "w") as f:
                json.dump(metadata, f, indent=2, default=str)
            
            return {"message": "Models saved successfully"}
        return {"error": "No trained models to save"}
    
    def load_models(self, base_filepath: str):
        """Load pre-trained models"""
        try:
            if os.path.exists(f"{base_filepath}_linear.joblib"):
                self.linear_model = joblib.load(f"{base_filepath}_linear.joblib")
            if os.path.exists(f"{base_filepath}_random_forest.joblib"):
                self.random_forest_model = joblib.load(f"{base_filepath}_random_forest.joblib")
            
            if os.path.exists(f"{base_filepath}_metadata.json"):
                with open(f"{base_filepath}_metadata.json", "r") as f:
                    metadata = json.load(f)
                    self.model_performance = metadata.get("model_performance", {})
                    self.training_data_info = metadata.get("training_data_info", {})
                    self.feature_columns = metadata.get("feature_columns", [])
            
            if self.linear_model or self.random_forest_model:
                self.is_trained = True
                return {"message": "Models loaded successfully"}
            else:
                return {"error": "No model files found"}
        except Exception as e:
            return {"error": f"Error loading models: {str(e)}"}

# Global ML service instance
ml_service = JudicialMLService()
