-- ============================================================
-- HI 671 Query 2 Assignment
-- Author: Rutvij Reddy Vakati
-- Date: March 2026
-- ============================================================

-- ************************************************************
-- PART 1: CCS Table and Hyperlipidemia Exclusion
-- ************************************************************

USE [HI-671];
GO

-- ============================================================
-- Part 1, Step 1: Create CCS Table
-- After downloading the CCS file from HCUP (Appendix A),
-- import it into SQL Server as dbo.CCS
-- ============================================================

-- Option A: If importing from CSV/flat file, create the table first
CREATE TABLE dbo.CCS (
    ICD9_Code       VARCHAR(10),
    CCS_Category    INT,
    CCS_Description VARCHAR(255)
);
GO

-- Import using BULK INSERT (adjust file path as needed)
-- BULK INSERT dbo.CCS
-- FROM 'C:\path\to\CCS_AppendixA.csv'
-- WITH (
--     FIRSTROW = 2,
--     FIELDTERMINATOR = ',',
--     ROWTERMINATOR = '\n',
--     TABLOCK
-- );
-- GO

-- Option B: If using the Import Wizard in SSMS:
-- 1. Right click on Database > Tasks > Import Data
-- 2. Select the downloaded CCS file
-- 3. Map columns: ICD9 Code, CCS Category, CCS Description
-- 4. Name the destination table dbo.CCS

-- Verify CCS table
SELECT TOP 10 * FROM dbo.CCS;
GO


-- ============================================================
-- Part 1, Step 2: Add CCS Category and Description to 
--                 dbo.clean using JOIN
-- ============================================================

-- Preview the JOIN result
SELECT 
    c.id,
    c.icd9,
    c.AgeAtDx,
    c.AgeAtDeath,
    c.AgeAtFirstDM,
    ccs.CCS_Category,
    ccs.CCS_Description
FROM dbo.clean c
LEFT JOIN dbo.CCS ccs
    ON c.icd9 = ccs.ICD9_Code;
GO

-- Create a new table with CCS data added
SELECT 
    c.id,
    c.icd9,
    c.AgeAtDx,
    c.AgeAtDeath,
    c.AgeAtFirstDM,
    ccs.CCS_Category,
    ccs.CCS_Description
INTO dbo.clean_with_CCS
FROM dbo.clean c
LEFT JOIN dbo.CCS ccs
    ON c.icd9 = ccs.ICD9_Code;
GO

-- Verify the new table
SELECT TOP 10 * FROM dbo.clean_with_CCS;
GO


-- ============================================================
-- Part 1, Step 3: Exclude patients with Hyperlipidemia
--                 (ICD9 codes 272.2 and 272.4)
-- Using JOIN to exclude all patients who had at least one
-- admission where diagnosis was hyperlipidemia
-- ============================================================

-- First, check how many patients have hyperlipidemia
SELECT COUNT(DISTINCT id) AS Patients_With_Hyperlipidemia
FROM dbo.clean_with_CCS
WHERE icd9 IN ('272.2', '272.4');
GO

-- Method: Use LEFT JOIN with NULL check to exclude patients
-- This removes ALL records for patients who had at least
-- one hyperlipidemia diagnosis (not just those specific rows)
SELECT cw.*
FROM dbo.clean_with_CCS cw
LEFT JOIN (
    SELECT DISTINCT id
    FROM dbo.clean_with_CCS
    WHERE icd9 IN ('272.2', '272.4')
) hyper ON cw.id = hyper.id
WHERE hyper.id IS NULL;
GO

-- Save as a new table for reference
SELECT cw.*
INTO dbo.clean_no_hyperlipidemia
FROM dbo.clean_with_CCS cw
LEFT JOIN (
    SELECT DISTINCT id
    FROM dbo.clean_with_CCS
    WHERE icd9 IN ('272.2', '272.4')
) hyper ON cw.id = hyper.id
WHERE hyper.id IS NULL;
GO

-- Verify exclusion
SELECT COUNT(DISTINCT id) AS Remaining_Patients
FROM dbo.clean_no_hyperlipidemia;
GO

-- Confirm no hyperlipidemia patients remain
SELECT COUNT(DISTINCT id) AS Should_Be_Zero
FROM dbo.clean_no_hyperlipidemia
WHERE icd9 IN ('272.2', '272.4');
GO


-- ************************************************************
-- PART 2: Working with ptid, claims, and icd tables
-- ************************************************************

-- ============================================================
-- Part 2, Step 1: Import data from Excel files into tables
-- Use SSMS Import Wizard for each file:
--   Right click Database > Tasks > Import Data
--   Source: Microsoft Excel
--   Select each .xls file and import
-- ============================================================

-- After importing, verify each table:
SELECT TOP 10 * FROM dbo.ptid;
GO

SELECT TOP 10 * FROM dbo.claims;
GO

SELECT TOP 10 * FROM dbo.icd;
GO

-- Check structure of each table
EXEC sp_columns 'ptid';
GO

EXEC sp_columns 'claims';
GO

EXEC sp_columns 'icd';
GO


