from pathlib import Path
import joblib
import numpy as np
import pandas as pd

# 13 Raw input features expected by the imputer
RAW_FEATURES = [
    'age',
    'sex',
    'trestbps',
    'chol',
    'fbs',
    'thalach',
    'exang',
    'oldpeak',
    'slope',
    'ca',
    'thal',
    'cp',
    'restecg',
]

# 18 Final one-hot encoded features expected by your trained model
EXPECTED_FEATURES = [
    'age',
    'sex',
    'trestbps',
    'chol',
    'fbs',
    'thalach',
    'exang',
    'oldpeak',
    'ca',
    'cp_2.0',
    'cp_3.0',
    'cp_4.0',
    'restecg_1.0',
    'restecg_2.0',
    'thal_6.0',
    'thal_7.0',
    'slope_2.0',
    'slope_3.0',
]

# Valid discrete category values
VALID_CATEGORIES = {
    'cp': [1.0, 2.0, 3.0, 4.0],
    'restecg': [0.0, 1.0, 2.0],
    'thal': [3.0, 6.0, 7.0],
    'slope': [1.0, 2.0, 3.0],
}

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = PROJECT_ROOT / "models"
BUNDLE_PATH = MODELS_DIR / "imputation_bundle.pkl"


def load_imputer():
    """Loads strictly the imputer object from the bundle."""
    if not BUNDLE_PATH.exists():
        raise FileNotFoundError(
            f"Preprocessing bundle not found at target location: {BUNDLE_PATH}"
        )

    artifacts = joblib.load(BUNDLE_PATH)
    if isinstance(artifacts, dict):
        return artifacts.get("imputer")
    return artifacts


# Load imputer artifact on web app startup
loaded_imputer = load_imputer()


def map_to_nearest_category(
    df: pd.DataFrame, cat_dict: dict
) -> pd.DataFrame:
    """Snaps continuous MICE float outputs back to valid discrete categories."""
    df_copy = df.copy()
    for col, valid_values in cat_dict.items():
        if col in df_copy.columns:
            valid_cats = np.array(valid_values)
            vals = df_copy[col].to_numpy()
            closest_idx = np.abs(vals[:, None] - valid_cats).argmin(axis=1)
            df_copy[col] = valid_cats[closest_idx]
    return df_copy


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans patient dict, handles missing values, and aligns raw 13 features for the imputer."""
    df = df.copy()
    df = df.replace(['?', '', np.inf, -np.inf, None], np.nan)

    for column in df.columns:
        df[column] = pd.to_numeric(df[column], errors='coerce')

    if 'chol' in df.columns:
        df['chol'] = df['chol'].replace(0, np.nan)

    # Reindex forces raw 13 columns in exact order expected by imputer
    raw_cols = (
        list(loaded_imputer.feature_names_in_)
        if (loaded_imputer is not None and hasattr(loaded_imputer, "feature_names_in_"))
        else RAW_FEATURES
    )
    return df.reindex(columns=raw_cols)


def impute_data(df: pd.DataFrame) -> pd.DataFrame:
    """Imputes missing raw values and snaps float output to valid category codes."""
    df_copy = df.copy()

    if loaded_imputer is not None:
        imputed_array = loaded_imputer.transform(df_copy)
        df_copy = pd.DataFrame(
            imputed_array, columns=df_copy.columns, index=df_copy.index
        )

    # Force continuous float categories to nearest valid discrete integers
    df_copy = map_to_nearest_category(df_copy, VALID_CATEGORIES)
    return df_copy


def encode_data(df: pd.DataFrame) -> pd.DataFrame:
    """Encodes discrete categories using pd.Categorical to guarantee dummy alignment on 1 row."""
    df_copy = df.copy()

    # Pre-assign categorical types with fixed categories so get_dummies generates all dummy columns
    df_copy['cp'] = pd.Categorical(df_copy['cp'], categories=VALID_CATEGORIES['cp'])
    df_copy['restecg'] = pd.Categorical(df_copy['restecg'], categories=VALID_CATEGORIES['restecg'])
    df_copy['thal'] = pd.Categorical(df_copy['thal'], categories=VALID_CATEGORIES['thal'])
    df_copy['slope'] = pd.Categorical(df_copy['slope'], categories=VALID_CATEGORIES['slope'])

    # One-hot encode with drop_first=True
    df_encoded = pd.get_dummies(
        df_copy,
        columns=['cp', 'restecg', 'thal', 'slope'],
        drop_first=True,
        dtype=float
    )

    # Reindex guarantees the exact 18-feature order expected by your model
    return df_encoded.reindex(columns=EXPECTED_FEATURES, fill_value=0.0)


def preprocess(patient: dict) -> pd.DataFrame:
    """Pipeline: Raw Dict -> Clean (13 raw) -> Impute -> Encode (18 model features)"""
    df = pd.DataFrame([patient])
    df = clean_data(df)
    df = impute_data(df)
    df = encode_data(df)
    return df