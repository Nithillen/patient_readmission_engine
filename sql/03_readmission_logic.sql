/*
================================================================================
  30-DAY READMISSION IDENTIFICATION
  03_readmission_logic.sql
================================================================================
  Uses CTEs (Common Table Expressions) and window functions to calculate the
  exact number of days between a patient's discharge and their next admission.

  A readmission is defined as a subsequent admission within 30 days of discharge
  from the prior visit. This is the industry-standard CMS definition.

  Key techniques:
    - LEAD() window function to peek at the next admission per patient
    - CTE for clean, readable stepwise logic
    - Date arithmetic for precise day-gap calculation
================================================================================
*/

CREATE VIEW IF NOT EXISTS vw_readmission_flags AS
WITH ordered_admissions AS (
    /*
     * Step 1: Order each patient's admissions chronologically
     *         and use LEAD() to identify the next admission date.
     */
    SELECT
        patient_id,
        admission_id,
        admit_date,
        discharge_date,
        admission_type,
        discharge_location,
        hospital_expire_flag,
        CAST(
            (JULIANDAY(discharge_date) - JULIANDAY(admit_date)) AS INTEGER
        ) AS length_of_stay_days,

        -- Peek at the next admission date for this patient
        LEAD(admit_date) OVER (
            PARTITION BY patient_id
            ORDER BY admit_date
        ) AS next_admit_date,

        -- Peek at the next admission ID for traceability
        LEAD(admission_id) OVER (
            PARTITION BY patient_id
            ORDER BY admit_date
        ) AS next_admission_id

    FROM admissions
    WHERE
        discharge_date IS NOT NULL
        AND hospital_expire_flag = 0
),

readmission_calc AS (
    /*
     * Step 2: Calculate the gap in days between discharge and next admission.
     */
    SELECT
        *,
        CASE
            WHEN next_admit_date IS NOT NULL
            THEN CAST(
                (JULIANDAY(next_admit_date) - JULIANDAY(discharge_date)) AS INTEGER
            )
            ELSE NULL
        END AS days_to_readmission
    FROM ordered_admissions
)

/*
 * Step 3: Flag readmissions using the 30-day threshold.
 */
SELECT
    patient_id,
    admission_id,
    admit_date,
    discharge_date,
    admission_type,
    discharge_location,
    length_of_stay_days,
    next_admit_date,
    next_admission_id,
    days_to_readmission,

    CASE
        WHEN days_to_readmission IS NOT NULL AND days_to_readmission <= 30
        THEN 1
        ELSE 0
    END AS is_30_day_readmission,

    CASE
        WHEN days_to_readmission IS NULL               THEN 'No Subsequent Admission'
        WHEN days_to_readmission <= 7                   THEN 'Critical (0-7 days)'
        WHEN days_to_readmission <= 30                  THEN 'High Risk (8-30 days)'
        WHEN days_to_readmission <= 90                  THEN 'Moderate (31-90 days)'
        ELSE 'Low Risk (90+ days)'
    END AS readmission_risk_category

FROM readmission_calc
ORDER BY patient_id, admit_date;
