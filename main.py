"""
Main Entry Point
=================
Orchestrates the full Patient Readmission and Resource Optimization pipeline:
    1. Generate synthetic healthcare data
    2. Execute SQL data wrangling pipeline
    3. Engineer ML features
    4. Train Random Forest classifier
    5. Generate SHAP explainability analysis
"""

import logging
from pathlib import Path

from src.data_generator import generate_dataset
from src.data_pipeline import build_analysis_dataset
from src.feature_engineering import engineer_features
from src.model import train_model
from src.shap_explainer import generate_shap_analysis

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

DB_PATH = Path(__file__).parent / "data" / "healthcare.db"
OUTPUT_DIR = Path(__file__).parent / "outputs"


def main() -> None:
    # Configure logging
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    logger = logging.getLogger("main")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 70)
    logger.info("PATIENT READMISSION AND RESOURCE OPTIMIZATION ENGINE")
    logger.info("=" * 70)

    # Step 1: Generate synthetic dataset
    logger.info("[STEP 1/5] Generating synthetic healthcare dataset...")
    generate_dataset(str(DB_PATH), n_patients=2000)

    # Step 2: Run SQL data wrangling pipeline
    logger.info("[STEP 2/5] Executing SQL data wrangling pipeline...")
    df = build_analysis_dataset(str(DB_PATH))

    # Step 3: Engineer features
    logger.info("[STEP 3/5] Engineering features for ML model...")
    X, y, encoders = engineer_features(df)

    # Step 4: Train Random Forest classifier
    logger.info("[STEP 4/5] Training Random Forest classifier...")
    model, X_test, y_test, y_pred, y_proba = train_model(X, y)

    # Step 5: Generate SHAP explainability analysis
    logger.info("[STEP 5/5] Generating SHAP explainability analysis...")
    generate_shap_analysis(model, X_test, y_test)

    logger.info("=" * 70)
    logger.info("Pipeline complete. All outputs saved to outputs/ directory.")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
