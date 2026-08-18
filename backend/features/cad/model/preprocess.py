from pathlib import Path
import joblib
import numpy as np
import pandas as pd

# 13 Raw input features expected by the imputer
RAW_FEATURES = [
    'age',
    'sex',
    'cp',
    'trestbps',
    'chol',
    'fbs',
    'restecg',
    'thalach',
    'exang',
    'oldpeak',
    'slope',
    'ca',
    'thal',
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

def _get_models_dir() -> Path:
    current = Path(__file__).resolve().parent
    for _ in range(6):
        models_dir = current / "models"
        if models_dir.exists():
            return models_dir
        current = current.parent
    # Fallback default
    return Path(__file__).resolve().parents[4] / "models"

MODELS_DIR = _get_models_dir()
BUNDLE_PATH = MODELS_DIR / "imputation_bundle.pkl"

def patch_imputer(imputer):
    """Patch scikit-learn imputer attribute differences across versions."""
    if imputer is None:
        return imputer

    objects_to_patch = [imputer]
    if hasattr(imputer, "initial_imputer_") and imputer.initial_imputer_ is not None:
        objects_to_patch.append(imputer.initial_imputer_)

    for obj in objects_to_patch:
        if hasattr(obj, "_fit_dtype") and not hasattr(obj, "_fill_dtype"):
            obj._fill_dtype = obj._fit_dtype
        elif hasattr(obj, "_fill_dtype") and not hasattr(obj, "_fit_dtype"):
            obj._fit_dtype = obj._fill_dtype

        if hasattr(obj, "_is_empty_feature") and not hasattr(obj, "keep_empty_features"):
            obj.keep_empty_features = obj._is_empty_feature
        elif hasattr(obj, "keep_empty_features") and not hasattr(obj, "_is_empty_feature"):
            obj._is_empty_feature = obj.keep_empty_features

    return imputer

def load_imputer():
    """Loads strictly the imputer object from the bundle."""
    if not BUNDLE_PATH.exists():
        raise FileNotFoundError(
            f"Preprocessing bundle not found at target location: {BUNDLE_PATH}"
        )

    artifacts = joblib.load(BUNDLE_PATH)
    imputer = artifacts.get("imputer") if isinstance(artifacts, dict) else artifacts
    return patch_imputer(imputer)


loaded_imputer = load_imputer()


def map_to_nearest_category(val, valid_categories):
    if pd.isna(val):
        return val

    try:
        val_float = float(val)
        closest_cat = min(valid_categories, key=lambda c: abs(c - val_float))
        return closest_cat
    except (ValueError, TypeError):
        return val


def preprocess(patient_dict: dict) -> pd.DataFrame:
    raw_df = pd.DataFrame([patient_dict])

    for col in RAW_FEATURES:
        if col not in raw_df.columns or pd.isna(raw_df[col].iloc[0]) or raw_df[col].iloc[0] == '':
            raw_df[col] = np.nan

    raw_df = raw_df[RAW_FEATURES]

    if not raw_df.isna().any().any():
        imputed_array = raw_df.to_numpy(dtype=float)
    else:
        try:
            imputed_array = loaded_imputer.transform(raw_df)
        except Exception:
            # Fallback for unpickled IterativeImputer version incompatibilities on missing values
            from sklearn.impute import SimpleImputer
            fallback_imputer = SimpleImputer(strategy='median')
            imputed_array = fallback_imputer.fit_transform(raw_df)

    imputed_df = pd.DataFrame(imputed_array, columns=RAW_FEATURES)

    for cat_col, valid_cats in VALID_CATEGORIES.items():
        imputed_df[cat_col] = imputed_df[cat_col].apply(
            lambda x: map_to_nearest_category(x, valid_cats)
        )

    encoded_df = pd.get_dummies(
        imputed_df,
        columns=['cp', 'restecg', 'thal', 'slope'],
        dtype=float
    )

    for col in EXPECTED_FEATURES:
        if col not in encoded_df.columns:
            encoded_df[col] = 0.0

    encoded_df = encoded_df[EXPECTED_FEATURES]

    return encoded_df
