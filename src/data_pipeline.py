"""
Data Pipeline Module
====================
Executes the SQL views against the SQLite database and produces a clean,
analysis-ready pandas DataFrame for the ML pipeline.
"""

import sqlite3
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

SQL_DIR = Path(__file__).parent.parent / "sql"


def _execute_sql_file(conn: sqlite3.Connection, filename: str) -> None:
    """Reads and executes a SQL file against the given connection."""
    filepath = SQL_DIR / filename
    with open(filepath, "r") as f:
        conn.executescript(f.read())
    logger.info(f"Executed: {filename}")


def build_analysis_dataset(db_path: str) -> pd.DataFrame:
    """
    Runs the full SQL pipeline and produces the final analysis-ready DataFrame.

    Steps:
        1. Creates the master patient view (multi-table join).
        2. Creates the readmission flags view (CTE + LEAD window function).
        3. Creates the severity classification view (CASE statements).
        4. Joins all three views into a single flat DataFrame.

    Args:
        db_path: Path to the SQLite database.

    Returns:
        pd.DataFrame ready for feature engineering and modeling.
    """
    conn = sqlite3.connect(db_path)

    # Execute SQL views in order
    _execute_sql_file(conn, "02_master_patient_view.sql")
    _execute_sql_file(conn, "03_readmission_logic.sql")
    _execute_sql_file(conn, "04_severity_classification.sql")

    # Build the final dataset by joining severity classification with readmission flags
    query = """
    SELECT
        s.patient_id,
        s.admission_id,
        s.gender,
        s.age_at_admission,
        s.ethnicity,
        s.insurance_type,
        s.marital_status,
        s.admission_type,
        s.discharge_location,
        s.length_of_stay_days,
        s.primary_icd_code,
        s.primary_diagnosis,
        s.diagnosis_group,
        s.total_procedures,
        s.total_treatment_cost,
        s.diagnosis_severity_score,
        s.los_severity_score,
        s.admission_type_score,
        s.procedure_severity_score,
        s.composite_severity_score,
        s.severity_level,
        r.days_to_readmission,
        r.is_30_day_readmission,
        r.readmission_risk_category
    FROM vw_severity_classification s
    LEFT JOIN vw_readmission_flags r
        ON s.admission_id = r.admission_id
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    logger.info(f"Analysis dataset built: {df.shape[0]} rows, {df.shape[1]} columns")
    logger.info(f"30-day readmission rate: {df['is_30_day_readmission'].mean():.2%}")

    return df
