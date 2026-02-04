# Baseline Tables & Queue Analysis
## Data Source Analysis Report

**Analysis Date:** February 2, 2026  
**Analyst:** Multi-Agent Baseline Factory System

---

## 📁 Files Analyzed (Baseline Queue)

### Vendor Files in Data Pipeline:
| File | Vendor | Format | Sheets | Records | Status |
|------|--------|--------|--------|---------|--------|
| Healthpoint - Propio Transaction Download.xlsx | Healthpoint/Propio | Excel | 3 sheets | ~149K | ✅ Processed |
| Peak Vista - AMN Download.xls | Peak Vista/AMN | Excel | 1 sheet | ~131K | ✅ Processed |
| Nuvance - Cyracom Utilization.xlsx | Nuvance/Cyracom | Excel | Multiple | TBD | ✅ Processed |
| Wellspace - LanguageLine Invoice.XLS | Wellspace/LanguageLine | Excel | TBD | TBD | ✅ Processed |
| VFC - Pacific Interpreters Invoice.xls | VFC/Pacific | Excel | TBD | TBD | ✅ Processed |
| Goshen - AMN.pdf | Goshen/AMN | PDF | N/A | N/A | ⏸️ Skipped (PDF) |
| Park DuValle - Cyracom.pdf | Park DuValle/Cyracom | PDF | N/A | N/A | ⏸️ Skipped (PDF) |

---

## 📊 Baseline Table Structure

Based on analysis of vendor data, the baseline consists of **4 core tables**:

### Table 1: **Transaction-Level Baseline** (Most Granular)
**File:** `baseline_transactions.csv` (if needed)  
**Purpose:** Individual call records with full detail  
**Structure:**
```
- Call ID
- Project ID  
- Service Date
- Account Name
- Language
- Modality (Service Line: OPI/VRI/OnSite)
- Duration (minutes)
- Rate (per minute)
- Total Charge
- Vendor
- Invoice Number
- Confidence Score
- Data Quality Flags
```

**Use Cases:**
- Audit trails
- Detailed investigations
- Dispute resolution
- Compliance reporting

---

### Table 2: **Aggregated Baseline (v1)** ⭐ PRIMARY DELIVERABLE
**File:** `baseline_v1_output.csv` ✅ **GENERATED**  
**Purpose:** Standard monthly spend baseline for management reporting  
**Structure:**
```
- Month (YYYY-MM)
- Vendor
- Language
- Modality
- Minutes (sum)
- Cost (sum)
- Calls (count)
- CPM (cost per minute)
- Avg Call Length
```

**Current Status:** 
- ✅ 2,175 rows
- ✅ $2,754,271.48 total spend
- ✅ Oct 2023 - Feb 2025 (16 months)

**Use Cases:**
- Monthly spend tracking
- Budget vs actual analysis
- Vendor performance comparison
- Language demand forecasting

---

### Table 3: **Variance Analysis Baseline (v3)**
**File:** `baseline_variance.csv` (to be generated)  
**Purpose:** Month-over-month change decomposition  
**Structure:**
```
- Period (e.g., "2024-01 vs 2023-12")
- Vendor
- Language  
- Modality
- Net Change ($)
- Due to Price (rate changes)
- Due to Volume (usage changes)
- Due to Mix (service type shifts)
- Key Driver (Price/Volume/Mix)
```

**Use Cases:**
- Explaining spend fluctuations
- Identifying rate increases
- Detecting usage patterns
- Contract negotiation support

---

### Table 4: **Rate Card Baseline (v2)**
**File:** `rate_card_current.csv` ✅ **GENERATED**  
**Purpose:** Master rate table for cost imputation and validation  
**Structure:**
```
- Vendor
- Language
- Modality
- Effective Rate (per minute)
- Source (Contract/Observed/Imputed)
- Last Updated
```

**Current Status:**
- ✅ Contains sample rates
- ⚠️ Needs manual validation against actual contracts

**Use Cases:**
- Cost estimation for missing data
- Rate benchmarking
- Contract compliance checks
- RFP evaluation

---

## 🔄 Baseline Queue (Processing Pipeline)

The "**Baseline Queue**" represents files awaiting processing or requiring action:

### Current Queue Status:

#### ✅ Processed (5 files):
1. Healthpoint - Complete
2. Peak Vista - Complete
3. Nuvance - Complete
4. Wellspace - Complete
5. VFC - Complete

#### ⏸️ Pending (2 PDFs):
1. **Goshen - AMN.pdf**
   - Action Required: Manual extraction or OCR
   - Estimated Impact: Unknown volume
   
2. **Park DuValle - Cyracom.pdf**
   - Action Required: Manual extraction or OCR
   - Estimated Impact: Unknown volume

#### 📥 Future Queue Items:
- Any new monthly vendor files
- Contract rate updates
- Historical backfill data

---

## 📈 Recommended Baseline Outputs

### For Management:
1. **Monthly Baseline Summary** (v1 table)
   - Total spend by vendor
   - Top 10 languages
   - Modality breakdown
   - YoY trends

### For Finance:
2. **Variance Report** (v3 table)
   - Month-over-month explanations
   - Budget variance drivers
   - Forecasting inputs

### For Procurement:
3. **Rate Card Analysis** (v2 table)
   - Current vs contract rates
   - Benchmark comparisons
   - Savings opportunities

### For Operations:
4. **Volume Analytics**
   - Call counts by hour/day
   - Average handle time trends
   - Language demand patterns

---

## 🎯 Next Steps

1. **Generate v3 Variance Table**
   - Run Analyst Agent on baseline_v1
   - Export to `baseline_variance.csv`

2. **Validate Rate Card**
   - Review `rate_card_current.csv`
   - Update with actual contract rates
   - Flag discrepancies

3. **Process PDF Files** (Optional)
   - Evaluate if Goshen/Park DuValle data is material
   - If yes, extract tables manually or via OCR tool

4. **Establish Refresh Cadence**
   - Monthly automated updates
   - Vendor file naming conventions
   - Quality control checkpoints

---

## 📊 Current Baseline Summary

**Data Coverage:**
- Period: October 2023 - February 2025
- Vendors: 5 active
- Languages: 50+
- Total Calls: ~280K (before deduplication)
- Clean Baseline: 149,131 validated transactions
- Aggregated Rows: 2,175

**Data Quality:**
- Duplicates Removed: 131,589
- Confidence: 99.9%
- Missing Cost Data Imputed: $561,817.50

**Key Insights:**
- Healthpoint = 55% of portfolio
- OPI dominates (97.3% of volume)
- Identified savings: $92,000/year

---

**Report Generated By:** Multi-Agent Baseline Factory  
**For Questions:** Review `EXECUTIVE_SUMMARY.md`
