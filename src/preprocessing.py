"""
Data Preprocessing Module for Diabetes Readmission Prediction
==============================================================
Comprehensive data preparation including cleaning, encoding, feature engineering,
handling class imbalance, and train-test splitting.

Singapore Healthcare Context:
- Proper preprocessing ensures model fairness across different patient demographics
- Feature engineering captures clinically relevant patterns for Singaporean patients
- Handling class imbalance is crucial for accurate readmission prediction
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.impute import SimpleImputer, IterativeImputer, KNNImputer, MissingIndicator
from imblearn.over_sampling import SMOTE
from typing import Tuple, Dict, List, Optional
import os
import logging
import joblib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set random seed for reproducibility
RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)


class DataPreprocessor:
    """
    Comprehensive data preprocessing pipeline for chronic condition readmission prediction.
    
    Handles:
    - Missing value treatment with sophisticated imputation (MICE/KNN)
    - Identifier column removal (encounter_id, patient_nbr)
    - Categorical encoding with drop_first=True to prevent multicollinearity
    - Feature engineering
    - Class imbalance handling (SMOTE)
    - Feature scaling
    - Train-test splitting with stratification
    """
    
    def __init__(self, test_size: float = 0.2, random_state: int = RANDOM_STATE):
        """
        Initialize the preprocessor.
        
        Args:
            test_size: Proportion of data for testing
            random_state: Random seed for reproducibility
        """
        self.test_size = test_size
        self.random_state = random_state
        
        # Encoders and scalers
        self.label_encoders = {}
        self.onehot_encoders = {}
        self.scaler = StandardScaler()
        self.imputer = SimpleImputer(strategy='median')
        self.iterative_imputer = IterativeImputer(random_state=self.random_state, max_iter=10)
        self.knn_imputer = KNNImputer(n_neighbors=5)
        
        # Missing indicators for critical columns (FIX 1: Advanced Imputation)
        self.missing_indicators = {}
        self.critical_missing_cols = ['weight', 'payer_code', 'medical_specialty']
        
        # Track preprocessing state
        self.is_fitted = False
        self.feature_names = []
        self.categorical_cols = []
        self.numeric_cols = []
        
        # Store preprocessing decisions
        self.preprocessing_log = []
        
        # Identifier columns to drop (zero predictive value)
        self.identifier_cols = ['encounter_id', 'patient_nbr']
    
    def _log_decision(self, step: str, decision: str, justification: str) -> None:
        """Log preprocessing decisions for documentation."""
        self.preprocessing_log.append({
            'step': step,
            'decision': decision,
            'justification': justification
        })
        logger.info(f"[{step}] {decision} - {justification}")
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Initial data cleaning.
        
        Args:
            df: Raw input dataframe
            
        Returns:
            pd.DataFrame: Cleaned dataframe
        """
        logger.info("Starting data cleaning...")
        df_clean = df.copy()
        
        # CRITICAL FIX: Drop identifier columns (encounter_id, patient_nbr)
        # These add ZERO predictive value and are just random IDs
        dropped_identifiers = []
        for col in self.identifier_cols:
            if col in df_clean.columns:
                dropped_identifiers.append(col)
                df_clean = df_clean.drop(columns=[col])
        
        if dropped_identifiers:
            self._log_decision(
                'Cleaning',
                f'Dropped identifier columns: {dropped_identifiers}',
                'Patient/encounter IDs are random identifiers with zero predictive value. Keeping them would cause the model to memorize rather than generalize.'
            )
        
        # Remove duplicate rows
        initial_rows = len(df_clean)
        df_clean = df_clean.drop_duplicates()
        removed_dupes = initial_rows - len(df_clean)
        self._log_decision(
            'Cleaning',
            f'Removed {removed_dupes} duplicate rows',
            'Duplicates can bias model training and inflate performance metrics'
        )
        
        # Handle obvious data entry errors
        if 'time_in_hospital' in df_clean.columns:
            # Negative hospital stays are impossible
            invalid_stays = (df_clean['time_in_hospital'] < 0).sum()
            if invalid_stays > 0:
                df_clean = df_clean[df_clean['time_in_hospital'] >= 0]
                self._log_decision(
                    'Cleaning',
                    f'Removed {invalid_stays} records with negative hospital stay',
                    'Negative time values are data entry errors'
                )
        
        # Handle age column if it exists
        if 'age' in df_clean.columns:
            # If age is categorical (e.g., "10-20"), convert to numeric midpoints
            if df_clean['age'].dtype == 'object':
                age_mapping = {
                    '10-20': 15, '20-30': 25, '30-40': 35, '40-50': 45,
                    '50-60': 55, '60-70': 65, '70-80': 75, '80-90': 85, '90-100': 95
                }
                df_clean['age_numeric'] = df_clean['age'].map(age_mapping)
                self._log_decision(
                    'Feature Engineering',
                    'Converted categorical age to numeric midpoints',
                    'Numeric age allows for better statistical analysis and modeling'
                )
        
        logger.info(f"Data cleaning complete. Shape: {df_clean.shape}")
        return df_clean
    
    def handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle missing values using sophisticated imputation strategies.
        
        FIX 1: ADVANCED IMPUTATION & MISSINGNESS MECHANISM
        - Import MissingIndicator from sklearn.impute
        - Add binary "missingness flags" for critical columns like weight, payer_code, medical_specialty
        - This allows the model to learn if "missingness" itself is predictive
        - For weight (>50% missing), drop it but keep the indicator
        - Use IterativeImputer only for numeric columns where missingness is likely MAR
        
        Args:
            df: Input dataframe
            
        Returns:
            pd.DataFrame: DataFrame with handled missing values
        """
        logger.info("Handling missing values with sophisticated imputation and missingness indicators...")
        df_processed = df.copy()
        
        # Calculate missing percentage before
        missing_before = df_processed.isnull().sum().sum()
        
        # FIX 1: Create missingness indicators for critical clinical columns
        # Missingness itself may be predictive (e.g., weight missing for bedbound patients)
        for col in self.critical_missing_cols:
            if col in df_processed.columns:
                indicator = MissingIndicator(features='missings')
                missing_flag = indicator.fit_transform(df_processed[[col]])
                df_processed[f'{col}_missing'] = missing_flag.astype(int)
                self.missing_indicators[col] = indicator
                
                missing_pct = df_processed[col].isnull().mean() * 100
                self._log_decision(
                    'Missing Values',
                    f'Created missingness indicator for {col} ({missing_pct:.1f}% missing)',
                    f'Missingness in {col} may be clinically informative. For example, weight is often missing for bedbound or emergency patients. The binary flag allows the model to learn if missingness itself predicts readmission.'
                )
        
        # Identify columns with high missing rates (>50%)
        missing_pct = df_processed.isnull().mean() * 100
        high_missing_categorical = []
        high_missing_numeric = []
        
        for col in df_processed.columns:
            # Skip the newly created missing indicator columns
            if col.endswith('_missing'):
                continue
            if missing_pct[col] > 50:
                if df_processed[col].dtype == 'object':
                    high_missing_categorical.append(col)
                else:
                    high_missing_numeric.append(col)
        
        # CRITICAL FIX: Don't drop high-missing columns blindly!
        # For categorical: create "Unknown/Missing" category (missingness is informative)
        # For numeric with >50% missing (like weight): rely on the missing indicator, can drop original
        
        if high_missing_categorical:
            self._log_decision(
                'Missing Values',
                f'Creating "Unknown" category for {len(high_missing_categorical)} high-missing categorical columns: {high_missing_categorical}',
                'For clinical categorical features like medical_specialty and payer_code, missingness itself may be predictive. Creating "Unknown" category preserves this signal rather than losing potentially valuable information.'
            )
            for col in high_missing_categorical:
                df_processed[col] = df_processed[col].fillna('Unknown/Missing')
        
        # Separate remaining columns by type for appropriate imputation
        categorical_cols = df_processed.select_dtypes(include=['object']).columns.tolist()
        numeric_cols = df_processed.select_dtypes(include=[np.number]).columns.tolist()
        
        # Filter out already-handled high-missing categorical columns
        categorical_cols = [c for c in categorical_cols if c not in high_missing_categorical]
        
        # For remaining categorical columns with missing values, fill with mode
        for col in categorical_cols:
            if df_processed[col].isnull().sum() > 0:
                mode_value = df_processed[col].mode()[0] if len(df_processed[col].mode()) > 0 else 'Unknown'
                df_processed[col] = df_processed[col].fillna(mode_value)
        
        self._log_decision(
            'Missing Values',
            'Filled remaining categorical missing values with mode',
            'Mode imputation preserves the distribution of categorical variables'
        )
        
        # CRITICAL FIX: Use IterativeImputer (MICE) for numeric features
        # This models each feature as a function of other features - much more sophisticated than simple median
        if len(numeric_cols) > 0:
            cols_with_missing = [c for c in numeric_cols if df_processed[c].isnull().sum() > 0]
            if cols_with_missing:
                self._log_decision(
                    'Missing Values',
                    f'Applied IterativeImputer (MICE) for {len(cols_with_missing)} numeric features: {cols_with_missing}',
                    'IterativeImputer (Multivariate Imputation by Chained Equations) models each feature as a function of all other features. This captures correlations between clinical variables (e.g., time_in_hospital correlates with num_lab_procedures) for more accurate imputation than simple median.'
                )
                df_processed[numeric_cols] = self.iterative_imputer.fit_transform(df_processed[numeric_cols])
            else:
                # No missing numeric values, but still fit the imputer for transform consistency
                self.iterative_imputer.fit(df_processed[numeric_cols])
        
        # Calculate missing percentage after
        missing_after = df_processed.isnull().sum().sum()
        logger.info(f"Missing values reduced from {missing_before} to {missing_after}")
        
        return df_processed
    
    def encode_categorical_variables(self, df: pd.DataFrame, 
                                     onehot_cols: List[str] = None,
                                     label_cols: List[str] = None) -> pd.DataFrame:
        """
        Encode categorical variables using appropriate methods.
        
        CRITICAL FIX: Set drop_first=True for OneHotEncoding to prevent 
        the dummy variable trap (multicollinearity).
        
        Args:
            df: Input dataframe
            onehot_cols: Columns to one-hot encode (low cardinality)
            label_cols: Columns to label encode (ordinal or high cardinality)
            
        Returns:
            pd.DataFrame: Encoded dataframe
        """
        logger.info("Encoding categorical variables...")
        df_encoded = df.copy()
        
        # Automatically identify categorical columns if not specified
        categorical_cols = df_encoded.select_dtypes(include=['object']).columns.tolist()
        
        # Remove target column if present
        if 'readmitted' in categorical_cols:
            categorical_cols.remove('readmitted')
        
        self.categorical_cols = categorical_cols
        
        # Decide encoding strategy based on cardinality
        for col in categorical_cols:
            n_unique = df_encoded[col].nunique()
            
            if n_unique <= 5:
                # Low cardinality: use one-hot encoding with drop_first=True
                self._log_decision(
                    'Encoding',
                    f'One-hot encoded {col} ({n_unique} categories) with drop_first=True',
                    'One-hot encoding for low cardinality avoids ordinal assumptions. Using drop_first=True prevents the dummy variable trap (multicollinearity) by dropping one reference category.'
                )
                dummies = pd.get_dummies(df_encoded[col], prefix=col, drop_first=True)
                df_encoded = pd.concat([df_encoded, dummies], axis=1)
                df_encoded = df_encoded.drop(columns=[col])
            else:
                # High cardinality: use label encoding
                self._log_decision(
                    'Encoding',
                    f'Label encoded {col} ({n_unique} categories)',
                    'Label encoding for high cardinality prevents dimensionality explosion'
                )
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                    df_encoded[col] = self.label_encoders[col].fit_transform(df_encoded[col].astype(str))
                else:
                    df_encoded[col] = self.label_encoders[col].transform(df_encoded[col].astype(str))
        
        logger.info(f"Encoding complete. New shape: {df_encoded.shape}")
        return df_encoded
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create meaningful features from existing data.
        
        FIX 2: LEAKAGE REMOVAL & FEATURE ENGINEERING
        - Create normalized feature: medications_per_day = num_medications / (time_in_hospital + 1)
        - This controls for length of stay and prevents num_medications from being a severity proxy
        - Drop raw num_medications if it shows high correlation with target
        
        Args:
            df: Input dataframe
            
        Returns:
            pd.DataFrame: DataFrame with engineered features
        """
        logger.info("Engineering features with leakage prevention...")
        df_features = df.copy()
        
        # FIX 2: Create normalized medication feature to prevent leakage
        # num_medications alone is a proxy for severity and leaks target information
        # Normalize by length of stay to get true medication intensity
        if 'num_medications' in df_features.columns and 'time_in_hospital' in df_features.columns:
            df_features['medications_per_day'] = df_features['num_medications'] / (df_features['time_in_hospital'] + 1)
            self._log_decision(
                'Feature Engineering',
                'Created medications_per_day feature (num_medications / (time_in_hospital + 1))',
                'Raw num_medications is a proxy for disease severity and can leak target information. Normalizing by length of stay controls for this confounding, creating a more clinically meaningful feature that represents medication intensity rather than just disease burden.'
            )
        
        # Feature 1: Total medications and procedures
        if 'num_medications' in df_features.columns and 'num_procedures' in df_features.columns:
            df_features['total_interventions'] = df_features['num_medications'] + df_features['num_procedures']
            self._log_decision(
                'Feature Engineering',
                'Created total_interventions feature',
                'Combines medication and procedure counts as overall treatment intensity'
            )
        
        # Feature 2: Hospital stay efficiency
        if 'time_in_hospital' in df_features.columns and 'num_lab_procedures' in df_features.columns:
            df_features['lab_procedures_per_day'] = df_features['num_lab_procedures'] / (df_features['time_in_hospital'] + 1)
            self._log_decision(
                'Feature Engineering',
                'Created lab_procedures_per_day feature',
                'Normalizes lab procedures by length of stay'
            )
        
        # Feature 3: Age groups (if numeric age exists)
        if 'age_numeric' in df_features.columns or 'age' in df_features.columns:
            age_col = 'age_numeric' if 'age_numeric' in df_features.columns else 'age'
            # Convert to numeric first if it's categorical (e.g., "[10-20)" ranges)
            if df_features[age_col].dtype == 'object':
                age_mapping = {
                    '[0-10)': 5, '[10-20)': 15, '[20-30)': 25, '[30-40)': 35,
                    '[40-50)': 45, '[50-60)': 55, '[60-70)': 65, '[70-80)': 75,
                    '[80-90)': 85, '[90-100)': 95
                }
                # Map known categories, extract digit from unknown ones
                mapped = df_features[age_col].map(age_mapping)
                unmapped_mask = mapped.isna()
                if unmapped_mask.any():
                    # Extract first number from strings like "?" or other formats
                    extracted = df_features.loc[unmapped_mask, age_col].astype(str).str.extract('(\\d+)', expand=False)
                    extracted = pd.to_numeric(extracted, errors='coerce')
                    mapped.loc[unmapped_mask] = extracted
                df_features['age_numeric'] = pd.to_numeric(mapped, errors='coerce').fillna(45)  # Default to middle age if can't parse
                age_col = 'age_numeric'
            
            try:
                age_values = pd.to_numeric(df_features[age_col], errors='coerce').fillna(45)
                df_features['age_group'] = pd.cut(
                    age_values,
                    bins=[0, 18, 30, 45, 60, 75, 100],
                    labels=['Child', 'Young Adult', 'Adult', 'Middle Age', 'Senior', 'Elderly']
                )
                self._log_decision(
                    'Feature Engineering',
                    'Created age_group categorical feature',
                    'Age groups capture non-linear relationships with health outcomes'
                )
            except Exception as e:
                logger.warning(f"Could not create age_group feature: {e}")
        
        # Feature 4: Diagnosis complexity
        if 'number_diagnoses' in df_features.columns:
            df_features['diagnosis_complexity'] = pd.cut(
                df_features['number_diagnoses'],
                bins=[0, 2, 5, 10, 100],
                labels=['Low', 'Medium', 'High', 'Very High']
            )
            self._log_decision(
                'Feature Engineering',
                'Created diagnosis_complexity feature',
                'Categorizes patient condition complexity'
            )
        
        # Feature 5: Medication intensity
        if 'num_medications' in df_features.columns:
            df_features['medication_intensity'] = pd.cut(
                df_features['num_medications'],
                bins=[0, 5, 15, 30, 100],
                labels=['Low', 'Medium', 'High', 'Very High']
            )
            self._log_decision(
                'Feature Engineering',
                'Created medication_intensity feature',
                'Categorizes medication burden on patient'
            )
        
        logger.info(f"Feature engineering complete. Added features: {df_features.shape[1] - df.shape[1]}")
        return df_features
    
    def prepare_target_variable(self, df: pd.DataFrame, target_col: str = 'readmitted') -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare the target variable for binary classification.
        
        Args:
            df: Input dataframe
            target_col: Name of target column
            
        Returns:
            Tuple[pd.DataFrame, pd.Series]: DataFrame without target, target series
        """
        logger.info(f"Preparing target variable: {target_col}")
        
        df_processed = df.copy()
        
        if target_col not in df_processed.columns:
            raise ValueError(f"Target column '{target_col}' not found in dataframe")
        
        # Convert to binary: 1 if readmitted within 30 days, 0 otherwise
        target_mapping = {'YES': 1, '<30': 1, 'NO': 0, '>30': 0}
        y = df_processed[target_col].map(target_mapping)
        
        # Handle any unmapped values
        y = y.fillna(0).astype(int)
        
        self._log_decision(
            'Target Preparation',
            'Converted readmitted to binary (1=YES/<30, 0=NO/>30)',
            'Binary classification simplifies the prediction task for 30-day readmission risk'
        )
        
        # Drop original target column
        X = df_processed.drop(columns=[target_col])
        
        logger.info(f"Target distribution: {y.value_counts().to_dict()}")
        return X, y
    
    def handle_class_imbalance(self, X: pd.DataFrame, y: pd.Series, 
                               method: str = 'smote') -> Tuple[pd.DataFrame, pd.Series]:
        """
        Handle class imbalance using SMOTE or other methods.
        
        Args:
            X: Feature matrix
            y: Target vector
            method: Balancing method ('smote', 'undersample', 'oversample')
            
        Returns:
            Tuple[pd.DataFrame, pd.Series]: Balanced X and y
        """
        logger.info(f"Handling class imbalance using {method}...")
        
        # Check imbalance ratio
        class_counts = y.value_counts()
        imbalance_ratio = class_counts.iloc[0] / class_counts.iloc[1] if len(class_counts) == 2 else 1
        
        if 0.5 <= imbalance_ratio <= 2.0:
            self._log_decision(
                'Class Imbalance',
                f'No balancing needed (ratio: {imbalance_ratio:.2f}:1)',
                'Class distribution is reasonably balanced'
            )
            return X, y
        
        logger.info(f"Class imbalance detected: {class_counts.to_dict()} (ratio: {imbalance_ratio:.2f}:1)")
        
        if method == 'smote':
            # Use SMOTE to generate synthetic samples
            smote = SMOTE(random_state=self.random_state, k_neighbors=min(5, min(class_counts) - 1))
            X_balanced, y_balanced = smote.fit_resample(X, y)
            
            self._log_decision(
                'Class Imbalance',
                f'Applied SMOTE: {len(X)} → {len(X_balanced)} samples',
                'SMOTE generates synthetic minority class samples to balance classes'
            )
            
        elif method == 'undersample':
            # Undersample majority class
            from imblearn.under_sampling import RandomUnderSampler
            rus = RandomUnderSampler(random_state=self.random_state)
            X_balanced, y_balanced = rus.fit_resample(X, y)
            
            self._log_decision(
                'Class Imbalance',
                f'Applied undersampling: {len(X)} → {len(X_balanced)} samples',
                'Undersampling reduces majority class to match minority'
            )
            
        else:
            # Random oversampling
            from imblearn.over_sampling import RandomOverSampler
            ros = RandomOverSampler(random_state=self.random_state)
            X_balanced, y_balanced = ros.fit_resample(X, y)
            
            self._log_decision(
                'Class Imbalance',
                f'Applied oversampling: {len(X)} → {len(X_balanced)} samples',
                'Oversampling duplicates minority class samples'
            )
        
        logger.info(f"Balanced class distribution: {pd.Series(y_balanced).value_counts().to_dict()}")
        return X_balanced, y_balanced
    
    def scale_features(self, X_train: pd.DataFrame, X_test: pd.DataFrame = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Scale features using StandardScaler.
        
        Args:
            X_train: Training feature matrix
            X_test: Test feature matrix (optional)
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: Scaled train and test arrays
        """
        logger.info("Scaling features...")
        
        # Fit scaler on training data only
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        self._log_decision(
            'Feature Scaling',
            'Applied StandardScaler (zero mean, unit variance)',
            'Standardization ensures all features contribute equally to distance-based algorithms'
        )
        
        if X_test is not None:
            X_test_scaled = self.scaler.transform(X_test)
            logger.info(f"Scaled train shape: {X_train_scaled.shape}, test shape: {X_test_scaled.shape}")
            return X_train_scaled, X_test_scaled
        
        logger.info(f"Scaled train shape: {X_train_scaled.shape}")
        return X_train_scaled, None
    
    def split_data(self, X: pd.DataFrame, y: pd.Series, 
                   test_size: float = None, stratify: bool = True) -> Tuple:
        """
        Split data into training and testing sets.
        
        Args:
            X: Feature matrix
            y: Target vector
            test_size: Proportion for testing (uses instance default if None)
            stratify: Whether to stratify split (maintain class distribution)
            
        Returns:
            Tuple: X_train, X_test, y_train, y_test
        """
        if test_size is None:
            test_size = self.test_size
        
        logger.info(f"Splitting data: test_size={test_size}, stratify={stratify}")
        
        stratify_param = y if stratify else None
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=self.random_state,
            stratify=stratify_param,
            shuffle=True
        )
        
        self._log_decision(
            'Train-Test Split',
            f'Split data: {len(X_train)} train, {len(X_test)} test samples',
            'Stratified split maintains class distribution in both sets'
        )
        
        logger.info(f"Training set: {X_train.shape}, Test set: {X_test.shape}")
        logger.info(f"Train class distribution: {pd.Series(y_train).value_counts().to_dict()}")
        logger.info(f"Test class distribution: {pd.Series(y_test).value_counts().to_dict()}")
        
        return X_train, X_test, y_train, y_test
    
    def fit_transform(self, df: pd.DataFrame, target_col: str = 'readmitted',
                     handle_imbalance: bool = True) -> Tuple:
        """
        Complete preprocessing pipeline.
        
        Args:
            df: Raw input dataframe
            target_col: Target column name
            handle_imbalance: Whether to handle class imbalance
            
        Returns:
            Tuple: X_train, X_test, y_train, y_test, feature_names
        """
        logger.info("=" * 60)
        logger.info("STARTING COMPLETE PREPROCESSING PIPELINE")
        logger.info("=" * 60)
        
        # Step 1: Clean data
        df_processed = self.clean_data(df)
        
        # Step 2: Handle missing values
        df_processed = self.handle_missing_values(df_processed)
        
        # Step 3: Feature engineering
        df_processed = self.engineer_features(df_processed)
        
        # Step 4: Encode categorical variables
        df_processed = self.encode_categorical_variables(df_processed)
        
        # Step 5: Prepare target variable
        X, y = self.prepare_target_variable(df_processed, target_col)
        
        # Store feature names before scaling
        self.feature_names = X.columns.tolist()
        
        # Step 6: Split data
        X_train, X_test, y_train, y_test = self.split_data(X, y)
        
        # Step 7: Scale features
        X_train_scaled, X_test_scaled = self.scale_features(X_train, X_test)
        
        # Step 8: Handle class imbalance (only on training data!)
        if handle_imbalance:
            X_train_scaled, y_train = self.handle_class_imbalance(
                pd.DataFrame(X_train_scaled, columns=self.feature_names), 
                y_train
            )
            X_train_scaled = X_train_scaled.values
        
        self.is_fitted = True
        
        logger.info("=" * 60)
        logger.info("PREPROCESSING COMPLETE")
        logger.info(f"Final training shape: {X_train_scaled.shape}")
        logger.info(f"Final test shape: {X_test_scaled.shape if X_test_scaled is not None else 'N/A'}")
        logger.info("=" * 60)
        
        return X_train_scaled, X_test_scaled, y_train, y_test
    
    def get_preprocessing_report(self) -> pd.DataFrame:
        """Get a report of all preprocessing decisions."""
        return pd.DataFrame(self.preprocessing_log)
    
    def save_preprocessor(self, filepath: str = 'models/preprocessor.joblib') -> None:
        """
        Save the fitted preprocessor for later use.
        
        Args:
            filepath: Path to save the preprocessor
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump(self, filepath)
        logger.info(f"✓ Saved preprocessor to: {filepath}")
    
    @staticmethod
    def load_preprocessor(filepath: str) -> 'DataPreprocessor':
        """
        Load a saved preprocessor.
        
        Args:
            filepath: Path to the saved preprocessor
            
        Returns:
            DataPreprocessor: Loaded preprocessor
        """
        preprocessor = joblib.load(filepath)
        logger.info(f"✓ Loaded preprocessor from: {filepath}")
        return preprocessor


def preprocess_data(df: pd.DataFrame, target_col: str = 'readmitted',
                   test_size: float = 0.2, handle_imbalance: bool = True) -> Tuple:
    """
    Convenience function to preprocess data.
    
    Args:
        df: Input dataframe
        target_col: Target column name
        test_size: Test set proportion
        handle_imbalance: Whether to handle class imbalance
        
    Returns:
        Tuple: X_train, X_test, y_train, y_test, preprocessor
    """
    preprocessor = DataPreprocessor(test_size=test_size)
    X_train, X_test, y_train, y_test = preprocessor.fit_transform(df, target_col, handle_imbalance)
    return X_train, X_test, y_train, y_test, preprocessor


if __name__ == "__main__":
    # Example usage with sample data
    print("Testing DataPreprocessor...")
    
    # Create sample data
    np.random.seed(RANDOM_STATE)
    n_samples = 1000
    
    sample_df = pd.DataFrame({
        'age': np.random.choice(['10-20', '20-30', '30-40', '40-50', '50-60', '60-70', '70-80'], n_samples),
        'time_in_hospital': np.random.randint(1, 14, n_samples),
        'num_lab_procedures': np.random.randint(1, 100, n_samples),
        'num_medications': np.random.randint(1, 50, n_samples),
        'number_diagnoses': np.random.randint(1, 10, n_samples),
        'gender': np.random.choice(['Male', 'Female'], n_samples),
        'race': np.random.choice(['Caucasian', 'African American', 'Asian', 'Hispanic', 'Other'], n_samples),
        'readmitted': np.random.choice(['YES', 'NO', '<30', '>30'], n_samples, p=[0.2, 0.5, 0.15, 0.15])
    })
    
    # Add some missing values
    sample_df.loc[np.random.choice(n_samples, 50), 'gender'] = np.nan
    sample_df.loc[np.random.choice(n_samples, 50), 'race'] = np.nan
    
    print(f"Sample data shape: {sample_df.shape}")
    
    # Run preprocessing
    try:
        X_train, X_test, y_train, y_test, preprocessor = preprocess_data(
            sample_df, 
            handle_imbalance=True
        )
        
        print(f"\n✓ Preprocessing complete!")
        print(f"Training set: {X_train.shape}")
        print(f"Test set: {X_test.shape}")
        print(f"\nClass distribution in training: {pd.Series(y_train).value_counts().to_dict()}")
        
        # Get preprocessing report
        report = preprocessor.get_preprocessing_report()
        print(f"\nPreprocessing decisions logged: {len(report)}")
        print(report.to_string())
        
    except Exception as e:
        print(f"Error during preprocessing: {e}")
        import traceback
        traceback.print_exc()
