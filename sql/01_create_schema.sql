/*
================================================================================
  PATIENT READMISSION ENGINE - SCHEMA DEFINITION
  01_create_schema.sql
================================================================================
  Creates the relational schema for the healthcare dataset.
  Designed to mirror the structure of clinical databases like MIMIC-III.
  
  Tables:
    - patients        : Demographics and identifiers
    - admissions      : Hospital admission and discharge records
    - diagnoses       : ICD-coded diagnoses tied to admissions
    - treatments      : Procedures and interventions performed
================================================================================
*/

-- Drop tables if they exist (for idempotent re-runs)
DROP TABLE IF EXISTS treatments;
DROP TABLE IF EXISTS diagnoses;
DROP TABLE IF EXISTS admissions;
DROP TABLE IF EXISTS patients;


CREATE TABLE patients (
    patient_id          INTEGER PRIMARY KEY,
    gender              TEXT NOT NULL CHECK (gender IN ('M', 'F')),
    date_of_birth       DATE NOT NULL,
    ethnicity           TEXT,
    insurance_type      TEXT CHECK (insurance_type IN ('Medicare', 'Medicaid', 'Private', 'Self-Pay', 'Government')),
    marital_status      TEXT CHECK (marital_status IN ('Single', 'Married', 'Divorced', 'Widowed', NULL))
);


CREATE TABLE admissions (
    admission_id        INTEGER PRIMARY KEY,
    patient_id          INTEGER NOT NULL,
    admit_date          DATETIME NOT NULL,
    discharge_date      DATETIME,                   -- NULL if patient is still admitted
    admission_type      TEXT NOT NULL CHECK (admission_type IN ('Emergency', 'Elective', 'Urgent', 'Newborn')),
    discharge_location  TEXT,
    admit_diagnosis     TEXT,
    hospital_expire_flag INTEGER DEFAULT 0,          -- 1 if the patient died during this admission
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);


CREATE TABLE diagnoses (
    diagnosis_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    admission_id        INTEGER NOT NULL,
    icd_code            TEXT NOT NULL,               -- ICD-9 or ICD-10 code
    icd_description     TEXT,
    diagnosis_priority  INTEGER DEFAULT 1,           -- 1 = primary, 2+ = secondary
    FOREIGN KEY (admission_id) REFERENCES admissions(admission_id)
);


CREATE TABLE treatments (
    treatment_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    admission_id        INTEGER NOT NULL,
    procedure_code      TEXT NOT NULL,
    procedure_description TEXT,
    treatment_date      DATETIME,
    cost_estimate       REAL,                        -- Estimated cost in USD
    FOREIGN KEY (admission_id) REFERENCES admissions(admission_id)
);


-- Indexes for query performance
CREATE INDEX idx_admissions_patient ON admissions(patient_id);
CREATE INDEX idx_admissions_dates ON admissions(admit_date, discharge_date);
CREATE INDEX idx_diagnoses_admission ON diagnoses(admission_id);
CREATE INDEX idx_treatments_admission ON treatments(admission_id);
