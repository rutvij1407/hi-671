**Healthcare Claims Analysis in SQL (HI 671)**

SQL analysis of patient, claims and diagnosis tables, written for a health informatics course at George Mason University.

**The problem**

Claims data records diagnoses as detailed ICD9 codes, which are hard to analyse directly. The assignment groups them into broader clinical categories and then answers questions about cost, patient mix and data quality.

**Approach**

1. Build a CCS table that maps ICD9 codes to HCUP Clinical Classifications Software categories, then exclude patients with hyperlipidemia.
2. Join the patient, claims and diagnosis tables to identify patients with diabetes.
3. Calculate the average cost of each diagnosis.
4. Test whether men are more likely than women to have a given diagnosis.
5. Find the top two months for a diagnosis.
6. Audit the ICD9 data and find seven planted errors.

**The data**

The real course data is not included. To make the project runnable by anyone, setup_and_run.py generates a seeded synthetic dataset with realistic ICD9 codes in DuckDB and runs the analysis on it. No real patient information is in this repository.

**Files**

* HI671_Query2.sql: the original SQL Server solution
* setup_and_run.py: a Mac friendly runner using DuckDB and synthetic data
* build_site.py: turns the output into a static report in the site folder

**Run it**

Run python3 setup_and_run.py to see the results, or python3 build_site.py to rebuild the HTML report.

**Tech stack**

SQL Server, DuckDB, Python, pandas.

Author: Rutvij Reddy Vakati, March 2026
