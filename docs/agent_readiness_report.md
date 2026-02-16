# Agent Readiness Report - Baseline Factory Audit

## Current State Assessment

### What the repo currently does
The repository contains a multi-agent system designed to process language services usage data (OPI, VRI, On-Site) from various vendors. It handles:
- **Ingestion**: Scanning Excel/CSV files.
- **Mapping**: Inferring schema mappings using heuristics and AI.
- **Standardization**: Converting raw data to a canonical format.
- **Validation**: Imputing costs via rate cards, detecting duplicates, and identifying outliers.
- **Analysis**: Performing Price-Volume-Mix variance analysis and running savings simulations.
- **Reporting**: Generating aggregated baseline tables and activity logs.

### How to run it
Currently, the pipeline is triggered by:
```bash
python multi_agent_system/run_pipeline.py
```
There is also an enhanced dashboard using Streamlit:
```bash
streamlit run dashboard_enhanced.py
```

### Agent-Readiness Assessment
**Status: Ready**

- **Clear entrypoints**: Unified `./baseline` CLI implemented with subcommands (`run`, `ingest`, `extract`, etc.).
- **Deterministic runs**: High determinism with heuristic fallbacks and config-driven mapping.
- **Test harness**: E2E and unit tests implemented in `tests/` using `pytest`.
- **Config**: `requirements.txt` added; configuration centralized in `config/`.
- **Logging**: Structured `audit_logs.json` and `manifest.json` produced for every run.
- **Idempotent outputs**: Structured output directory `out/<client>/<timestamp>/` prevents overwriting and enables versioning.
- **Minimal manual steps**: Golden dataset in `tests/fixtures/` allows immediate verification.

### Gaps Blocking Reliable Generation
1. **Missing Input Data**: The `data_files/Language Services` directory is empty in the current state, preventing the pipeline from running out-of-the-box.
2. **Monolithic Entrypoint**: Hard to run just one part of the pipeline (e.g., only "extract" or only "validate").
3. **Environment Setup**: No `requirements.txt` or `pyproject.toml` to quickly install dependencies.
4. **Output Structure**: Outputs are dumped in the root directory rather than a structured `out/` folder.
5. **Validation Schema**: No formal schema contract (e.g., Pydantic) for standardized records.

## Improvements Implemented

1.  ✅ **Unified CLI**: Added `./baseline` wrapper for easy agent interaction.
2.  ✅ **Golden Dataset**: Added synthetic transactions in `tests/fixtures/` for testing.
3.  ✅ **Structured Outputs**: Implemented `out/` directory with `manifest.json` and versioned runs.
4.  ✅ **Pydantic Validation**: Upgraded `CanonicalRecord` to Pydantic for strict data validation.
5.  ✅ **Agent Guide**: Created `AGENTS.md` with operational instructions.

## Final Recommendations
The repository is now "agent-enabled". Future agents can clone, install dependencies, and run the pipeline deterministically using the `./baseline` command.
