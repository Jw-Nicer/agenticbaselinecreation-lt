# 🏭 Multi-Agent Baseline Factory

**A production-ready AI system for transforming raw language services data into strategic financial intelligence.**

---

## 🚀 Quick Links
- **[Executive Summary](EXECUTIVE_SUMMARY.md)** - 📊 Final results, savings, and strategy (**Start Here** for business insights).
- **[Quick Start Guide](QUICK_START.md)** - 🏃 Instruction manual for running the pipeline on new data.
- **[Dashboard UI](dashboard_enhanced.py)** - 🖥️ Run `streamlit run dashboard_enhanced.py` (**primary UI**).
- **[Project Completion](PROJECT_COMPLETION.md)** - 🏆 Comprehensive technical report, metrics, and roadmap.
- **[Implementation Plan](CURRENT_IMPLEMENTATION_PLAN.md)** - 🗺️ Original project roadmap and status.

---

## 🎯 System Capabilities
This system uses a team of **9 Specialized AI Agents** to automate the entire data analysis lifecycle:

1.  **Ingest:** Reads raw, messy Excel/CSV files from multiple vendors.
2.  **Clean:** Maps schemas, standardizes dates/currencies, and removes duplicates.
3.  **Enrich:** Imputes missing costs using a hierarchical rate card.
4.  **Verify:** Checks data against "Ground Truth" invoices (Reconciliation).
5.  **Analyze:** Decomposes spend changes into Price, Volume, and Mix effects.
6.  **Simulate:** Models "What-If" savings scenarios (e.g., Modality Shifts).

---

## 💰 Key Outcomes (Feb 2026 Run)
- **Portfolio Analyzed:** $2.75M Spend
- **Records Processed:** 280,000+ (100% automated)
- **Cost Recovered:** $561,817 (Imputed missing data)
- **Savings Identified:** ~$92,000/year (Rate Caps & Modality Shifts)

---

## 🛠️ How to Run

### Quickstart (Agent-Enabled)
```bash
# Install dependencies
pip install -r requirements.txt

# Run the full pipeline on sample data
./baseline run --input tests/fixtures --client test_client
```

### CLI Usage
The `./baseline` CLI provides several subcommands:
- `run`: Run the full end-to-end pipeline.
- `ingest`: Scan and classify input files.
- `extract`: Map schemas and standardize data.
- `validate`: Apply QA rules and validate against rate cards.
- `report`: Generate final baseline reports.

**Common Options:**
- `--input`, `-i`: Path to the directory containing vendor files.
- `--client`, `-c`: Client name for output organization.

### Outputs
Pipeline results are written to a structured directory:
`out/<client>/<timestamp>/`

Each run produces:
- `baseline_v1_output.csv`: Aggregated baseline spend table.
- `baseline_transactions.csv`: Cleaned transaction-level data.
- `manifest.json`: Machine-readable run summary.
- `AGENT_ACTIVITY_LOG.md`: Human-readable processing log.
- `audit_logs.json`: Detailed agent mapping and processing logs.

## 🖥️ UI Dashboard
```bash
streamlit run dashboard_enhanced.py
```
Note: `dashboard_legacy.py` is legacy and will be removed in a future cleanup.

---

## 📁 Repository Structure
```
.
├── baseline                    # Primary CLI entrypoint
├── multi_agent_system/         # Source code for agents
│   ├── src/                    # Core logic and agent definitions
│   └── run_pipeline.py         # Pipeline orchestrator
├── out/                        # Structured output directory
├── tests/                      # Unit and E2E tests
│   └── fixtures/               # Golden dataset
├── docs/                       # Reports and documentation
├── requirements.txt            # Dependency manifest
└── rate_card_current.csv       # Hierarchical rate card config
```

## 🧪 Testing
```bash
# Run all tests
pytest tests/
```

*Built by Antigravity AI - February 2026*
