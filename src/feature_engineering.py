"""
Feature Engineering Module
==========================
Transforms the raw analysis dataset into model-ready features.
Handles categorical encoding, missing value imputation, and feature selection.
"""

import logging

import pandas as pd
from sklearn.preprocessing import LabelEncoder

logger = logging.getLogger(__name__)

# Features to encode as categorical
CATEGORICAL_FEATURES = [
    "gender",
    "ethnicity",
    "insurance_type",
    "marital_status",
    "admission_type",
    "discharge_location",
    "diagnosis_group",
    "severity_level",
]

# Numeric features to include directly
NUMERIC_FEATURES = [
    "age_at_admission",
    "length_of_stay_days",
    "total_procedures",
    "total_treatment_cost",
    "diagnosis_severity_score",
    "los_severity_score",
    "admission_type_score",
    "procedure_severity_score",
    "composite_severity_score",
]

TARGET_COLUMN = "is_30_day_readmission"


def engineer_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, dict]:
    """
    Transforms the analysis DataFrame into model-ready features and target.

    Steps:
        1. Drop rows with missing target.
        2. Fill missing categorical values with 'Unknown'.
        3. Fill missing numeric values with median.
        4. Label-encode all categorical columns.

    Args:
        df: Raw analysis DataFrame from the SQL pipeline.

    Returns:
        Tuple of (X features DataFrame, y target Series, label_encoders dict).
    """
    logger.info("Engineering features...")

    # Drop rows where the target is null
    df = df.dropna(subset=[TARGET_COLUMN]).copy()

    # Fill missing values
    for col in CATEGORICAL_FEATURES:
        df[col] = df[col].fillna("Unknown")

    for col in NUMERIC_FEATURES:
        df[col] = df[col].fillna(df[col].median())

    # Label encode categorical features
    encoders = {}
    for col in CATEGORICAL_FEATURES:
        le = LabelEncoder()
        df[col + "_encoded"] = le.fit_transform(df[col].astype(str))
        encoders[col] = le

    # Build feature matrix
    encoded_cat_cols = [c + "_encoded" for c in CATEGORICAL_FEATURES]
    feature_cols = NUMERIC_FEATURES + encoded_cat_cols

    X = df[feature_cols].copy()
    y = df[TARGET_COLUMN].astype(int).copy()

    # Create human-readable feature name mapping for SHAP
    feature_name_map = {}
    for col in NUMERIC_FEATURES:
        feature_name_map[col] = col.replace("_", " ").title()
    for col in CATEGORICAL_FEATURES:
        feature_name_map[col + "_encoded"] = col.replace("_", " ").title()

    X.columns = [feature_name_map.get(c, c) for c in X.columns]

    logger.info(f"Feature matrix shape: {X.shape}")
    logger.info(f"Target distribution:\n{y.value_counts().to_string()}")

    return X, y, encoders
