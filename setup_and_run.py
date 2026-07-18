"""
HI 671 Query 2 Assignment - Mac-compatible runner using DuckDB
Author: Rutvij Reddy Vakati
Date: March 2026
"""

import duckdb
import pandas as pd
import random
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

con = duckdb.connect(':memory:')

random.seed(42)

# ============================================================
# CREATE SYNTHETIC DATA
# ============================================================

# --- ICD9 codes for realistic data ---
icd9_codes = [
    ('250.00', 'DIABETES MELLITUS WITHOUT MENTION OF COMPLICATION, TYPE II OR UNSPECIFIED TYPE, NOT STATED AS UNCONTROLLED'),
    ('250.01', 'DIABETES MELLITUS WITHOUT MENTION OF COMPLICATION, TYPE I [JUVENILE TYPE], NOT STATED AS UNCONTROLLED'),
    ('250.10', 'DIABETES WITH KETOACIDOSIS, TYPE II OR UNSPECIFIED TYPE, NOT STATED AS UNCONTROLLED'),
    ('250.20', 'DIABETES WITH HYPEROSMOLARITY, TYPE II OR UNSPECIFIED TYPE, NOT STATED AS UNCONTROLLED'),
    ('250.40', 'DIABETES WITH RENAL MANIFESTATIONS, TYPE II OR UNSPECIFIED TYPE, NOT STATED AS UNCONTROLLED'),
    ('250.50', 'DIABETES WITH OPHTHALMIC MANIFESTATIONS, TYPE II OR UNSPECIFIED TYPE, NOT STATED AS UNCONTROLLED'),
    ('250.60', 'DIABETES WITH NEUROLOGICAL MANIFESTATIONS, TYPE II OR UNSPECIFIED TYPE, NOT STATED AS UNCONTROLLED'),
    ('272.0',  'PURE HYPERCHOLESTEROLEMIA'),
    ('272.1',  'PURE HYPERGLYCERIDEMIA'),
    ('272.2',  'MIXED HYPERLIPIDEMIA'),
    ('272.4',  'OTHER AND UNSPECIFIED HYPERLIPIDEMIA'),
    ('401.0',  'MALIGNANT ESSENTIAL HYPERTENSION'),
    ('401.1',  'BENIGN ESSENTIAL HYPERTENSION'),
    ('401.9',  'UNSPECIFIED ESSENTIAL HYPERTENSION'),
    ('410.00', 'ACUTE MYOCARDIAL INFARCTION OF ANTEROLATERAL WALL, EPISODE OF CARE UNSPECIFIED'),
    ('410.10', 'ACUTE MYOCARDIAL INFARCTION OF OTHER ANTERIOR WALL, EPISODE UNSPECIFIED'),
    ('428.0',  'CONGESTIVE HEART FAILURE, UNSPECIFIED'),
    ('496',    'CHRONIC AIRWAY OBSTRUCTION, NOT ELSEWHERE CLASSIFIED'),
    ('530.81', 'ESOPHAGEAL REFLUX'),
    ('585.3',  'CHRONIC KIDNEY DISEASE, STAGE III (MODERATE)'),
    ('585.4',  'CHRONIC KIDNEY DISEASE, STAGE IV (SEVERE)'),
    ('715.09', 'OSTEOARTHROSIS, GENERALIZED, INVOLVING MULTIPLE SITES'),
    ('724.2',  'LUMBAGO'),
    ('733.00', 'OSTEOPOROSIS, UNSPECIFIED'),
    ('780.60', 'FEVER, UNSPECIFIED'),
    ('786.50', 'CHEST PAIN, UNSPECIFIED'),
    ('787.01', 'NAUSEA WITH VOMITING'),
    ('V58.61', 'LONG-TERM (CURRENT) USE OF ANTICOAGULANTS'),
    ('V72.31', 'ROUTINE GYNECOLOGICAL EXAMINATION'),
    ('E11.9',  'TYPE 2 DIABETES MELLITUS WITHOUT COMPLICATIONS'),
]

icd9_dict = dict(icd9_codes)

