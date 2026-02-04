# 🚀 Quick Start Guide - Multi-Agent Baseline Factory

This guide will help you run the baseline factory on new data files.

---

## 📋 Prerequisites

- Python 3.11+
- Required packages: `pandas`, `openpyxl`, `xlrd`

---

## 🏃 Running the Pipeline

### Step 1: Prepare Your Data
Place your vendor Excel/CSV files in the `data_files/Language Services/` directory.

**Supported formats:**
- `.xlsx` (Excel 2007+)
- `.xls` (Excel 97-2003)
- `.csv` (Comma-separated values)

### Step 2: Run the Pipeline
```bash
cd C:\Users\John\.gemini\antigravity\playground\multiagent-baseline-lt
python multi_agent_system\run_pipeline.py
```

### Step 3: Review the Output
The pipeline will generate:
- `baseline_v1_output.csv` - Your final baseline table
- `pipeline_log.txt` - Detailed processing log
- Console output with all agent reports

---

## 📊 Understanding the Output

### Baseline Table Columns:
- **Month:** YYYY-MM format (e.g., "2024-01")
- **Vendor:** Vendor name extracted from filename
- **Language:** Standardized language name
- **Modality:** OPI, VRI, OnSite, or Translation
- **Minutes:** Total billable minutes
- **Cost:** Total charges
- **Calls:** Number of calls/sessions
- **CPM:** Cost per minute (Cost / Minutes)
- **Avg_Call_Length:** Average call duration (Minutes / Calls)

### Agent Reports in Console:

#### 1. Intake Agent
Shows files discovered and loaded.

#### 2. Schema Agent
Shows mapping confidence and column matches:
- **1.00:** Perfect match (all critical columns found)
- **0.75:** Good match (most columns found)
- **0.50:** Partial match (some columns missing)
- **0.00:** No match (skipped)

#### 3. Standardizer Agent
Shows number of valid records extracted per sheet.

#### 4. Rate Card Agent
Shows cost imputation statistics:
- Total records processed
- Number of records with imputed costs
- Total dollar amount imputed

#### 5. Modality Agent
Shows distribution across OPI/VRI/OnSite/Translation.

#### 6. QA Agent
Shows data quality metrics:
- Duplicates removed
- Quality issues flagged
- Critical errors quarantined
- Top issues detected

#### 7. Reconciliation Agent
Shows calculated vs. billed totals per vendor.

#### 8. Analyst Agent
Shows month-over-month variance analysis:
- Total spend change
- Volume effect (usage changes)
- Price effect (rate changes)
- Mix effect (service type shifts)

#### 9. Simulator Agent
Shows savings opportunities:
- Rate standardization savings
- Modality shift savings

---

## 🔧 Customizing the Rate Card

### Step 1: Export Current Rates
```bash
python export_rate_card.py
```

This creates `rate_card_current.csv` with all rates currently in the system.

### Step 2: Edit the Rate Card
Open `rate_card_current.csv` in Excel and update rates:

**Format:**
```csv
Vendor,Modality,Language,Rate
Healthpoint,OPI,Spanish,0.75
Nuvance,VRI,Spanish,0.95
Peak,OPI,,0.70
,OPI,Dari,0.80
```

**Rules:**
- Leave Vendor blank for industry averages
- Leave Language blank for modality-only rates
- More specific rates override general ones

### Step 3: Import Updated Rates
Edit `multi_agent_system/src/agents/rate_card_agent.py`:

```python
def _load_default_rates(self):
    # Option 1: Load from CSV
    import pandas as pd
    df = pd.read_csv("rate_card_current.csv")
    rates = {}
    for _, row in df.iterrows():
        key = (row['Vendor'] or None, row['Modality'], row['Language'] or None)
        rates[key] = row['Rate']
    return rates
```

---

## 🎯 Adjusting Simulator Targets

Edit `multi_agent_system/run_pipeline.py`:

```python
# Change target rates for simulations
simulator = SimulatorAgent(
    target_opi_rate=0.65,  # Target OPI rate
    target_vri_rate=0.85   # Target VRI rate
)
```

---

## 🔍 Troubleshooting

### Issue: "No files found"
**Solution:** Check that files are in `data_files/Language Services/` directory.

### Issue: "Schema confidence too low"
**Solution:** The file format is unusual. Check `pipeline_log.txt` for the attempted column mapping. You may need to add custom mappings in `schema_agent.py`.

### Issue: "UnicodeEncodeError"
**Solution:** This is a Windows terminal encoding issue. The pipeline will still complete successfully. Check `baseline_v1_output.csv` for results.

### Issue: "Missing rates for imputation"
**Solution:** Some vendor/modality/language combinations don't have rates in the rate card. Update `rate_card_agent.py` with actual contract rates.

---

## 📅 Monthly Baseline Updates

### Recommended Workflow:

1. **Week 1 of Month:** Collect vendor invoices/reports
2. **Week 2:** Place files in `data_files/Language Services/`
3. **Week 2:** Run pipeline: `python multi_agent_system\run_pipeline.py`
4. **Week 2:** Review QA statistics in console output
5. **Week 3:** Analyze variance report (Analyst Agent output)
6. **Week 3:** Review savings opportunities (Simulator Agent output)
7. **Week 4:** Share `EXECUTIVE_SUMMARY.md` with stakeholders

---

## 🎓 Advanced Usage

### Running on Specific Files Only
Edit `run_pipeline.py`:

```python
# Only process files matching a pattern
files = [f for f in files if "Healthpoint" in f]
```

### Changing QA Thresholds
Edit the QA Agent initialization in `run_pipeline.py`:

```python
qa_agent = QAgent(
    rate_std_dev_threshold=4.0,  # Stricter outlier detection (default: 3.0)
    duration_max_minutes=180.0   # Lower max duration (default: 240.0)
)
```

### Exporting to Excel Instead of CSV
Edit the end of `run_pipeline.py`:

```python
# Save as Excel with formatting
baseline_table.to_excel("baseline_v1_output.xlsx", index=False)
```

---

## 📞 Support

For questions or issues:
1. Check `pipeline_log.txt` for detailed error messages
2. Review `PROJECT_COMPLETION.md` for architecture details
3. Consult `multi_agent_architecture_v2.md` for agent specifications

---

**Happy Analyzing!** 🎉
