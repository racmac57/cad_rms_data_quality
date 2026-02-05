# Quality Report Files Reference

This document describes each file produced by the monthly validation scripts (`validate_cad.py` and `validate_rms.py`). Reports are written to `monthly_validation/reports/YYYY_MM_cad/` or `YYYY_MM_rms/` (prefix = month being reported on, e.g. January 2026 → `2026_01_cad`), or a custom path via `--output`.

---

## Field Names: CAD vs RMS

| Meaning | CAD export | RMS export |
|--------|------------|------------|
| Case number | **ReportNumberNew** | **Case Number** (mapped to CaseNumber in scripts) |
| Address | **FullAddress2** | **FullAddress** |
| Zone | **PDZone** | **Zone** |
| How reported | **HowReported** | Not in RMS raw data |

- **ReportNumberNew** is CAD; **Case Number** is RMS. Both are the case identifier (format YY-NNNNNN).
- **FullAddress2** is CAD; **FullAddress** is RMS. Both are the incident address field.
- **PDZone** is used in CAD; RMS uses the field **Zone**.
- **HowReported** is CAD only; it is not included in the raw RMS export.

---

## Score categories and what they mean

- **Required fields** – One or more required columns are missing or empty (e.g. Case Number, FullAddress, Zone for RMS; ReportNumberNew, FullAddress2, PDZone, HowReported for CAD). The report shows **only** the system you ran (CAD or RMS).
- **Valid formats** – Values that don’t match the expected pattern (e.g. case number YY-NNNNNN, date/time format). The report summarizes the actual issues found in this run (e.g. “Invalid case number format (4)”).
- **Address quality** – Address problems in this run: null/blank, missing street number or name, cross-street/intersection only, non-standard format, or failed standardization.
- **Domain compliance** – A value is outside the allowed list (e.g. HowReported, Disposition for CAD).
- **Consistency checks** – **What it means:** Two or more related fields don’t agree, or a date/time is impossible. **Examples:** Incident date is *after* the report date (can’t report before the incident); time is out of range (e.g. 25:00); date and time don’t match. The report lists the specific rules that failed in this run.

---

## Files in Each Report Folder

| File | Format | Purpose |
|------|--------|---------|
| **action_items.xlsx** | Excel | Detailed list of records that failed validation, by priority |
| **validation_summary.html** | HTML | Human-readable summary with quality score and metrics |
| **metrics.json** | JSON | Machine-readable metrics for trend analysis |
| **validation.log** | Text | Run log (timestamps, step messages, counts) |

---

## 1. action_items.xlsx

**What it shows:** Every record that failed at least one validation rule, with enough detail to find and fix the issue.

**Structure:**
- **Sheet: Critical Issues (P1)** – Priority 1 issues (e.g. null case number, invalid format, missing required fields). Fix these first.
- **Sheet: Warnings (P2)** – Priority 2 issues (e.g. invalid domain values, date/time anomalies).
- **Sheet: Info (P3)** – Priority 3 issues (e.g. call type format suggestions, offense code notes).
- **Sheet: All Issues** – All of the above in one list.

**Columns (CAD):**
- `row_number` – Excel row (header = 1, so first data row is 2).
- `ReportNumberNew` – Case number for the row.
- `TimeOfCall` – Call time (for context).
- `field` – Field that failed (e.g. ReportNumberNew, PDZone, HowReported).
- `current_value` – Value that failed (or NULL).
- `suggested_correction` – What to change (e.g. “Format should be YY-NNNNNN”).
- `rule_violated` – Short description of the rule (e.g. “Required field PDZone is null or empty”).
- `category` – Grouping (e.g. Data Quality, Missing Data, Domain Violation, Call Type Format).
- `priority` – 1 (Critical), 2 (Warning), or 3 (Info).

**Columns (RMS):** Same idea; key identifiers are `CaseNumber` and `IncidentDate` instead of `ReportNumberNew` and `TimeOfCall`. Categories can include Date Validation, Time Validation, Offense Code.

**Use:** Open in Excel; filter/sort by sheet, field, or category to work through corrections.

---

## 2. validation_summary.html

**What it shows:** A single-page summary you can open in a browser: overall quality, score breakdown, and issue counts.

**Sections:**
- **Header** – Input file name and validation timestamp.
- **Quality score (0–100)** – Large score with a label:
  - **Excellent** (≥95) – Green.
  - **Good** (≥80) – Blue.
  - **Needs Attention** (≥60) – Yellow.
  - **Critical** (&lt;60) – Red.
- **Summary metrics** – Total records; counts of Critical (P1), Warnings (P2), and Info (P3) issues.
- **Score breakdown table** – Points per category (e.g. Required Fields 30, Valid Formats 25, Address Quality 20, Domain Compliance 15, Consistency 10) and total.
- **Action items summary** – Table of issue counts by priority and category (e.g. P1 / Missing Data / 1694).
- **Footer** – Note to use `action_items.xlsx` for detail; script name and version.

**Use:** Quick check of quality level and where points were lost; share or print for status updates.

---

## 3. metrics.json

**What it shows:** Same run in structured form for scripts, dashboards, or trend analysis.

**Typical fields:**
- `validation_timestamp` – ISO datetime of the run.
- `input_file` – Name of the validated file (e.g. 2026_01_CAD.xlsx).
- `total_records` – Number of rows validated.
- `quality_score` – Overall score (0–100).
- `score_breakdown` – Points per category (e.g. required_fields, valid_formats, domain_compliance, consistency_checks, address_quality) and priority counts (priority_1_issues, priority_2_issues, priority_3_issues).
- `action_items_count` – Total number of issues (one row can have multiple).
- `issues_by_category` – Count per category (e.g. "Missing Data": 1694).
- `issues_by_priority` – Count per priority (priority_1, priority_2, priority_3).
- `pass_rate` – Percent of records with no issues (e.g. 83.77).

**RMS:** May also include `data_source`: `"rms"`.

**Use:** Automation, comparing runs over time, or feeding into other reporting tools.

---

## 4. validation.log

**What it shows:** Chronological log of the validation run: config load, steps, record counts, and any warnings/errors.

**Typical content:**
- Config and validation rules loaded.
- Output directory.
- Step messages (e.g. “Validating case numbers…”, “Found N case number issues”).
- Quality score and final summary (total records, score, action items count, processing time, report paths).

**Use:** Debugging failed runs or understanding what the script did step-by-step.

---

## 5. latest.json (in monthly_validation/reports/)

**What it shows:** Pointer to the most recent validation run so you don’t have to remember the folder name.

**Location:** `monthly_validation/reports/latest.json` (one file for the whole reports directory).

**Typical fields:**
- `latest_run` or `latest_rms_run` – Report folder name (e.g. 2026_02_02_jan_cad).
- `timestamp` / `rms_timestamp` – When the run completed.
- `path` / `rms_path` – Full path to the report folder.
- `record_count` / `rms_record_count` – Total records validated.
- `quality_score` / `rms_quality_score` – Overall score.
- `action_items_count` / `rms_action_items_count` – Total action items.

**Use:** Scripts or people can read this to find “the latest CAD (or RMS) report” without hard-coding a date.

---

## Quick Reference

| If you want to… | Use… |
|-----------------|------|
| Fix specific bad rows | **action_items.xlsx** (by priority sheet) |
| See overall quality at a glance | **validation_summary.html** |
| Automate or trend quality over time | **metrics.json** |
| See what the script did | **validation.log** |
| Find the latest report path | **latest.json** |
