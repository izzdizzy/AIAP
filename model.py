"""
model.py - XGBoost Model Training and Optimization for Hospital Readmission Prediction

This module handles:
- Advanced feature engineering
- Data preprocessing with proper scaling
- SMOTE for handling class imbalance
- Hyperparameter optimization using RandomizedSearchCV with StratifiedKFold
- Model evaluation with comprehensive metrics
- SHAP integration for model interpretability
- Model serialization for deployment
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, StratifiedKFold, RandomizedSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, roc_curve, confusion_matrix, classification_report
)
from sklearn.pipeline import Pipeline
import xgboost as xgb
from imblearn.over_sampling import SMOTE
import shap
import joblib
import os
import json
from datetime import datetime


class ReadmissionPredictor:
    """
    A comprehensive class for training, optimizing, and deploying
    an XGBoost model for hospital readmission prediction.
    """
    
    def __init__(self, random_state=42):
        """
        Initialize the predictor with a fixed random state for reproducibility.
        
        Args:
            random_state (int): Random seed for reproducibility
        """
        self.random_state = random_state
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = None
        self.best_params = None
        self.training_metrics = {}
        self.shap_explainer = None
        
    def load_data(self, filepath):
        """
        Load dataset from CSV file with error handling.
        
        Args:
            filepath (str): Path to the CSV file
            
        Returns:
            pd.DataFrame: Loaded dataframe
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is empty or invalid
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Data file not found: {filepath}")
        
        try:
            df = pd.read_csv(filepath)
            if df.empty:
                raise ValueError("Loaded dataframe is empty")
            print(f"Successfully loaded data: {df.shape[0]} samples, {df.shape[1]} features")
            return df
        except Exception as e:
            raise ValueError(f"Error loading data: {str(e)}")
    
    def advanced_feature_engineering(self, df):
        """
        Perform advanced feature engineering to create predictive features.
        
        Args:
            df (pd.DataFrame): Raw input dataframe
            
        Returns:
            pd.DataFrame: DataFrame with engineered features
        """
        # Create a copy to avoid modifying original data
        df_eng = df.copy()
        
        # Age-based features
        if 'age' in df_eng.columns:
            df_eng['age_group'] = pd.cut(
                df_eng['age'],
                bins=[0, 30, 45, 60, 75, 100],
                labels=['Young', 'Middle', 'Senior', 'Elderly', 'Very Elderly']
            )
            df_eng['is_elderly'] = (df_eng['age'] >= 65).astype(int)
            df_eng['age_squared'] = df_eng['age'] ** 2
        
        # Comorbidity features
        comorbidity_cols = [col for col in df_eng.columns if 'comorbidity' in col.lower() or 'chronic' in col.lower()]
        if comorbidity_cols:
            df_eng['total_comorbidities'] = df_eng[comorbidity_cols].sum(axis=1, skipna=True)
            df_eng['has_multiple_comorbidities'] = (df_eng['total_comorbidities'] >= 2).astype(int)
        
        # Medication-related features
        med_cols = [col for col in df_eng.columns if 'medication' in col.lower() or 'drug' in col.lower()]
        if med_cols:
            df_eng['total_medications'] = df_eng[med_cols].sum(axis=1, skipna=True)
            df_eng['polypharmacy'] = (df_eng['total_medications'] >= 5).astype(int)
        
        # Previous admission features
        if 'previous_admissions' in df_eng.columns:
            df_eng['frequent_admitter'] = (df_eng['previous_admissions'] >= 3).astype(int)
            df_eng['admission_rate'] = df_eng['previous_admissions'] / (df_eng['age'] + 1)
        
        # Length of stay features (if available)
        if 'length_of_stay' in df_eng.columns:
            df_eng['prolonged_stay'] = (df_eng['length_of_stay'] > 7).astype(int)
            df_eng['los_category'] = pd.cut(
                df_eng['length_of_stay'],
                bins=[-1, 3, 7, 14, 100],
                labels=['Short', 'Medium', 'Long', 'Very Long']
            )
        
        # Lab value aggregations (if lab columns exist)
        lab_cols = [col for col in df_eng.columns if any(x in col.lower() for x in ['lab', 'blood', 'test', 'hba1c', 'creatinine', 'cholesterol'])]
        if lab_cols:
            df_eng['abnormal_lab_count'] = df_eng[lab_cols].apply(
                lambda row: sum(1 for val in row if pd.notna(val) and (val < 0 or val > 1000)),
                axis=1
            )
        
        # Encode categorical variables
        categorical_cols = df_eng.select_dtypes(include=['object', 'category']).columns
        for col in categorical_cols:
            if col != 'readmitted':  # Don't encode target variable
                # Use one-hot encoding for categorical variables
                dummies = pd.get_dummies(df_eng[col], prefix=col, drop_first=True)
                df_eng = pd.concat([df_eng, dummies], axis=1)
                df_eng = df_eng.drop(col, axis=1)
        
        print(f"Feature engineering complete: {df_eng.shape[1]} total features")
        return df_eng
    
    def preprocess_data(self, df, target_col='readmitted'):
        """
        Preprocess data including handling missing values and scaling.
        
        Args:
            df (pd.DataFrame): Input dataframe
            target_col (str): Name of target column
            
        Returns:
            tuple: (X_processed, y, feature_names)
        """
        # Separate features and target
        if target_col not in df.columns:
            raise ValueError(f"Target column '{target_col}' not found in dataframe")
        
        y = df[target_col].values
        X = df.drop(columns=[target_col])
        
        # Store feature names
        self.feature_names = X.columns.tolist()
        
        # Handle missing values - fill with median for numeric columns
        numeric_cols = X.select_dtypes(include=[np.number]).columns
        X[numeric_cols] = X[numeric_cols].fillna(X[numeric_cols].median())
        
        # Fill any remaining NaN with 0
        X = X.fillna(0)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        X_processed = pd.DataFrame(X_scaled, columns=self.feature_names)
        
        print(f"Preprocessing complete: {X_processed.shape[0]} samples, {X_processed.shape[1]} features")
        return X_processed, y, self.feature_names
    
    def apply_smote(self, X, y, sampling_strategy='auto'):
        """
        Apply SMOTE to handle class imbalance.
        
        Args:
            X (pd.DataFrame): Feature matrix
            y (array): Target vector
            sampling_strategy (str or float): SMOTE sampling strategy
            
        Returns:
            tuple: (X_resampled, y_resampled)
        """
        # Check class distribution before SMOTE
        unique, counts = np.unique(y, return_counts=True)
        print(f"Class distribution before SMOTE: {dict(zip(unique, counts))}")
        
        # Apply SMOTE
        smote = SMOTE(random_state=self.random_state, sampling_strategy=sampling_strategy)
        X_resampled, y_resampled = smote.fit_resample(X, y)
        
        # Check class distribution after SMOTE
        unique, counts = np.unique(y_resampled, return_counts=True)
        print(f"Class distribution after SMOTE: {dict(zip(unique, counts))}")
        
        return X_resampled, y_resampled
    
    def optimize_hyperparameters(self, X, y, n_iter=50, cv_folds=5):
        """
        Optimize XGBoost hyperparameters using RandomizedSearchCV with StratifiedKFold.
        
        Args:
            X (pd.DataFrame): Feature matrix
            y (array): Target vector
            n_iter (int): Number of parameter settings sampled
            cv_folds (int): Number of CV folds
            
        Returns:
            dict: Best parameters found
        """
        # Define parameter distribution for randomized search
        param_dist = {
            'n_estimators': [100, 200, 300, 400, 500],
            'max_depth': [3, 4, 5, 6, 7, 8, 9, 10],
            'learning_rate': [0.01, 0.05, 0.1, 0.15, 0.2, 0.3],
            'subsample': [0.6, 0.7, 0.8, 0.9, 1.0],
            'colsample_bytree': [0.6, 0.7, 0.8, 0.9, 1.0],
            'min_child_weight': [1, 3, 5, 7],
            'gamma': [0, 0.1, 0.2, 0.3, 0.4],
            'reg_alpha': [0, 0.01, 0.1, 1, 10],
            'reg_lambda': [0.01, 0.1, 1, 10, 100],
            'scale_pos_weight': [1, 2, 3, 4, 5]
        }
        
        # Create stratified k-fold
        skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=self.random_state)
        
        # Initialize XGBoost classifier
        xgb_clf = xgb.XGBClassifier(
            objective='binary:logistic',
            eval_metric='auc',
            use_label_encoder=False,
            random_state=self.random_state,
            n_jobs=-1
        )
        
        # Setup randomized search
        random_search = RandomizedSearchCV(
            estimator=xgb_clf,
            param_distributions=param_dist,
            n_iter=n_iter,
            scoring='roc_auc',
            cv=skf,
            verbose=1,
            n_jobs=-1,
            random_state=self.random_state
        )
        
        print("Starting hyperparameter optimization...")
        random_search.fit(X, y)
        
        self.best_params = random_search.best_params_
        print(f"Best parameters found: {self.best_params}")
        print(f"Best ROC-AUC score: {random_search.best_score_:.4f}")
        
        return self.best_params
    
    def train_model(self, X, y, params=None):
        """
        Train the final XGBoost model with optimized parameters.
        
        Args:
            X (pd.DataFrame): Feature matrix
            y (array): Target vector
            params (dict): Optional custom parameters
            
        Returns:
            xgb.XGBClassifier: Trained model
        """
        # Use best parameters if available, otherwise use defaults
        if params is None:
            if self.best_params:
                params = self.best_params
            else:
                params = {
                    'n_estimators': 300,
                    'max_depth': 6,
                    'learning_rate': 0.1,
                    'subsample': 0.8,
                    'colsample_bytree': 0.8,
                    'min_child_weight': 3,
                    'gamma': 0.1,
                    'reg_alpha': 0.1,
                    'reg_lambda': 1,
                    'scale_pos_weight': 1
                }
        
        # Initialize and train model
        self.model = xgb.XGBClassifier(
            **params,
            objective='binary:logistic',
            eval_metric='auc',
            use_label_encoder=False,
            random_state=self.random_state,
            n_jobs=-1
        )
        
        self.model.fit(X, y)
        print("Model training complete")
        
        return self.model
    
    def evaluate_model(self, X, y, threshold=0.5):
        """
        Evaluate model performance with comprehensive metrics.
        
        Args:
            X (pd.DataFrame): Feature matrix
            y (array): Target vector
            threshold (float): Classification threshold
            
        Returns:
            dict: Dictionary of evaluation metrics
        """
        if self.model is None:
            raise ValueError("No trained model available for evaluation")
        
        # Get predictions and probabilities
        y_pred_proba = self.model.predict_proba(X)[:, 1]
        y_pred = (y_pred_proba >= threshold).astype(int)
        
        # Calculate metrics
        metrics = {
            'accuracy': accuracy_score(y, y_pred),
            'precision': precision_score(y, y_pred, zero_division=0),
            'recall': recall_score(y, y_pred, zero_division=0),
            'f1_score': f1_score(y, y_pred, zero_division=0),
            'roc_auc': roc_auc_score(y, y_pred_proba),
            'confusion_matrix': confusion_matrix(y, y_pred).tolist()
        }
        
        # Print classification report
        print("\nClassification Report:")
        print(classification_report(y, y_pred, digits=4))
        
        # Print detailed metrics
        print("\nDetailed Metrics:")
        for metric_name, metric_value in metrics.items():
            if metric_name != 'confusion_matrix':
                print(f"{metric_name}: {metric_value:.4f}")
        
        self.training_metrics = metrics
        return metrics
    
    def compute_shap_values(self, X_sample, max_samples=1000):
        """
        Compute SHAP values for model interpretability.
        
        Args:
            X_sample (pd.DataFrame): Sample of data for SHAP computation
            max_samples (int): Maximum number of samples for SHAP
            
        Returns:
            shap.Explanation: SHAP explanation object
        """
        if self.model is None:
            raise ValueError("No trained model available for SHAP analysis")
        
        # Limit sample size for computational efficiency
        if len(X_sample) > max_samples:
            X_sample = X_sample.sample(n=max_samples, random_state=self.random_state)
        
        # Create TreeExplainer for XGBoost
        self.shap_explainer = shap.TreeExplainer(self.model)
        shap_values = self.shap_explainer.shap_values(X_sample)
        
        print(f"SHAP values computed for {len(X_sample)} samples")
        return shap_values
    
    def get_feature_importance(self, top_n=20):
        """
        Get top N most important features.
        
        Args:
            top_n (int): Number of top features to return
            
        Returns:
            pd.DataFrame: DataFrame with feature importances
        """
        if self.model is None:
            raise ValueError("No trained model available")
        
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        })
        importance_df = importance_df.sort_values('importance', ascending=False)
        
        print(f"Top {top_n} most important features:")
        print(importance_df.head(top_n))
        
        return importance_df.head(top_n)
    
    def save_model(self, output_dir='models', model_name='readmission_predictor'):
        """
        Save trained model, scaler, and metadata for deployment.
        
        Args:
            output_dir (str): Directory to save model artifacts
            model_name (str): Base name for saved files
            
        Returns:
            str: Path to saved model directory
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate timestamp for versioning
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        model_path = os.path.join(output_dir, f"{model_name}_{timestamp}")
        os.makedirs(model_path, exist_ok=True)
        
        # Save model
        model_file = os.path.join(model_path, 'model.joblib')
        joblib.dump(self.model, model_file)
        
        # Save scaler
        scaler_file = os.path.join(model_path, 'scaler.joblib')
        joblib.dump(self.scaler, scaler_file)
        
        # Save metadata
        metadata = {
            'feature_names': self.feature_names,
            'best_params': self.best_params,
            'training_metrics': self.training_metrics,
            'random_state': self.random_state,
            'created_at': timestamp
        }
        metadata_file = os.path.join(model_path, 'metadata.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Model artifacts saved to: {model_path}")
        return model_path
    
    def load_model(self, model_path):
        """
        Load a trained model from disk.
        
        Args:
            model_path (str): Path to model directory
            
        Returns:
            bool: True if successful
        """
        try:
            # Load model
            model_file = os.path.join(model_path, 'model.joblib')
            self.model = joblib.load(model_file)
            
            # Load scaler
            scaler_file = os.path.join(model_path, 'scaler.joblib')
            self.scaler = joblib.load(scaler_file)
            
            # Load metadata
            metadata_file = os.path.join(model_path, 'metadata.json')
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            self.feature_names = metadata['feature_names']
            self.best_params = metadata['best_params']
            self.training_metrics = metadata['training_metrics']
            self.random_state = metadata['random_state']
            
            print(f"Model loaded successfully from: {model_path}")
            return True
            
        except Exception as e:
            print(f"Error loading model: {str(e)}")
            return False
    
    def predict(self, X):
        """
        Make predictions on new data.
        
        Args:
            X (pd.DataFrame): Input features
            
        Returns:
            tuple: (predictions, probabilities)
        """
        if self.model is None:
            raise ValueError("No trained model available for prediction")
        
        # Ensure features are in correct order
        if isinstance(X, pd.DataFrame):
            # Reorder columns to match training data
            X = X.reindex(columns=self.feature_names, fill_value=0)
            # Scale features
            X_scaled = self.scaler.transform(X)
        else:
            X_scaled = self.scaler.transform(X)
        
        # Make predictions
        predictions = self.model.predict(X_scaled)
        probabilities = self.model.predict_proba(X_scaled)[:, 1]
        
        return predictions, probabilities


def run_training_pipeline(data_path, output_dir='models', target_col='readmitted'):
    """
    Execute the complete training pipeline.
    
    Args:
        data_path (str): Path to training data CSV
        output_dir (str): Directory to save model artifacts
        target_col (str): Name of target column
        
    Returns:
        ReadmissionPredictor: Trained predictor instance
    """
    print("=" * 60)
    print("HOSPITAL READMISSION PREDICTION - TRAINING PIPELINE")
    print("=" * 60)
    
    # Initialize predictor
    predictor = ReadmissionPredictor(random_state=42)
    
    # Step 1: Load data
    print("\n[Step 1/7] Loading data...")
    df = predictor.load_data(data_path)
    
    # Step 2: Feature engineering
    print("\n[Step 2/7] Performing feature engineering...")
    df_engineered = predictor.advanced_feature_engineering(df)
    
    # Step 3: Preprocess data
    print("\n[Step 3/7] Preprocessing data...")
    X_processed, y, feature_names = predictor.preprocess_data(df_engineered, target_col=target_col)
    
    # Step 4: Apply SMOTE for class imbalance
    print("\n[Step 4/7] Applying SMOTE...")
    X_resampled, y_resampled = predictor.apply_smote(X_processed, y)
    
    # Step 5: Split data for validation
    print("\n[Step 5/7] Splitting data for validation...")
    X_train, X_val, y_train, y_val = train_test_split(
        X_resampled, y_resampled, 
        test_size=0.2, 
        random_state=42,
        stratify=y_resampled
    )
    print(f"Training set: {X_train.shape[0]} samples")
    print(f"Validation set: {X_val.shape[0]} samples")
    
    # Step 6: Hyperparameter optimization
    print("\n[Step 6/7] Optimizing hyperparameters...")
    best_params = predictor.optimize_hyperparameters(X_train, y_train, n_iter=50, cv_folds=5)
    
    # Step 7: Train final model
    print("\n[Step 7/7] Training final model...")
    predictor.train_model(X_train, y_train, params=best_params)
    
    # Evaluate on validation set
    print("\n" + "=" * 60)
    print("VALIDATION SET EVALUATION")
    print("=" * 60)
    metrics = predictor.evaluate_model(X_val, y_val)
    
    # Get feature importance
    print("\n" + "=" * 60)
    print("FEATURE IMPORTANCE ANALYSIS")
    print("=" * 60)
    predictor.get_feature_importance(top_n=20)
    
    # Compute SHAP values
    print("\n" + "=" * 60)
    print("SHAP ANALYSIS")
    print("=" * 60)
    shap_values = predictor.compute_shap_values(X_val, max_samples=500)
    
    # Save model
    print("\n" + "=" * 60)
    print("SAVING MODEL ARTIFACTS")
    print("=" * 60)
    model_path = predictor.save_model(output_dir=output_dir)
    
    print("\n" + "=" * 60)
    print("TRAINING PIPELINE COMPLETE")
    print("=" * 60)
    print(f"Model saved to: {model_path}")
    print(f"Validation ROC-AUC: {metrics['roc_auc']:.4f}")
    print(f"Validation Accuracy: {metrics['accuracy']:.4f}")
    
    return predictor


if __name__ == "__main__":
    # Example usage - adjust path to your data file
    # python model.py
    try:
        # Update this path to your actual data file location
        data_file = "data/hospital_readmission_data.csv"
        
        if os.path.exists(data_file):
            predictor = run_training_pipeline(data_file)
        else:
            print(f"Data file not found at: {data_file}")
            print("Please update the data_file path in model.py to your actual data location")
    except Exception as e:
        print(f"Error in training pipeline: {str(e)}")