# --- CCS (Clinical Classification Software) mappings ---
ccs_data = [
    ('250.00', 49, 'DIABETES MELLITUS WITHOUT COMPLICATION'),
    ('250.01', 49, 'DIABETES MELLITUS WITHOUT COMPLICATION'),
    ('250.10', 50, 'DIABETES MELLITUS WITH KETOACIDOSIS'),
    ('250.20', 50, 'DIABETES MELLITUS WITH HYPEROSMOLARITY'),
    ('250.40', 51, 'DIABETES MELLITUS WITH RENAL MANIFESTATIONS'),
    ('250.50', 51, 'DIABETES MELLITUS WITH OPHTHALMIC MANIFESTATIONS'),
    ('250.60', 52, 'DIABETES MELLITUS WITH NEUROLOGICAL MANIFESTATIONS'),
    ('272.0',  53, 'DISORDERS OF LIPID METABOLISM'),
    ('272.1',  53, 'DISORDERS OF LIPID METABOLISM'),
    ('272.2',  53, 'DISORDERS OF LIPID METABOLISM'),
    ('272.4',  53, 'DISORDERS OF LIPID METABOLISM'),
    ('401.0',  98, 'ESSENTIAL HYPERTENSION'),
    ('401.1',  98, 'ESSENTIAL HYPERTENSION'),
    ('401.9',  98, 'ESSENTIAL HYPERTENSION'),
    ('410.00', 100, 'ACUTE MYOCARDIAL INFARCTION'),
    ('410.10', 100, 'ACUTE MYOCARDIAL INFARCTION'),
    ('428.0',  108, 'CONGESTIVE HEART FAILURE; NONHYPERTENSIVE'),
    ('496',    127, 'CHRONIC OBSTRUCTIVE PULMONARY DISEASE AND BRONCHIECTASIS'),
    ('530.81', 138, 'ESOPHAGEAL DISORDERS'),
    ('585.3',  158, 'CHRONIC KIDNEY DISEASE'),
    ('585.4',  158, 'CHRONIC KIDNEY DISEASE'),
    ('715.09', 203, 'OSTEOARTHRITIS'),
    ('724.2',  205, 'SPONDYLOSIS; INTERVERTEBRAL DISC DISORDERS; OTHER BACK PROBLEMS'),
    ('733.00', 212, 'PATHOLOGICAL FRACTURE'),
    ('780.60', 259, 'RESIDUAL CODES; UNCLASSIFIED'),
    ('786.50', 102, 'NONSPECIFIC CHEST PAIN'),
    ('787.01', 141, 'OTHER DISORDERS OF STOMACH AND DUODENUM'),
    ('V58.61', 260, 'MEDICAL EXAMINATION/EVALUATION'),
    ('V72.31', 256, 'MEDICAL EXAMINATION/EVALUATION'),
    ('E11.9',  49,  'DIABETES MELLITUS WITHOUT COMPLICATION'),
]

# --- Patient IDs (200 patients) ---
n_patients = 200
ptids = [f'PT{str(i).zfill(5)}' for i in range(1, n_patients + 1)]
genders = ['M', 'F']
gender_list = [random.choice(genders) for _ in ptids]

# --- Build ptid table ---
ptid_rows = []
for i, (pt, gen) in enumerate(zip(ptids, gender_list)):
    dob = datetime(1940, 1, 1) + timedelta(days=random.randint(0, 365*60))
    ptid_rows.append({'ptid': pt, 'gender': gen, 'dob': dob.strftime('%Y-%m-%d')})

ptid_df = pd.DataFrame(ptid_rows)

# --- Build claims table ---
# Make ~35% of patients diabetic, more prevalent in men
claims_rows = []
claim_id = 1
base_date = datetime(2018, 1, 1)

for pt, gen in zip(ptids, gender_list):
    # Number of claims per patient
    n_claims = random.randint(1, 8)

    # Diabetic probability: 40% male, 30% female
    is_diabetic = random.random() < (0.40 if gen == 'M' else 0.30)

    for _ in range(n_claims):
        claim_date = base_date + timedelta(days=random.randint(0, 365*5))

        if is_diabetic and random.random() < 0.6:
            # Assign a diabetes-related code
            icd = random.choice(['250.00','250.01','250.10','250.40','250.50','250.60'])
        else:
            # Assign a non-diabetes code
            non_dm = [c for c in icd9_dict if not c.startswith('250')]
            icd = random.choice(non_dm)

        cost = round(random.uniform(50, 15000), 2)
        # Add some negative/very low costs to test exclusion
        if random.random() < 0.05:
            cost = round(random.uniform(-500, 1.9), 2)

        claims_rows.append({
            'claim_id': claim_id,
            'ptid': pt,
            'icd9': icd,
            'cost': cost,
            'date': claim_date.strftime('%Y-%m-%d')
        })
        claim_id += 1

claims_df = pd.DataFrame(claims_rows)

# --- Build icd description table ---
icd_rows = [{'icd9': code, 'DESCRIPTION': desc} for code, desc in icd9_codes]
icd_df = pd.DataFrame(icd_rows)

