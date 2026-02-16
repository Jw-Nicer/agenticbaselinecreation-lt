
import os
import sys
import datetime
from pathlib import Path
import json
import subprocess
import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables
load_dotenv()

# Ensure src is in path
# Determine paths
current_dir = Path(__file__).resolve().parent
PROJECT_ROOT = current_dir.parent
SRC_PATH = current_dir / "src"

# Add src to pythonpath
if SRC_PATH.exists():
    sys.path.append(str(SRC_PATH))

# Import agents after path setup
from agents.intake_agent import IntakeAgent
from agents.schema_agent import SchemaAgent
from agents.standardizer_agent import StandardizerAgent
from agents.rate_card_agent import RateCardAgent
from agents.modality_agent import ModalityRefinementAgent
from agents.qa_agent import QAgent
from agents.reconciliation_agent import ReconciliationAgent
from agents.analyst_agent import AnalystAgent
from agents.simulator_agent import SimulatorAgent
from agents.aggregator_agent import AggregatorAgent
from core.activity_logger import reset_logger, get_logger
from core.ai_client import AIClient

# Update base_dir to project root for data access
BASE_DIR = PROJECT_ROOT

def main():
    base_dir = BASE_DIR
    
    # Configuration from environment
    client_name = os.getenv("CLIENT_NAME", "default")
    input_dir = os.getenv("INPUT_DIR", str(base_dir / "data_files" / "Language Services"))
    data_dir = Path(input_dir)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_base = base_dir / "out" / client_name / timestamp
    output_base.mkdir(parents=True, exist_ok=True)

    # Initialize activity logger
    logger = reset_logger()
    
    # Ensure output directory exists in project root or multi_agent_system?
    # Let's write output to project root for visibility
    output_dir = base_dir
    
    ai_status = "ENABLED" if AIClient().enabled else "DISABLED"
    print(f"AI MODE: {ai_status}")
    logger.log("Orchestrator", "AI mode", {"status": ai_status})
    
    print("=" * 60)
    print("BASELINE FACTORY - MULTI-AGENT SYSTEM")
    print("=" * 60)
    
    # =========================================================================
    # AGENT 1: INTAKE
    # =========================================================================
    print("\n[1/9] INTAKE AGENT - Scanning for files...")
    logger.log("Intake Agent", "Started scanning", {"directory": str(data_dir)})
    
    intake = IntakeAgent(str(data_dir))
    files = intake.scan_files()
    
    logger.log("Intake Agent", "Files discovered", {"count": len(files)})
    for f in files:
        logger.log("Intake Agent", "File found", {"filename": os.path.basename(f)})
    
    print(f"    Found {len(files)} files")
    
    logger.set_summary("Intake Agent", {
        "key_metric": f"{len(files)} files found",
        "status": "OK",
        "issues": []
    })
    
    records = []
    schema_detective = SchemaAgent()
    standardizer = StandardizerAgent()
    reconciler = ReconciliationAgent()
    
    files_with_issues = []
    schema_audit_log = []
    std_audit_log = []
    
    # =========================================================================
    # AGENT 2 & 3: SCHEMA + STANDARDIZER (per file)
    # =========================================================================
    print("\n[2/9] SCHEMA AGENT - Mapping columns...")
    print("[3/9] STANDARDIZER AGENT - Extracting records...")
    
    for filepath in tqdm(files, desc="Processing files", unit="file"):
        filename = os.path.basename(filepath)
        vendor = filename.split(" ")[0].split("-")[0].replace("_", "")
        
        logger.log("Schema Agent", f"Processing file", {"file": filename, "vendor": vendor})
        
        recon_sheets = intake.load_all_sheets_for_reconciliation(filepath)
        reconciler.extract_totals_from_sheets(recon_sheets, vendor)
        sheets = intake.load_clean_sheet(filepath)
        
        for sheet_name, df in sheets.items():
            cols = list(df.columns)
            mapping = schema_detective.infer_mapping(
                cols,
                df.iloc[0] if len(df) > 0 else None,
                vendor=vendor,
                df=df
            )
            conf = schema_detective.assess_mapping(df, mapping)
            score = conf["final_confidence"]
            min_final = schema_detective.min_final_confidence
            source = schema_detective.get_last_source()
            
            logger.log("Schema Agent", "Column mapping", {
                "sheet": sheet_name,
                "confidence": f"{score:.0%}",
                "field_confidence": f"{conf['field_confidence']:.0%}",
                "data_confidence": f"{conf['data_confidence']:.0%}",
                "source": source,
                "mapped_fields": list(mapping.keys())
            })
            
            schema_audit_log.append({
                "File": filename,
                "Sheet": sheet_name,
                "Confidence": f"{score:.1%}",
                "Field Confidence": f"{conf['field_confidence']:.1%}",
                "Data Confidence": f"{conf['data_confidence']:.1%}",
                "Source": source,
                "AI Reasoning": schema_detective.get_last_ai_reasoning(),
                "Status": "Success" if score >= min_final else "Skipped (Low Confidence)",
                "Columns Mapped": len(mapping),
                "Mapping": str(mapping) if score < 0.5 else None,
                "Date Col": mapping.get('date', 'MISSING'),
                "Lang Col": mapping.get('language', 'MISSING'),
                "Mins Col": mapping.get('minutes', 'MISSING'),
                "Cost Col": mapping.get('charge', mapping.get('cost', 'MISSING'))
            })
            
            if score < min_final:
                logger.log("Schema Agent", "SKIPPED - Low confidence", {"sheet": sheet_name})
                files_with_issues.append(f"{filename}/{sheet_name}: Low mapping confidence ({score:.0%})")
                continue

            schema_detective.confirm_mapping(
                source_columns=cols,
                mapping=mapping,
                vendor=vendor,
                data_confidence=conf["data_confidence"],
                field_confidence=conf["field_confidence"]
            )
            
            # Standardize
            new_records = standardizer.process_dataframe(df, mapping, filename, vendor)
            
            logger.log("Standardizer Agent", "Records extracted", {
                "file": filename,
                "sheet": sheet_name,
                "records": len(new_records)
            })
            
            std_audit_log.append({
                "File": filename,
                "Sheet": sheet_name,
                "Input Rows": len(df),
                "Extracted Records": len(new_records),
                "Dropped Rows": len(df) - len(new_records),
                "Status": "Success"
            })
            
            print(f"    {filename}: {len(new_records):,} records (confidence: {score:.0%})")
            records.extend(new_records)
    
    logger.set_summary("Schema Agent", {
        "key_metric": f"{len(files)} files mapped",
        "status": "OK" if not files_with_issues else "ISSUES",
        "issues": files_with_issues
    })
    
    logger.set_summary("Standardizer Agent", {
        "key_metric": f"{len(records):,} total records extracted",
        "status": "OK",
        "issues": []
    })
    
    # =========================================================================
    # AGENT 4: RATE CARD
    # =========================================================================
    print(f"\n[4/9] RATE CARD AGENT - Validating costs...")
    logger.log("Rate Card Agent", "Started validation", {"input_records": len(records)})
    
    rate_card = RateCardAgent()
    records, imputation_stats = rate_card.batch_impute(records)
    
    records_with_cost = imputation_stats.get('records_with_cost', 0)
    records_missing_cost = imputation_stats.get('records_missing_cost', 0)
    
    logger.log("Rate Card Agent", "Cost validation complete", {
        "records_with_cost": records_with_cost,
        "records_missing_cost": records_missing_cost
    })
    
    print(f"    Records with cost data: {records_with_cost:,}")
    print(f"    Records missing cost:   {records_missing_cost:,}")
    
    rate_issues = []
    if records_missing_cost > 0:
        missing_vendors = imputation_stats.get('missing_cost_vendors', [])
        rate_issues.append(f"{records_missing_cost:,} records have no cost data")
        for v in missing_vendors:
            rate_issues.append(f"  - Vendor '{v}' has no cost column in source file")
    
    logger.set_summary("Rate Card Agent", {
        "key_metric": f"{records_with_cost:,} with cost, {records_missing_cost:,} missing",
        "status": "OK" if records_missing_cost == 0 else "ISSUES",
        "issues": rate_issues
    })
    
    # =========================================================================
    # AGENT 5: MODALITY
    # =========================================================================
    print(f"\n[5/9] MODALITY AGENT - Refining service types...")
    logger.log("Modality Agent", "Started refinement", {"input_records": len(records)})
    
    modality_agent = ModalityRefinementAgent()
    m_stats = modality_agent.refine_records(records)
    
    logger.log("Modality Agent", "Distribution", {
        "OPI": m_stats['OPI'],
        "VRI": m_stats['VRI'],
        "OnSite": m_stats['OnSite'],
        "Translation": m_stats['Translation'],
        "Unknown": m_stats['Unknown']
    })
    
    print(f"    OPI: {m_stats['OPI']:,}, VRI: {m_stats['VRI']:,}, OnSite: {m_stats['OnSite']:,}")
    
    modality_issues = []
    if m_stats['Unknown'] > 0:
        modality_issues.append(f"{m_stats['Unknown']:,} records had unrecognized modality")
    
    logger.set_summary("Modality Agent", {
        "key_metric": f"OPI:{m_stats['OPI']:,} VRI:{m_stats['VRI']:,}",
        "status": "OK" if m_stats['Unknown'] == 0 else "ISSUES",
        "issues": modality_issues
    })
    
    # =========================================================================
    # AGENT 6: QA
    # =========================================================================
    print(f"\n[6/9] QA AGENT - Finding duplicates and outliers...")
    logger.log("QA Agent", "Started validation", {"input_records": len(records)})
    
    qa_agent = QAgent()
    records, qa_stats = qa_agent.process_records(records)
    
    logger.log("QA Agent", "Duplicate detection", {
        "duplicates_removed": qa_stats['duplicates_removed']
    })
    logger.log("QA Agent", "Quality flags", {
        "outliers_flagged": qa_stats['outliers_flagged'],
        "critical_errors": qa_stats['critical_errors_quarantined']
    })
    
    print(f"    Duplicates removed: {qa_stats['duplicates_removed']:,}")
    print(f"    Outliers flagged:   {qa_stats['outliers_flagged']:,}")
    print(f"    Records output:     {qa_stats['total_records_output']:,}")
    
    qa_issues = []
    if qa_stats['duplicates_removed'] > 0:
        qa_issues.append(f"FOUND: {qa_stats['duplicates_removed']:,} duplicate records removed")
    if qa_stats['outliers_flagged'] > 0:
        qa_issues.append(f"FLAGGED: {qa_stats['outliers_flagged']:,} outlier records")
    if qa_stats['issue_counts']:
        for issue, count in sorted(qa_stats['issue_counts'].items(), key=lambda x: x[1], reverse=True)[:3]:
            qa_issues.append(f"  - {issue}: {count:,}")
    
    logger.set_summary("QA Agent", {
        "key_metric": f"{qa_stats['duplicates_removed']:,} duplicates, {qa_stats['outliers_flagged']:,} outliers",
        "status": "OK" if qa_stats['critical_errors_quarantined'] == 0 else "ISSUES",
        "issues": qa_issues
    })

    # =========================================================================
    # AGENT 7: RECONCILIATION
    # =========================================================================
    print(f"\n[7/9] RECONCILIATION AGENT - Matching invoice totals...")
    logger.log("Reconciliation Agent", "Started reconciliation", {"input_records": len(records)})
    
    recon_results = reconciler.run_reconciliation(records)
    overall_status = recon_results.get("overall_status", "UNKNOWN")
    total_variance = recon_results.get("total_variance", 0.0)
    
    logger.log("Reconciliation Agent", "Reconciliation complete", {
        "overall_status": overall_status,
        "total_variance": f"${total_variance:,.2f}",
        "vendors": len(recon_results.get("vendors", {}))
    })
    
    print(f"    Overall status: {overall_status}")
    print(f"    Total variance: ${total_variance:,.2f}")
    
    recon_issues = []
    for vendor, stats in recon_results.get("vendors", {}).items():
        if stats.get("status") != "MATCH":
            recon_issues.append(
                f"{vendor}: {stats.get('status')} (variance {stats.get('variance_pct', 0):.2f}%)"
            )
    
    logger.set_summary("Reconciliation Agent", {
        "key_metric": f"{overall_status} | ${total_variance:,.2f} variance",
        "status": "OK" if overall_status == "MATCH" else "ISSUES",
        "issues": recon_issues
    })
    
    # =========================================================================
    # AGENT 8: AGGREGATOR
    # =========================================================================
    print(f"\n[8/9] AGGREGATOR AGENT - Creating baseline...")
    logger.log("Aggregator Agent", "Started aggregation", {"input_records": len(records)})
    
    aggregator = AggregatorAgent()
    baseline_table = aggregator.create_baseline(records)
    
    # Handle empty baseline
    if baseline_table.empty:
        total_cost = 0.0
        total_minutes = 0.0
        total_calls = 0
    else:
        total_cost = baseline_table['Cost'].sum()
        total_minutes = baseline_table['Minutes'].sum()
        total_calls = baseline_table['Calls'].sum()
    
    logger.log("Aggregator Agent", "Baseline created", {
        "rows": len(baseline_table),
        "total_cost": f"${total_cost:,.2f}",
        "total_minutes": f"{total_minutes:,.0f}",
        "total_calls": f"{total_calls:,.0f}"
    })
    
    print(f"    Baseline rows:  {len(baseline_table):,}")
    print(f"    Total cost:     ${total_cost:,.2f}")
    print(f"    Total minutes:  {total_minutes:,.0f}")

    # Sanity Checks
    if total_cost == 0 and len(records) > 0:
        print("  ⚠️ WARNING: Total cost is $0 despite having records. Check rate card/mapping.")
        logger.log("Orchestrator", "Sanity Check Warning", {"message": "Total cost is $0"})

    if len(records) == 0:
        print("  ❌ ERROR: No records processed. Check input files and schema mappings.")
        logger.log("Orchestrator", "Sanity Check Error", {"message": "No records processed"})
    
    logger.set_summary("Aggregator Agent", {
        "key_metric": f"${total_cost:,.2f} total spend",
        "status": "OK",
        "issues": []
    })

    # =========================================================================
    # AGENT 9: STRATEGY (ANALYST + SIMULATOR)
    # =========================================================================
    print(f"\n[9/9] STRATEGY AGENTS - Variance and savings analysis...")
    
    # Analyst
    analyst = AnalystAgent()
    analysis_results = analyst.analyze_variance(baseline_table)
    if isinstance(analysis_results, dict) and "status" not in analysis_results:
        analyst.print_summary(analysis_results)
        latest_period = list(analysis_results.keys())[-1] if analysis_results else None
        latest_variance = analysis_results[latest_period]["total_variance"] if latest_period else 0.0
        analyst_summary = f"{latest_period}: ${latest_variance:,.2f} variance" if latest_period else "Variance analysis complete"
        analyst_status = "OK"
        analyst_issues = []
    else:
        analyst_summary = analysis_results.get("status", "Variance analysis unavailable")
        analyst_status = "ISSUES"
        analyst_issues = [analyst_summary]
    
    logger.set_summary("Analyst Agent", {
        "key_metric": analyst_summary,
        "status": analyst_status,
        "issues": analyst_issues
    })
    
    # Simulator
    simulator = SimulatorAgent()
    sim_results = simulator.run_scenarios(baseline_table)
    simulator.print_opportunity_register(sim_results)
    total_savings = sum(
        s.get("annual_impact", 0) for s in sim_results.get("scenarios", {}).values()
        if isinstance(s, dict)
    )
    
    logger.set_summary("Simulator Agent", {
        "key_metric": f"${total_savings:,.2f} potential savings",
        "status": "OK",
        "issues": []
    })
    
    # =========================================================================
    # SAVE OUTPUTS
    # =========================================================================
    print("\n" + "=" * 60)
    print("SAVING OUTPUTS...")
    print("=" * 60)
    
    # Save baseline
    v1_path = output_base / "baseline_v1_output.csv"
    baseline_table.to_csv(v1_path, index=False)
    # Also save to root for backward compatibility if needed, but prefer out/
    baseline_table.to_csv(base_dir / "baseline_v1_output.csv", index=False)
    print(f"  Baseline saved to: {v1_path}")
    
    # Save transactions
    transactions_df = pd.DataFrame([r.model_dump() for r in records])
    if 'date' in transactions_df.columns:
        transactions_df['date'] = transactions_df['date'].astype(str)
    trans_path = output_base / "baseline_transactions.csv"
    transactions_df.to_csv(trans_path, index=False)
    # Also save to root
    transactions_df.to_csv(base_dir / "baseline_transactions.csv", index=False)
    print(f"  Transactions saved to: {trans_path}")
    
    # Save Activity Log
    log_path = output_base / "AGENT_ACTIVITY_LOG.md"
    logger.save_report(log_path)
    print(f"  Activity log saved to: {log_path}")

    # Save Agent Audit Logs (JSON)
    audit_data = {
        'intake': intake.file_diagnostics,
        'schema': schema_audit_log,
        'standardizer': std_audit_log
    }
    
    audit_path = output_base / "audit_logs.json"
    with open(audit_path, 'w') as f:
        json.dump(audit_data, f, indent=2)
    print(f"  Agent audit logs saved to: {audit_path}")

    # Generate Manifest
    manifest = {
        "client": client_name,
        "timestamp": timestamp,
        "input_dir": str(data_dir),
        "files_processed": [os.path.basename(f) for f in files],
        "outputs": {
            "baseline": "baseline_v1_output.csv",
            "transactions": "baseline_transactions.csv",
            "activity_log": "AGENT_ACTIVITY_LOG.md",
            "audit_logs": "audit_logs.json"
        },
        "metrics": {
            "total_records": len(records),
            "total_spend": float(total_cost),
            "total_minutes": float(total_minutes)
        },
        "status": "COMPLETE"
    }
    manifest_path = output_base / "manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"  Manifest saved to: {manifest_path}")

    # Universal validation gate
    validator_script = base_dir / "scripts" / "validate_baseline.py"
    if validator_script.exists():
        validation_report = base_dir / "reports" / "baseline_validation_report.json"
        
        # Ensure reports dir exists
        validation_report.parent.mkdir(exist_ok=True)
        
        strict_validation = os.getenv("VALIDATION_STRICT", "").strip().lower() in {"1", "true", "yes", "on"}
        validation_cmd = [
            sys.executable,
            str(validator_script),
            "--baseline", str(v1_path),
            "--transactions", str(trans_path),
            "--output", str(validation_report)
        ]
        if strict_validation:
            validation_cmd.append("--strict")
        print("  Running universal baseline validation...")
        validation_proc = subprocess.run(validation_cmd, capture_output=True, text=True)
        if validation_proc.stdout:
            print(f"    {validation_proc.stdout.strip()}")
        if validation_proc.returncode != 0:
            if validation_proc.stderr:
                print(f"    Validation error: {validation_proc.stderr.strip()}")
            raise SystemExit("Pipeline failed validation check.")
        else:
            try:
                with open(validation_report, "r", encoding="utf-8") as f:
                    validation_data = json.load(f)
                if validation_data.get("status") != "PASS":
                    failed_checks = validation_data.get("summary", {}).get("failed_checks", [])
                    print(f"    Validation failed checks: {failed_checks}")
                    raise SystemExit("Pipeline failed validation check.")
            except Exception as e:
                raise SystemExit(f"Pipeline could not confirm validation status: {e}")
    else:
        print("  Validation script not found; skipping post-run validation.")
    
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
