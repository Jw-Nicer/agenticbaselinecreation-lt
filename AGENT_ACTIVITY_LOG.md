# AGENT PIPELINE ACTIVITY LOG

**Processing Date:** 2026-02-05 13:35:43
**Duration:** 251.6 seconds

---

## AGENT SUMMARY

| Agent | Key Metric | Status |
|-------|------------|--------|
| Intake Agent | 5 files found | OK |
| Schema Agent | 5 files mapped | ISSUE |
| Standardizer Agent | 280,733 total records extracted | OK |
| Rate Card Agent | 235,856 with cost, 44,877 missing | ISSUE |
| Modality Agent | OPI:235,952 VRI:37,798 | OK |
| QA Agent | 162,396 duplicates, 4,285 outliers | ISSUE |
| Reconciliation Agent | MATCH | $2,302,469.18 variance | OK |
| Aggregator Agent | $2,302,469.18 total spend | OK |
| Analyst Agent | 2024-12 -> 2025-02: $-25,215.90 variance | OK |
| Simulator Agent | $15,877.01 potential savings | OK |

---

## DETAILED ACTIVITY LOG


### Orchestrator

- **AI mode**: status: ENABLED

### Intake Agent

- **Started scanning**: directory: C:\Users\John\.gemini\antigravity\playground\multiagent-baseline-lt\data_files\Language Services
- **Files discovered**: count: 5
- **File found**: filename: Healthpoint - Propio Transaction Download.xlsx
- **File found**: filename: Nuvance - Cyracom Utilization.xlsx
- **File found**: filename: Peak Vista - AMN Download.xls
- **File found**: filename: VFC - Pacific Interpreters Invoice.xls
- **File found**: filename: Wellspace - LanguageLine Invoice.XLS

### Schema Agent

- **Processing file**: file: Healthpoint - Propio Transaction Download.xlsx, vendor: Healthpoint
- **Column mapping**: sheet: ag-grid, confidence: 100%, field_confidence: 100%, data_confidence: 100%, source: ai, mapped_fields: ['date', 'language', 'minutes', 'charge', 'rate', 'modality']

### Standardizer Agent

- **Records extracted**: file: Healthpoint - Propio Transaction Download.xlsx, sheet: ag-grid, records: 227272

### Schema Agent

- **Column mapping**: sheet: Pivot, confidence: 96%, field_confidence: 100%, data_confidence: 100%, source: ai, mapped_fields: ['date', 'language', 'minutes', 'charge', 'rate', 'modality']

### Standardizer Agent

- **Records extracted**: file: Healthpoint - Propio Transaction Download.xlsx, sheet: Pivot, records: 13

### Schema Agent

- **Column mapping**: sheet: Beyond a Year, confidence: 50%, field_confidence: 50%, data_confidence: 100%, source: ai, mapped_fields: ['date', 'language', 'modality']
- **SKIPPED - Low confidence**: sheet: Beyond a Year
- **Processing file**: file: Nuvance - Cyracom Utilization.xlsx, vendor: Nuvance
- **Column mapping**: sheet: Raw Data OPI.VRI, confidence: 98%, field_confidence: 100%, data_confidence: 100%, source: ai, mapped_fields: ['date', 'language', 'minutes', 'charge', 'rate', 'modality']

### Standardizer Agent

- **Records extracted**: file: Nuvance - Cyracom Utilization.xlsx, sheet: Raw Data OPI.VRI, records: 1588

### Schema Agent

- **Processing file**: file: Peak Vista - AMN Download.xls, vendor: Peak
- **Column mapping**: sheet: Sheet0, confidence: 75%, field_confidence: 75%, data_confidence: 100%, source: ai, mapped_fields: ['date', 'language', 'minutes', 'modality']

### Standardizer Agent

- **Records extracted**: file: Peak Vista - AMN Download.xls, sheet: Sheet0, records: 44877

### Schema Agent

- **Processing file**: file: VFC - Pacific Interpreters Invoice.xls, vendor: VFC
- **Column mapping**: sheet: Call Detail, confidence: 100%, field_confidence: 100%, data_confidence: 100%, source: ai, mapped_fields: ['date', 'language', 'minutes', 'charge']

