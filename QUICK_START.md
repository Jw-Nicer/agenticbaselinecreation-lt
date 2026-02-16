# 🚀 Quick Start Guide - Multi-Agent Baseline Factory

This guide will help you run the baseline factory on new data files.

---

## 📋 Prerequisites

- Python 3.11+
- Required packages:
  ```bash
  pip install pandas openpyxl xlrd pytest tqdm streamlit altair
  ```

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
*Tip: You will see a progress bar indicating the processing status.*

### Step 3: Run Tests (Optional)
To ensure everything is working correctly, you can run the test suite:
```bash
python -m pytest tests/
```

### Step 4: Review the Output
The pipeline will generate:
- `baseline_v1_output.csv` - Your final baseline table
- `pipeline_log.txt` - Detailed processing log
- Console output with all agent reports

---

## 🖥️ Optional: Run the Dashboard
```bash
streamlit run dashboard_enhanced.py
```
Note: `dashboard_legacy.py` is legacy and will be removed in a future cleanup.

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

---

## 🔧 Managing Verified Contract Rates

### Step 1: Export Current Rates
```bash
python export_rate_card.py
```

### Step 2: Edit the Rate Card
Open `rate_card_current.csv` in Excel and update rates:

**Format:**
```csv
Vendor,Modality,Language,Rate
Healthpoint,OPI,Spanish,0.75
Nuvance,VRI,Spanish,0.95
```

### Step 3: Import Updated Rates
Edit `multi_agent_system/src/agents/rate_card_agent.py` to load this CSV.

---

## 🔍 Troubleshooting

### Issue: "No files found"
**Solution:** Check that files are in `data_files/Language Services/` directory.

### Issue: "Schema confidence too low"
**Solution:** The file format is unusual. Check `pipeline_log.txt` for the attempted column mapping. You may need to add custom mappings in `schema_agent.py`.

### Issue: "UnicodeEncodeError"
**Solution:** This is a Windows terminal encoding issue. The pipeline will still complete successfully. Check `baseline_v1_output.csv` for results.

### Issue: "Processing seems stuck"
**Solution:** The Standardizer Agent uses tqdm, so check the progress bar. If it's truly stuck, ensure you don't have a corrupted 0-byte file.

---

## 📞 Support
For questions or issues:
1. Check `pipeline_log.txt` for detailed error messages
2. Consult `SYSTEM_ARCHITECTURE_MAP.md` for logic flow.

**Happy Analyzing!** 🎉
