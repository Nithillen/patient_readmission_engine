/*
================================================================================
  MASTER PATIENT VIEW
  02_master_patient_view.sql
================================================================================
  Creates a unified view of each patient's hospital journey by joining across
  the patients, admissions, diagnoses, and treatments tables.

  Data Quality Rules Applied:
    - Excludes admissions with NULL discharge dates (still admitted)
    - Excludes admissions where discharge occurred before admission (data error)
    - Gracefully handles missing dates with COALESCE defaults
    - Filters to only primary diagnoses (diagnosis_priority = 1)
================================================================================
*/

CREATE VIEW IF NOT EXISTS vw_master_patient_journey AS
SELECT
    p.patient_id,
    p.gender,
    p.date_of_birth,
    p.ethnicity,
    p.insurance_type,
    p.marital_status,

    -- Admission details
    a.admission_id,
    a.admit_date,
    a.discharge_date,
    a.admission_type,
    a.discharge_location,
    a.hospital_expire_flag,

    -- Calculated: Length of Stay (days)
    CAST(
        (JULIANDAY(a.discharge_date) - JULIANDAY(a.admit_date)) AS INTEGER
    ) AS length_of_stay_days,

    -- Calculated: Patient age at admission
    CAST(
        (JULIANDAY(a.admit_date) - JULIANDAY(p.date_of_birth)) / 365.25 AS INTEGER
    ) AS age_at_admission,

    -- Primary diagnosis
    d.icd_code              AS primary_icd_code,
    d.icd_description       AS primary_diagnosis,

    -- Treatment summary (aggregated per admission)
    t.total_procedures,
    COALESCE(t.total_treatment_cost, 0.0) AS total_treatment_cost

FROM patients p

INNER JOIN admissions a
    ON p.patient_id = a.patient_id

-- Join only the primary diagnosis for each admission
LEFT JOIN diagnoses d
    ON a.admission_id = d.admission_id
    AND d.diagnosis_priority = 1

-- Subquery: aggregate treatment data per admission to avoid row duplication
LEFT JOIN (
    SELECT
        admission_id,
        COUNT(*)            AS total_procedures,
        SUM(cost_estimate)  AS total_treatment_cost
    FROM treatments
    GROUP BY admission_id
) t ON a.admission_id = t.admission_id

WHERE
    -- Exclude patients still admitted (no discharge date)
    a.discharge_date IS NOT NULL

    -- Exclude data errors where discharge precedes admission
    AND JULIANDAY(a.discharge_date) >= JULIANDAY(a.admit_date)

    -- Exclude patients who expired during this admission
    AND a.hospital_expire_flag = 0

ORDER BY
    p.patient_id,
    a.admit_date;