### Standardizer Agent

- **Records extracted**: file: VFC - Pacific Interpreters Invoice.xls, sheet: Call Detail, records: 622

### Schema Agent

- **Column mapping**: sheet: Invoice, confidence: 25%, field_confidence: 25%, data_confidence: 100%, source: heuristic_ai, mapped_fields: ['minutes']
- **SKIPPED - Low confidence**: sheet: Invoice
- **Processing file**: file: Wellspace - LanguageLine Invoice.XLS, vendor: Wellspace
- **Column mapping**: sheet: Call Detail, confidence: 100%, field_confidence: 100%, data_confidence: 100%, source: ai, mapped_fields: ['date', 'language', 'minutes', 'charge']

### Standardizer Agent

- **Records extracted**: file: Wellspace - LanguageLine Invoice.XLS, sheet: Call Detail, records: 6327

### Schema Agent

- **Column mapping**: sheet: Call Detail Summary Report, confidence: 75%, field_confidence: 75%, data_confidence: 100%, source: ai, mapped_fields: ['language', 'minutes', 'charge']

### Standardizer Agent

- **Records extracted**: file: Wellspace - LanguageLine Invoice.XLS, sheet: Call Detail Summary Report, records: 0

### Schema Agent

- **Column mapping**: sheet: Insight, confidence: 93%, field_confidence: 100%, data_confidence: 95%, source: cache, mapped_fields: ['date', 'language', 'minutes', 'charge']

### Standardizer Agent

- **Records extracted**: file: Wellspace - LanguageLine Invoice.XLS, sheet: Insight, records: 34

### Schema Agent

- **Column mapping**: sheet: Misc Charges Detail, confidence: 50%, field_confidence: 50%, data_confidence: 100%, source: heuristic_ai, mapped_fields: ['date', 'charge']
- **SKIPPED - Low confidence**: sheet: Misc Charges Detail

### Rate Card Agent

- **Started validation**: input_records: 280733
- **Cost validation complete**: records_with_cost: 235856, records_missing_cost: 44877

### Modality Agent

- **Started refinement**: input_records: 280733
- **Distribution**: OPI: 235952, VRI: 37798, OnSite: 0, Translation: 6983, Unknown: 0

### QA Agent

- **Started validation**: input_records: 280733
- **Duplicate detection**: duplicates_removed: 162396
- **Quality flags**: outliers_flagged: 4285, critical_errors: 2

### Reconciliation Agent

- **Started reconciliation**: input_records: 118337
- **Reconciliation complete**: overall_status: MATCH, total_variance: $2,302,469.18, vendors: 5

### Aggregator Agent

- **Started aggregation**: input_records: 118337
- **Baseline created**: rows: 2313, total_cost: $2,302,469.18, total_minutes: 3,759,857, total_calls: 118,337

---

## ISSUES DETECTED


### Schema Agent Issues:

- Healthpoint - Propio Transaction Download.xlsx/Beyond a Year: Low mapping confidence (50%)
- VFC - Pacific Interpreters Invoice.xls/Invoice: Low mapping confidence (25%)
- Wellspace - LanguageLine Invoice.XLS/Misc Charges Detail: Low mapping confidence (50%)

### Rate Card Agent Issues:

- 44,877 records have no cost data
-   - Vendor 'Peak' has no cost column in source file

### QA Agent Issues:

- FOUND: 162,396 duplicate records removed
- FLAGGED: 4,285 outlier records
-   - Statistical Rate Outlier (Z=3.1): 2,984
-   - Statistical Rate Outlier (Z=5.0): 546
-   - Excessive Duration (> 240.0 min): 266

### Reconciliation Agent Issues:

- Healthpoint: NO_INVOICE_FOUND (variance 0.00%)
- Nuvance: NO_INVOICE_FOUND (variance 0.00%)
- Peak: NO_INVOICE_FOUND (variance 0.00%)
- VFC: NO_INVOICE_FOUND (variance 0.00%)
- Wellspace: NO_INVOICE_FOUND (variance 0.00%)