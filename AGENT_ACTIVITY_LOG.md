# AGENT PIPELINE ACTIVITY LOG

**Processing Date:** 2026-02-04 06:40:07
**Duration:** 76.9 seconds

---

## AGENT SUMMARY

| Agent | Key Metric | Status |
|-------|------------|--------|
| Intake Agent | 5 files found | OK |
| Schema Agent | 5 files mapped | ISSUE |
| Standardizer Agent | 280,720 total records extracted | OK |
| Rate Card Agent | 228,894 with cost, 51,826 missing | ISSUE |
| Modality Agent | OPI:221,282 VRI:7,578 | OK |
| QA Agent | 131,589 duplicates, 532 outliers | ISSUE |
| Aggregator Agent | $2,219,389.98 total spend | OK |

---

## DETAILED ACTIVITY LOG


### Intake Agent

- **Started scanning**: directory: c:\Users\John\.gemini\antigravity\playground\multiagent-baseline-lt\data_files\Language Services
- **Files discovered**: count: 5
- **File found**: filename: Healthpoint - Propio Transaction Download.xlsx
- **File found**: filename: Nuvance - Cyracom Utilization.xlsx
- **File found**: filename: Peak Vista - AMN Download.xls
- **File found**: filename: VFC - Pacific Interpreters Invoice.xls
- **File found**: filename: Wellspace - LanguageLine Invoice.XLS

### Schema Agent

- **Processing file**: file: Healthpoint - Propio Transaction Download.xlsx, vendor: Healthpoint
- **Column mapping**: sheet: ag-grid, confidence: 100%, mapped_fields: ['date', 'language', 'minutes', 'charge', 'rate', 'modality']

### Standardizer Agent

- **Records extracted**: file: Healthpoint - Propio Transaction Download.xlsx, sheet: ag-grid, records: 227272

### Schema Agent

- **Column mapping**: sheet: Pivot, confidence: 75%, mapped_fields: ['language', 'minutes', 'charge', 'rate', 'modality']

### Standardizer Agent

- **Records extracted**: file: Healthpoint - Propio Transaction Download.xlsx, sheet: Pivot, records: 0

### Schema Agent

- **Column mapping**: sheet: Beyond a Year, confidence: 0%, mapped_fields: []
- **SKIPPED - Low confidence**: sheet: Beyond a Year
- **Processing file**: file: Nuvance - Cyracom Utilization.xlsx, vendor: Nuvance
- **Column mapping**: sheet: Raw Data OPI.VRI, confidence: 100%, mapped_fields: ['date', 'language', 'minutes', 'charge', 'rate', 'modality']

### Standardizer Agent

- **Records extracted**: file: Nuvance - Cyracom Utilization.xlsx, sheet: Raw Data OPI.VRI, records: 1588

### Schema Agent

- **Processing file**: file: Peak Vista - AMN Download.xls, vendor: Peak
- **Column mapping**: sheet: Sheet0, confidence: 75%, mapped_fields: ['date', 'language', 'minutes']

### Standardizer Agent

- **Records extracted**: file: Peak Vista - AMN Download.xls, sheet: Sheet0, records: 44877

### Schema Agent

- **Processing file**: file: VFC - Pacific Interpreters Invoice.xls, vendor: VFC
- **Column mapping**: sheet: Call Detail, confidence: 75%, mapped_fields: ['date', 'language', 'minutes']

### Standardizer Agent

- **Records extracted**: file: VFC - Pacific Interpreters Invoice.xls, sheet: Call Detail, records: 622

### Schema Agent

- **Column mapping**: sheet: Invoice, confidence: 50%, mapped_fields: ['date', 'charge']

### Standardizer Agent

- **Records extracted**: file: VFC - Pacific Interpreters Invoice.xls, sheet: Invoice, records: 0

### Schema Agent

- **Processing file**: file: Wellspace - LanguageLine Invoice.XLS, vendor: Wellspace
- **Column mapping**: sheet: Call Detail, confidence: 75%, mapped_fields: ['date', 'language', 'minutes']

### Standardizer Agent

- **Records extracted**: file: Wellspace - LanguageLine Invoice.XLS, sheet: Call Detail, records: 6327

### Schema Agent

- **Column mapping**: sheet: Call Detail Summary Report, confidence: 75%, mapped_fields: ['language', 'minutes', 'charge']

### Standardizer Agent

- **Records extracted**: file: Wellspace - LanguageLine Invoice.XLS, sheet: Call Detail Summary Report, records: 0

### Schema Agent

- **Column mapping**: sheet: Insight, confidence: 100%, mapped_fields: ['date', 'language', 'minutes', 'charge']

### Standardizer Agent

- **Records extracted**: file: Wellspace - LanguageLine Invoice.XLS, sheet: Insight, records: 34

### Schema Agent

- **Column mapping**: sheet: Misc Charges Detail, confidence: 50%, mapped_fields: ['date', 'minutes']

### Standardizer Agent

- **Records extracted**: file: Wellspace - LanguageLine Invoice.XLS, sheet: Misc Charges Detail, records: 0

### Rate Card Agent

- **Started validation**: input_records: 280720
- **Cost validation complete**: records_with_cost: 228894, records_missing_cost: 51826

### Modality Agent

- **Started refinement**: input_records: 280720
- **Distribution**: OPI: 221282, VRI: 7578, OnSite: 0, Translation: 0, Unknown: 51860

### QA Agent

- **Started validation**: input_records: 280720
- **Duplicate detection**: duplicates_removed: 131589
- **Quality flags**: outliers_flagged: 532, critical_errors: 2

### Aggregator Agent

- **Started aggregation**: input_records: 149131
- **Baseline created**: rows: 2175, total_cost: $2,219,389.98, total_minutes: 4,065,319, total_calls: 149,131

---

## ISSUES DETECTED


### Schema Agent Issues:

- Healthpoint - Propio Transaction Download.xlsx/Beyond a Year: Low mapping confidence (0%)

### Rate Card Agent Issues:

- 51,826 records have no cost data
-   - Vendor 'Wellspace' has no cost column in source file
-   - Vendor 'Peak' has no cost column in source file
-   - Vendor 'VFC' has no cost column in source file

### Modality Agent Issues:

- 51,860 records had unrecognized modality

### QA Agent Issues:

- FOUND: 131,589 duplicate records removed
- FLAGGED: 532 outlier records
-   - Excessive Duration (> 240.0 min): 262
-   - Statistical Rate Outlier (Z=10.2): 197
-   - Statistical Rate Outlier (Z=7.5): 42