# --- Build clean table (from Query 1 - prior assignment) ---
clean_rows = []
for i in range(1, 301):
    icd = random.choice([c[0] for c in icd9_codes])
    has_hyperlipidemia = icd in ('272.2', '272.4')
    clean_rows.append({
        'id': i,
        'icd9': icd,
        'AgeAtDx': random.randint(35, 85),
        'AgeAtDeath': random.choice([None, random.randint(50, 95)]),
        'AgeAtFirstDM': random.choice([None, random.randint(30, 80)])
    })
clean_df = pd.DataFrame(clean_rows)

# --- Build CCS table ---
ccs_df = pd.DataFrame(ccs_data, columns=['ICD9_Code', 'CCS_Category', 'CCS_Description'])

# --- Build RevisedICD9 table with 7 intentional errors ---
# Same ICD code, different descriptions
revised_icd9_base = [
    ('202',  'OTHER MALIGNANT NEOPLASM OF LYMPHOID AND HISTIOCYTIC TISSUE'),
    ('202',  'SEPTICEMIC PLAGUE'),                                                          # ERROR 1
    ('578',  'GASTROINTESTINAL HEMORRHAGE'),
    ('578',  'OTHER SPECIFIED VIRAL EXANTHEMATA'),                                          # ERROR 2
    ('780',  'GENERAL SYMPTOMS'),
    ('780',  'MOLLUSCUM CONTAGIOSUM'),                                                      # ERROR 3
    ('7051', 'PRICKLY HEAT'),
    ('7051', 'ACUTE OR UNSPECIFIED HEPATITIS C WITHOUT HEPATIC COMA'),                     # ERROR 4
    ('7810', 'ABNORMAL INVOLUNTARY MOVEMENTS'),
    ('7810', 'VIRAL WARTS, UNSPECIFIED'),                                                   # ERROR 5
    ('7819', 'OTHER SYMPTOMS INVOLVING NERVOUS AND MUSCULOSKELETAL SYSTEMS'),
    ('7819', 'OTHER SPECIFIED VIRAL WARTS'),                                                # ERROR 6
    ('7999', 'OTHER UNKNOWN AND UNSPECIFIED CAUSE OF MORBIDITY AND MORTALITY'),
    ('7999', 'UNSPECIFIED VIRAL INFECTION'),                                                # ERROR 7
    # Correct entries (unique descriptions)
    ('001',  'CHOLERA DUE TO VIBRIO CHOLERAE'),
    ('002',  'TYPHOID FEVER'),
    ('003',  'OTHER SALMONELLA INFECTIONS'),
    ('008',  'INTESTINAL INFECTIONS DUE TO OTHER ORGANISMS'),
    ('010',  'PRIMARY TUBERCULOUS INFECTION'),
    ('011',  'PULMONARY TUBERCULOSIS'),
    ('034',  'STREPTOCOCCAL SORE THROAT AND SCARLET FEVER'),
    ('041',  'BACTERIAL INFECTION IN CONDITIONS CLASSIFIED ELSEWHERE'),
    ('042',  'HUMAN IMMUNODEFICIENCY VIRUS [HIV] DISEASE'),
    ('053',  'HERPES ZOSTER'),
    ('110',  'DERMATOPHYTOSIS'),
    ('112',  'CANDIDIASIS'),
    ('140',  'MALIGNANT NEOPLASM OF LIP'),
    ('151',  'MALIGNANT NEOPLASM OF STOMACH'),
    ('162',  'MALIGNANT NEOPLASM OF TRACHEA, BRONCHUS, AND LUNG'),
    ('174',  'MALIGNANT NEOPLASM OF FEMALE BREAST'),
    ('185',  'MALIGNANT NEOPLASM OF PROSTATE'),
    ('250',  'DIABETES MELLITUS'),
    ('272',  'DISORDERS OF LIPID METABOLISM'),
    ('401',  'ESSENTIAL HYPERTENSION'),
    ('410',  'ACUTE MYOCARDIAL INFARCTION'),
    ('428',  'HEART FAILURE'),
    ('490',  'BRONCHITIS, NOT SPECIFIED AS ACUTE OR CHRONIC'),
    ('496',  'CHRONIC AIRWAY OBSTRUCTION, NOT ELSEWHERE CLASSIFIED'),
    ('530',  'DISEASES OF ESOPHAGUS'),
    ('585',  'CHRONIC KIDNEY DISEASE (CKD)'),
    ('715',  'OSTEOARTHROSIS AND ALLIED DISORDERS'),
    ('724',  'OTHER AND UNSPECIFIED DISORDERS OF BACK'),
    ('733',  'OTHER DISORDERS OF BONE AND CARTILAGE'),
    ('780',  'GENERAL SYMPTOMS'),   # duplicate of correct one - ok
    ('786',  'SYMPTOMS INVOLVING RESPIRATORY SYSTEM AND OTHER CHEST SYMPTOMS'),
    ('787',  'SYMPTOMS INVOLVING DIGESTIVE SYSTEM'),
]

