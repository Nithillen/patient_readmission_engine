/*
================================================================================
  ADMISSION SEVERITY CLASSIFICATION
  04_severity_classification.sql
================================================================================
  Categorizes the severity of each admission based on a combination of:
    1. Primary diagnosis ICD code grouping (cardiac, respiratory, etc.)
    2. Length of stay (longer stays often indicate higher acuity)
    3. Number of procedures performed
    4. Admission type (Emergency vs Elective)

  Severity Levels:
    - Critical   : High-acuity diagnosis group + extended stay + emergency
    - Severe     : Significant diagnosis or extended stay
    - Moderate   : Standard admission profile
    - Mild       : Short stay, elective, low procedure count
================================================================================
*/

CREATE VIEW IF NOT EXISTS vw_severity_classification AS
WITH base AS (
    SELECT
        m.patient_id,
        m.admission_id,
        m.admit_date,
        m.discharge_date,
        m.admission_type,
        m.length_of_stay_days,
        m.age_at_admission,
        m.primary_icd_code,
        m.primary_diagnosis,
        m.total_procedures,
        m.total_treatment_cost,
        m.insurance_type,

        -- Classify diagnosis into clinical groups based on ICD code prefix
        CASE
            WHEN m.primary_icd_code LIKE 'I%'   THEN 'Cardiovascular'
            WHEN m.primary_icd_code LIKE 'J%'   THEN 'Respiratory'
            WHEN m.primary_icd_code LIKE 'K%'   THEN 'Digestive'
            WHEN m.primary_icd_code LIKE 'N%'   THEN 'Genitourinary'
            WHEN m.primary_icd_code LIKE 'E%'   THEN 'Endocrine/Metabolic'
            WHEN m.primary_icd_code LIKE 'S%'
              OR m.primary_icd_code LIKE 'T%'   THEN 'Injury/Trauma'
            WHEN m.primary_icd_code LIKE 'C%'   THEN 'Neoplasm'
            ELSE 'Other'
        END AS diagnosis_group,

        -- Score components for severity calculation
        CASE
            WHEN m.primary_icd_code LIKE 'I%'
              OR m.primary_icd_code LIKE 'J%'
              OR m.primary_icd_code LIKE 'C%'   THEN 3
            WHEN m.primary_icd_code LIKE 'S%'
              OR m.primary_icd_code LIKE 'T%'
              OR m.primary_icd_code LIKE 'N%'   THEN 2
            ELSE 1
        END AS diagnosis_severity_score,

        CASE
            WHEN m.length_of_stay_days >= 14     THEN 3
            WHEN m.length_of_stay_days >= 7      THEN 2
            WHEN m.length_of_stay_days >= 3      THEN 1
            ELSE 0
        END AS los_severity_score,

        CASE
            WHEN m.admission_type = 'Emergency'  THEN 2
            WHEN m.admission_type = 'Urgent'     THEN 1
            ELSE 0
        END AS admission_type_score,

        CASE
            WHEN COALESCE(m.total_procedures, 0) >= 5 THEN 2
            WHEN COALESCE(m.total_procedures, 0) >= 2 THEN 1
            ELSE 0
        END AS procedure_severity_score

    FROM vw_master_patient_journey m
)

SELECT
    *,
    (diagnosis_severity_score + los_severity_score +
     admission_type_score + procedure_severity_score) AS composite_severity_score,

    CASE
        WHEN (diagnosis_severity_score + los_severity_score +
              admission_type_score + procedure_severity_score) >= 8
        THEN 'Critical'

        WHEN (diagnosis_severity_score + los_severity_score +
              admission_type_score + procedure_severity_score) >= 5
        THEN 'Severe'

        WHEN (diagnosis_severity_score + los_severity_score +
              admission_type_score + procedure_severity_score) >= 3
        THEN 'Moderate'

        ELSE 'Mild'
    END AS severity_level

FROM base
ORDER BY composite_severity_score DESC;
