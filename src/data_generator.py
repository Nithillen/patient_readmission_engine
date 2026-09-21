"""
Synthetic Data Generator
========================
Generates a realistic synthetic healthcare dataset that mirrors the structure
of clinical databases like MIMIC-III. This avoids the need for credentialed
access to protected health information (PHI) while preserving the statistical
properties necessary for model development.

All data is entirely synthetic. No real patient data is used.
"""

import random
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

# ICD-10 code samples grouped by clinical category
ICD_CODES = {
    "Cardiovascular": [
        ("I21.0", "Acute ST elevation myocardial infarction of anterior wall"),
        ("I50.9", "Heart failure, unspecified"),
        ("I48.0", "Paroxysmal atrial fibrillation"),
        ("I25.10", "Atherosclerotic heart disease of native coronary artery"),
        ("I63.9", "Cerebral infarction, unspecified"),
    ],
    "Respiratory": [
        ("J18.9", "Pneumonia, unspecified organism"),
        ("J44.1", "Chronic obstructive pulmonary disease with acute exacerbation"),
        ("J96.01", "Acute respiratory failure with hypoxia"),
        ("J45.41", "Moderate persistent asthma with acute exacerbation"),
    ],
    "Digestive": [
        ("K92.0", "Hematemesis"),
        ("K80.10", "Calculus of gallbladder with chronic cholecystitis"),
        ("K35.80", "Unspecified acute appendicitis"),
    ],
    "Genitourinary": [
        ("N17.9", "Acute kidney failure, unspecified"),
        ("N39.0", "Urinary tract infection, site not specified"),
    ],
    "Endocrine": [
        ("E11.65", "Type 2 diabetes mellitus with hyperglycemia"),
        ("E87.1", "Hypo-osmolality and hyponatremia"),
    ],
    "Injury": [
        ("S72.001A", "Fracture of unspecified part of neck of right femur"),
        ("S06.0X0A", "Concussion without loss of consciousness"),
        ("T81.4XXA", "Infection following a procedure"),
    ],
    "Neoplasm": [
        ("C34.90", "Malignant neoplasm of unspecified part of bronchus or lung"),
        ("C18.9", "Malignant neoplasm of colon, unspecified"),
    ],
}

PROCEDURES = [
    ("99213", "Office/outpatient visit, established patient", 150.0),
    ("36415", "Venipuncture", 25.0),
    ("71046", "Chest X-ray, 2 views", 200.0),
    ("93000", "Electrocardiogram, routine", 125.0),
    ("43239", "Upper GI endoscopy with biopsy", 2500.0),
    ("27447", "Total knee replacement", 35000.0),
    ("33533", "Coronary artery bypass graft", 75000.0),
    ("47562", "Laparoscopic cholecystectomy", 12000.0),
    ("99223", "Initial hospital care, high complexity", 450.0),
    ("99232", "Subsequent hospital care, moderate complexity", 200.0),
    ("94640", "Nebulizer treatment", 80.0),
    ("90837", "Psychotherapy, 60 minutes", 250.0),
]

ETHNICITIES = [
    "White", "Black/African American", "Hispanic/Latino",
    "Asian", "Other/Unknown",
]

DISCHARGE_LOCATIONS = [
    "Home", "Home Health Care", "Skilled Nursing Facility",
    "Rehab", "Long Term Care", "Against Medical Advice",
]