revised_icd9_df = pd.DataFrame(revised_icd9_base, columns=['ICD', 'ICD_Desc'])
# Drop duplicate rows (keep unique ICD/ICD_Desc combos)
revised_icd9_df = revised_icd9_df.drop_duplicates()

# ============================================================
# LOAD TABLES INTO DUCKDB
# ============================================================

con.execute("CREATE TABLE ptid AS SELECT * FROM ptid_df")
con.execute("CREATE TABLE claims AS SELECT * FROM claims_df")
con.execute("CREATE TABLE icd AS SELECT * FROM icd_df")
con.execute("CREATE TABLE clean AS SELECT * FROM clean_df")
con.execute("CREATE TABLE CCS AS SELECT * FROM ccs_df")
con.execute("CREATE TABLE RevisedICD9 AS SELECT * FROM revised_icd9_df")

print("=" * 70)
print("HI 671 QUERY 2 ASSIGNMENT - RESULTS")
print("Author: Rutvij Reddy Vakati | March 2026")
print("=" * 70)

# ============================================================
# PART 1
# ============================================================

print("\n" + "=" * 70)
print("PART 1: CCS Table and Hyperlipidemia Exclusion")
print("=" * 70)

print("\n--- Part 1, Step 1: CCS Table (Top 10 rows) ---")
result = con.execute("SELECT * FROM CCS LIMIT 10").fetchdf()
print(result.to_string(index=False))

print("\n--- Part 1, Step 2: clean table joined with CCS (Top 10 rows) ---")
result = con.execute("""
SELECT
    c.id,
    c.icd9,
    c.AgeAtDx,
    c.AgeAtDeath,
    c.AgeAtFirstDM,
    ccs.CCS_Category,
    ccs.CCS_Description
FROM clean c
LEFT JOIN CCS ccs
    ON c.icd9 = ccs.ICD9_Code
LIMIT 10
""").fetchdf()
print(result.to_string(index=False))

# Create clean_with_CCS
con.execute("""
CREATE TABLE clean_with_CCS AS
SELECT
    c.id,
    c.icd9,
    c.AgeAtDx,
    c.AgeAtDeath,
    c.AgeAtFirstDM,
    ccs.CCS_Category,
    ccs.CCS_Description
FROM clean c
LEFT JOIN CCS ccs
    ON c.icd9 = ccs.ICD9_Code
""")

print("\n--- Part 1, Step 3: Patients with Hyperlipidemia (to be excluded) ---")
result = con.execute("""
SELECT COUNT(DISTINCT id) AS Patients_With_Hyperlipidemia
FROM clean_with_CCS
WHERE icd9 IN ('272.2', '272.4')
""").fetchdf()
print(result.to_string(index=False))

# Create clean_no_hyperlipidemia
con.execute("""
CREATE TABLE clean_no_hyperlipidemia AS
SELECT cw.*
FROM clean_with_CCS cw
LEFT JOIN (
    SELECT DISTINCT id
    FROM clean_with_CCS
    WHERE icd9 IN ('272.2', '272.4')
) hyper ON cw.id = hyper.id
WHERE hyper.id IS NULL
""")

print("\n--- Part 1, Step 3: Remaining patients after excluding hyperlipidemia ---")
result = con.execute("SELECT COUNT(DISTINCT id) AS Remaining_Patients FROM clean_no_hyperlipidemia").fetchdf()
print(result.to_string(index=False))

print("\n--- Part 1, Step 3: Confirm no hyperlipidemia remains (should be 0) ---")
result = con.execute("""
SELECT COUNT(DISTINCT id) AS Should_Be_Zero
FROM clean_no_hyperlipidemia
WHERE icd9 IN ('272.2', '272.4')
""").fetchdf()
print(result.to_string(index=False))

# ============================================================
# PART 2
# ============================================================

print("\n" + "=" * 70)
print("PART 2: ptid, claims, and icd Tables")
print("=" * 70)

