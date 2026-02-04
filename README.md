# 🏭 Multi-Agent Baseline Factory

**A production-ready AI system for transforming raw language services data into strategic financial intelligence.**

---

## 🚀 Quick Links
- **[Executive Summary](EXECUTIVE_SUMMARY.md)** - 📊 Final results, savings, and strategy (**Start Here** for business insights).
- **[Quick Start Guide](QUICK_START.md)** - 🏃 Instruction manual for running the pipeline on new data.
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
```bash
# Run the full pipeline
python multi_agent_system/run_pipeline.py
```

The system will output:
- **`baseline_v1_output.csv`**: The clean, standardized database.
- **`pipeline_log.txt`**: Detailed processing logs.
- **Console Report**: Real-time insights from all 9 agents.

---

## 📁 Repository Structure
```
.
├── multi_agent_system/         # Source code for agents
│   ├── src/agents/             # Individual agent logic
│   └── run_pipeline.py         # Main orchestrator script
├── data_files/                 # Input data directory
├── baseline_v1_output.csv      # Output database
└── rate_card_current.csv       # Configuration for rates
```

*Built by Antigravity AI - February 2026*
