# 🤖 Agent Operating Guide

Welcome, Jules or Codex. This repository is optimized for autonomous operation.

## 🎯 Mission
The goal of this system is to transform messy vendor interpretation data into a clean, aggregated baseline.

## 🛠️ Operational Commands

### 1. Environment Setup
```bash
pip install -r requirements.txt
```

### 2. Running the Pipeline
Always use the `./baseline` entrypoint.
```bash
./baseline run --input <path_to_data> --client <client_name>
```

### 3. Verification
Run tests after any code change:
```bash
pytest tests/
```

## 📂 Key Data Locations
- **Schemas**: `multi_agent_system/src/core/canonical_schema.py` defines the source of truth for records.
- **Fixtures**: `tests/fixtures/` contains sample CSVs for testing.
- **Config**: `config/schema_config.json` controls mapping sensitivity.
- **Memory**: `agent_memory/` contains learned mappings and file classifications.

## 🧠 Core Logic
- **IntakeAgent**: Detects header rows and scores sheets for transaction data.
- **SchemaAgent**: Infers column mappings using keywords, type inference, and AI.
- **StandardizerAgent**: Converts raw rows into `CanonicalRecord` (Pydantic model).
- **QA_Agent**: Removes duplicates and flags rate outliers.

## 🚦 Guidelines
- **Idempotency**: All outputs go to `out/<client>/<timestamp>`. Do not rely on root-level CSVs.
- **Validation**: Every run generates a `manifest.json`. Check this for `status: "COMPLETE"`.
- **Debugging**: If mappings fail, check `out/.../audit_logs.json` to see why the SchemaAgent skipped a sheet.
- **Adding Vendors**: Most vendors work via keyword matching. If a new vendor has weird headers, add them to `CANONICAL_FIELDS` in `canonical_schema.py`.