-- ============================================================
-- Part 2, Step 2: Identify patients that have diabetes
-- ICD9 codes for Diabetes Mellitus start with 250
-- ============================================================

SELECT DISTINCT 
    p.*,
    c.icd9,
    i.DESCRIPTION
FROM dbo.ptid p
INNER JOIN dbo.claims c ON p.ptid = c.ptid
INNER JOIN dbo.icd i ON c.icd9 = i.icd9
WHERE c.icd9 LIKE '250%'
ORDER BY p.ptid;
GO

-- Count of diabetes patients
SELECT COUNT(DISTINCT p.ptid) AS Total_Diabetes_Patients
FROM dbo.ptid p
INNER JOIN dbo.claims c ON p.ptid = c.ptid
WHERE c.icd9 LIKE '250%';
GO


-- ============================================================
-- Part 2, Step 3: Average cost of each diagnosis
-- Sorted most expensive to least expensive
-- Exclude all bills with negative or less than 2.0 values
-- ============================================================

SELECT 
    c.icd9,
    i.DESCRIPTION,
    AVG(c.cost) AS Average_Cost,
    COUNT(*) AS Number_of_Claims
FROM dbo.claims c
INNER JOIN dbo.icd i ON c.icd9 = i.icd9
WHERE c.cost >= 2.0
GROUP BY c.icd9, i.DESCRIPTION
ORDER BY Average_Cost DESC;
GO


-- ============================================================
-- Part 2, Step 4: Show if men are more likely to have 
--                 diabetes than women
-- ============================================================

-- Count and percentage of diabetes by gender
SELECT 
    p.gender,
    COUNT(DISTINCT p.ptid) AS Total_Patients,
    COUNT(DISTINCT CASE 
        WHEN c.icd9 LIKE '250%' THEN p.ptid 
    END) AS Diabetes_Patients,
    CAST(COUNT(DISTINCT CASE 
        WHEN c.icd9 LIKE '250%' THEN p.ptid 
    END) AS FLOAT) / COUNT(DISTINCT p.ptid) * 100 
        AS Diabetes_Percentage
FROM dbo.ptid p
LEFT JOIN dbo.claims c ON p.ptid = c.ptid
GROUP BY p.gender
ORDER BY Diabetes_Percentage DESC;
GO


-- ============================================================
-- Part 2, Step 5: Top two months most likely to have a 
--                 diagnosis reported
-- ============================================================

SELECT TOP 2
    MONTH(c.date) AS Month_Number,
    DATENAME(MONTH, c.date) AS Month_Name,
    COUNT(*) AS Total_Diagnoses
FROM dbo.claims c
GROUP BY MONTH(c.date), DATENAME(MONTH, c.date)
ORDER BY Total_Diagnoses DESC;
GO


-- ============================================================
-- Part 2, Step 6: Find seven errors in ICD9 data
-- File: RevisedICD9.xls (columns: ICD, ICD_Desc)
-- Same ICD9 code assigned different descriptions
-- ============================================================

-- First, import RevisedICD9.xls using SSMS Import Wizard
-- Right click Database > Tasks > Import Data > Microsoft Excel
-- This creates dbo.RevisedICD9 (or rename as needed)

-- Find ICD codes with multiple different descriptions
SELECT 
    ICD,
    COUNT(DISTINCT ICD_Desc) AS Num_Different_Descriptions
FROM dbo.RevisedICD9
GROUP BY ICD
HAVING COUNT(DISTINCT ICD_Desc) > 1
ORDER BY ICD;
GO

-- Show the actual conflicting descriptions for each error
SELECT 
    a.ICD,
    a.ICD_Desc AS Description_1,
    b.ICD_Desc AS Description_2
FROM dbo.RevisedICD9 a
INNER JOIN dbo.RevisedICD9 b 
    ON a.ICD = b.ICD 
    AND a.ICD_Desc < b.ICD_Desc
GROUP BY a.ICD, a.ICD_Desc, b.ICD_Desc
ORDER BY a.ICD;
GO

-- The errors found are:
-- ICD 202:  SEPTICEMIC PLAGUE vs OTHER MALIGNANT NEOPLASM OF LYMPHOID...
-- ICD 578:  OTHER SPECIFIED VIRAL EXANTHEMATA vs GASTROINTESTINAL HEMORRHAGE
-- ICD 780:  MOLLUSCUM CONTAGIOSUM vs GENERAL SYMPTOMS
-- ICD 7051: ACUTE OR UNSPECIFIED HEPATITIS C... vs PRICKLY HEAT
-- ICD 7810: VIRAL WARTS, UNSPECIFIED vs ABNORMAL INVOLUNTARY MOVEMENTS
-- ICD 7819: OTHER SPECIFIED VIRAL WARTS vs OTHER SYMPTOMS INVOLVING NERVOUS...
-- ICD 7999: UNSPECIFIED VIRAL INFECTION vs OTHER UNKNOWN AND UNSPECIFIED...
-- ICD 9941: HLAMYDIA TRACHOMATIS vs DROWNING AND NONFATAL SUBMERSION
GO