def generate_dataset(db_path: str, n_patients: int = 2000, seed: int = 42) -> str:
    """
    Generates a full synthetic healthcare dataset and writes it to a SQLite database.

    Args:
        db_path: Path to the SQLite database file.
        n_patients: Number of unique patients to generate.
        seed: Random seed for reproducibility.

    Returns:
        The database path.
    """
    random.seed(seed)
    logger.info(f"Generating synthetic dataset with {n_patients} patients...")

    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Execute schema creation
    schema_path = Path(__file__).parent.parent / "sql" / "01_create_schema.sql"
    with open(schema_path, "r") as f:
        cursor.executescript(f.read())

    admission_id_counter = 1

    for patient_id in range(1, n_patients + 1):
        # Generate patient demographics
        gender = random.choice(["M", "F"])
        birth_year = random.randint(1940, 2000)
        dob = datetime(birth_year, random.randint(1, 12), random.randint(1, 28))
        ethnicity = random.choice(ETHNICITIES)
        insurance = random.choice(["Medicare", "Medicaid", "Private", "Self-Pay", "Government"])
        marital = random.choice(["Single", "Married", "Divorced", "Widowed"])

        cursor.execute(
            "INSERT INTO patients VALUES (?, ?, ?, ?, ?, ?)",
            (patient_id, gender, dob.strftime("%Y-%m-%d"), ethnicity, insurance, marital),
        )

        # Generate 1 to 5 admissions per patient
        n_admissions = random.choices([1, 2, 3, 4, 5], weights=[40, 30, 15, 10, 5])[0]
        last_discharge = datetime(2019, 1, 1) + timedelta(days=random.randint(0, 365))

        for _ in range(n_admissions):
            # Gap between admissions (some will be readmissions within 30 days)
            gap_days = random.choices(
                [random.randint(1, 15), random.randint(16, 30), random.randint(31, 365)],
                weights=[20, 15, 65],
            )[0]
            admit_date = last_discharge + timedelta(days=gap_days)

            # Ensure admission is before the data cutoff
            if admit_date > datetime(2023, 12, 31):
                break

            admission_type = random.choices(
                ["Emergency", "Elective", "Urgent", "Newborn"],
                weights=[40, 35, 20, 5],
            )[0]

            los = random.choices(
                [random.randint(1, 3), random.randint(4, 7), random.randint(8, 21), random.randint(22, 45)],
                weights=[35, 35, 20, 10],
            )[0]
            discharge_date = admit_date + timedelta(days=los)

            # Small chance of in-hospital mortality
            expire_flag = 1 if random.random() < 0.03 else 0
            discharge_loc = random.choice(DISCHARGE_LOCATIONS) if expire_flag == 0 else None

            # Select a diagnosis category (higher acuity more likely for emergency)
            if admission_type == "Emergency":
                diag_category = random.choices(
                    list(ICD_CODES.keys()),
                    weights=[30, 25, 10, 10, 10, 10, 5],
                )[0]
            else:
                diag_category = random.choice(list(ICD_CODES.keys()))

            primary_diag = random.choice(ICD_CODES[diag_category])

            cursor.execute(
                "INSERT INTO admissions VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    admission_id_counter,
                    patient_id,
                    admit_date.strftime("%Y-%m-%d %H:%M:%S"),
                    discharge_date.strftime("%Y-%m-%d %H:%M:%S"),
                    admission_type,
                    discharge_loc,
                    primary_diag[1],
                    expire_flag,
                ),
            )

            # Insert primary diagnosis
            cursor.execute(
                "INSERT INTO diagnoses (admission_id, icd_code, icd_description, diagnosis_priority) VALUES (?, ?, ?, ?)",
                (admission_id_counter, primary_diag[0], primary_diag[1], 1),
            )

            # Possibly add secondary diagnoses
            n_secondary = random.randint(0, 3)
            for priority in range(2, 2 + n_secondary):
                sec_category = random.choice(list(ICD_CODES.keys()))
                sec_diag = random.choice(ICD_CODES[sec_category])
                cursor.execute(
                    "INSERT INTO diagnoses (admission_id, icd_code, icd_description, diagnosis_priority) VALUES (?, ?, ?, ?)",
                    (admission_id_counter, sec_diag[0], sec_diag[1], priority),
                )

            # Insert treatments
            n_procedures = random.choices([1, 2, 3, 4, 5, 6], weights=[20, 30, 25, 15, 7, 3])[0]
            selected_procedures = random.sample(PROCEDURES, min(n_procedures, len(PROCEDURES)))
            for proc in selected_procedures:
                proc_date = admit_date + timedelta(days=random.randint(0, los))
                cost_jitter = proc[2] * random.uniform(0.8, 1.3)
                cursor.execute(
                    "INSERT INTO treatments (admission_id, procedure_code, procedure_description, treatment_date, cost_estimate) VALUES (?, ?, ?, ?, ?)",
                    (admission_id_counter, proc[0], proc[1], proc_date.strftime("%Y-%m-%d %H:%M:%S"), round(cost_jitter, 2)),
                )

            admission_id_counter += 1
            last_discharge = discharge_date

    conn.commit()

    # Report counts
    cursor.execute("SELECT COUNT(*) FROM patients")
    n_p = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM admissions")
    n_a = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM diagnoses")
    n_d = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM treatments")
    n_t = cursor.fetchone()[0]

    logger.info(f"Dataset generated: {n_p} patients, {n_a} admissions, {n_d} diagnoses, {n_t} treatments")
    conn.close()
    return str(db_path)
