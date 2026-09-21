# Patient Readmission and Resource Optimization Engine

A full-stack data science pipeline that predicts 30-day hospital readmissions using complex SQL data wrangling, a Random Forest classifier, and SHAP-based model interpretability. The system is designed to provide actionable clinical insights for hospital administrators and care coordinators.

---

## Problem Statement

Hospital readmissions within 30 days of discharge are a significant quality indicator and a major cost driver in healthcare. The Centers for Medicare and Medicaid Services (CMS) penalizes hospitals with excess readmission rates, making accurate prediction and intervention a critical operational priority.

This engine addresses the problem end-to-end: from raw relational data spread across multiple clinical tables, through complex SQL transformations, to a predictive model with full explainability.

---

## SQL Pipeline

The SQL layer handles the data wrangling across four normalized clinical tables. Each script addresses a specific analytical requirement:

### 01 - Schema Definition (`01_create_schema.sql`)
Creates the relational schema with proper foreign key constraints, CHECK constraints for data integrity, and performance indexes.

### 02 - Master Patient View (`02_master_patient_view.sql`)
Joins patients, admissions, diagnoses, and treatments into a unified view of each patient's hospital journey. Applies data quality rules:
- Filters incomplete records (missing discharge dates)
- Handles date anomalies (discharge before admission)
- Aggregates treatment data via subquery to prevent row duplication
- Restricts to primary diagnoses only

### 03 - Readmission Logic (`03_readmission_logic.sql`)
Uses Common Table Expressions (CTEs) and the `LEAD()` window function to calculate the exact number of days between each discharge and the next admission for the same patient. Flags 30-day readmissions using the CMS standard definition.

### 04 - Severity Classification (`04_severity_classification.sql`)
Applies multi-factor `CASE` statements to classify admission severity based on:
- ICD-10 diagnosis code grouping (Cardiovascular, Respiratory, Neoplasm, etc.)
- Length of stay thresholds
- Admission type (Emergency, Urgent, Elective)
- Procedure count

Produces a composite severity score and categorical severity level (Critical, Severe, Moderate, Mild).

---

## ML Pipeline

### Random Forest Classifier
- Stratified train-test split to preserve class distribution
- `class_weight="balanced"` to handle the inherent class imbalance in readmission data
- 5-fold cross-validated ROC-AUC evaluation
- Generates confusion matrix, ROC curve, and feature importance plots

### SHAP Explainability
- **Beeswarm Plot**: Global view of which features push predictions toward readmission vs. non-readmission
- **Bar Plot**: Mean absolute SHAP values ranked by importance
- **Waterfall Plot**: Individual patient explanation showing exactly why a specific patient was flagged as high-risk
- **Dependence Plot**: How the top feature's value interacts with readmission risk
- **Stakeholder Summary**: Plain-English briefing document with recommended actions for hospital administrators

---

## Project Structure

```
patient_readmission_engine/
|-- main.py                          # Pipeline orchestrator
|-- requirements.txt
|-- LICENSE
|-- .gitignore
|-- sql/
|   |-- 01_create_schema.sql         # Relational schema definition
|   |-- 02_master_patient_view.sql   # Multi-table JOIN with filtering
|   |-- 03_readmission_logic.sql     # CTE + LEAD() readmission identification
|   |-- 04_severity_classification.sql  # CASE-based severity scoring
|-- src/
|   |-- __init__.py
|   |-- data_generator.py            # Synthetic MIMIC-III-like data generation
|   |-- data_pipeline.py             # SQL execution and DataFrame assembly
|   |-- feature_engineering.py       # Encoding, imputation, feature selection
|   |-- model.py                     # Random Forest training and evaluation
|   |-- shap_explainer.py            # SHAP analysis and stakeholder reporting
|-- outputs/                         # Generated plots and reports (gitignored)
```

---

## Getting Started

### Prerequisites
- Python 3.10+

### Installation

```bash
git clone https://github.com/Nithillen/patient_readmission_engine.git
cd patient_readmission_engine
pip install -r requirements.txt
```

### Run

```bash
python main.py
```

The pipeline will:
1. Generate a synthetic dataset (2,000 patients, ~4,000+ admissions)
2. Execute the SQL wrangling pipeline
3. Engineer features and train the Random Forest model
4. Generate SHAP visualizations and a stakeholder briefing

All outputs (plots, reports) are saved to the `outputs/` directory.

---

## Technical Stack

| Component | Technology |
|-----------|-----------|
| Database | SQLite (portable, no server required) |
| SQL | CTEs, Window Functions (LEAD), Multi-table JOINs, CASE Statements |
| ML | Scikit-Learn (Random Forest), Stratified Splitting, Cross-Validation |
| Explainability | SHAP (TreeExplainer, Beeswarm, Waterfall, Dependence) |
| Visualization | Matplotlib, Seaborn |
| Data | Synthetic generator mirroring MIMIC-III schema |

---

## Disclaimer

This project uses entirely synthetic data. No real patient health information (PHI) is used or included. The system is designed for educational and research purposes to demonstrate the application of data science in healthcare operations.

---

## License

MIT License. See [LICENSE](LICENSE).