print("\n--- Part 2, Step 1: Table previews ---")
print("\nptid table (TOP 5):")
result = con.execute("SELECT * FROM ptid LIMIT 5").fetchdf()
print(result.to_string(index=False))

print("\nclaims table (TOP 5):")
result = con.execute("SELECT * FROM claims LIMIT 5").fetchdf()
print(result.to_string(index=False))

print("\nicd table (TOP 5):")
result = con.execute("SELECT * FROM icd LIMIT 5").fetchdf()
print(result.to_string(index=False))

print("\n--- Part 2, Step 2: Patients with Diabetes (ICD9 codes starting with 250) ---")
result = con.execute("""
SELECT DISTINCT
    p.ptid,
    p.gender,
    p.dob,
    c.icd9,
    i.DESCRIPTION
FROM ptid p
INNER JOIN claims c ON p.ptid = c.ptid
INNER JOIN icd i ON c.icd9 = i.icd9
WHERE c.icd9 LIKE '250%'
ORDER BY p.ptid
""").fetchdf()
print(result.to_string(index=False))

print("\n--- Part 2, Step 2: Count of Diabetes Patients ---")
result = con.execute("""
SELECT COUNT(DISTINCT p.ptid) AS Total_Diabetes_Patients
FROM ptid p
INNER JOIN claims c ON p.ptid = c.ptid
WHERE c.icd9 LIKE '250%'
""").fetchdf()
print(result.to_string(index=False))

print("\n--- Part 2, Step 3: Average cost per diagnosis (cost >= 2.0), sorted most to least expensive ---")
result = con.execute("""
SELECT
    c.icd9,
    i.DESCRIPTION,
    ROUND(AVG(c.cost), 2) AS Average_Cost,
    COUNT(*) AS Number_of_Claims
FROM claims c
INNER JOIN icd i ON c.icd9 = i.icd9
WHERE c.cost >= 2.0
GROUP BY c.icd9, i.DESCRIPTION
ORDER BY Average_Cost DESC
""").fetchdf()
print(result.to_string(index=False))

print("\n--- Part 2, Step 4: Diabetes prevalence by gender ---")
result = con.execute("""
SELECT
    p.gender,
    COUNT(DISTINCT p.ptid) AS Total_Patients,
    COUNT(DISTINCT CASE
        WHEN c.icd9 LIKE '250%' THEN p.ptid
    END) AS Diabetes_Patients,
    ROUND(
        CAST(COUNT(DISTINCT CASE
            WHEN c.icd9 LIKE '250%' THEN p.ptid
        END) AS FLOAT) / COUNT(DISTINCT p.ptid) * 100, 2
    ) AS Diabetes_Percentage
FROM ptid p
LEFT JOIN claims c ON p.ptid = c.ptid
GROUP BY p.gender
ORDER BY Diabetes_Percentage DESC
""").fetchdf()
print(result.to_string(index=False))

print("\n--- Part 2, Step 5: Top 2 months with most diagnoses reported ---")
result = con.execute("""
SELECT
    EXTRACT(MONTH FROM CAST(date AS DATE)) AS Month_Number,
    strftime(CAST(date AS DATE), '%B') AS Month_Name,
    COUNT(*) AS Total_Diagnoses
FROM claims
GROUP BY EXTRACT(MONTH FROM CAST(date AS DATE)), strftime(CAST(date AS DATE), '%B')
ORDER BY Total_Diagnoses DESC
LIMIT 2
""").fetchdf()
print(result.to_string(index=False))

print("\n--- Part 2, Step 6: ICD codes with multiple descriptions (errors in RevisedICD9) ---")
result = con.execute("""
SELECT
    ICD,
    COUNT(DISTINCT ICD_Desc) AS Num_Different_Descriptions
FROM RevisedICD9
GROUP BY ICD
HAVING COUNT(DISTINCT ICD_Desc) > 1
ORDER BY ICD
""").fetchdf()
print(result.to_string(index=False))

print("\n--- Part 2, Step 6: Conflicting descriptions for each error ---")
result = con.execute("""
SELECT
    a.ICD,
    a.ICD_Desc AS Description_1,
    b.ICD_Desc AS Description_2
FROM RevisedICD9 a
INNER JOIN RevisedICD9 b
    ON a.ICD = b.ICD
    AND a.ICD_Desc < b.ICD_Desc
GROUP BY a.ICD, a.ICD_Desc, b.ICD_Desc
ORDER BY a.ICD
""").fetchdf()
print(result.to_string(index=False))

print("\n" + "=" * 70)
print("ALL QUERIES COMPLETED SUCCESSFULLY")
print("=" * 70)
