
import os
import sys
import pandas as pd

# Ensure src is in path
current_dir = os.getcwd()
src_path = os.path.join(current_dir, 'multi_agent_system', 'src')
if os.path.exists(src_path):
    sys.path.append(src_path)
else:
    sys.path.append(os.path.join(current_dir, 'src'))

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

def main():
    base_dir = r"c:\Users\John\.gemini\antigravity\playground\multiagent-baseline-lt"
    data_dir = os.path.join(base_dir, "data_files", "Language Services")
    
    # Initialize activity logger
    logger = reset_logger()
    
    print("=" * 60)
    print("BASELINE FACTORY - MULTI-AGENT SYSTEM")
    print("=" * 60)
    
    # =========================================================================
    # AGENT 1: INTAKE
    # =========================================================================
    print("\n[1/7] INTAKE AGENT - Scanning for files...")
    logger.log("Intake Agent", "Started scanning", {"directory": data_dir})
    
    intake = IntakeAgent(data_dir)
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
    
    # =========================================================================
    # AGENT 2 & 3: SCHEMA + STANDARDIZER (per file)
    # =========================================================================
    print("\n[2/7] SCHEMA AGENT - Mapping columns...")
    print("[3/7] STANDARDIZER AGENT - Extracting records...")
    
    for filepath in files:
        filename = os.path.basename(filepath)
        vendor = filename.split(" ")[0].split("-")[0].replace("_", "")
        
        logger.log("Schema Agent", f"Processing file", {"file": filename, "vendor": vendor})
        
        sheets = intake.load_clean_sheet(filepath)
        reconciler.extract_totals_from_sheets(sheets, vendor)
        
        for sheet_name, df in sheets.items():
            cols = list(df.columns)
            mapping = schema_detective.infer_mapping(cols)
            score = schema_detective.validate_mapping(mapping)
            
            logger.log("Schema Agent", "Column mapping", {
                "sheet": sheet_name,
                "confidence": f"{score:.0%}",
                "mapped_fields": list(mapping.keys())
            })
            
            if score < 0.5:
                logger.log("Schema Agent", "SKIPPED - Low confidence", {"sheet": sheet_name})
                files_with_issues.append(f"{filename}/{sheet_name}: Low mapping confidence ({score:.0%})")
                continue
            
            # Standardize
            new_records = standardizer.process_dataframe(df, mapping, filename, vendor)
            
            logger.log("Standardizer Agent", "Records extracted", {
                "file": filename,
                "sheet": sheet_name,
                "records": len(new_records)
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
    print(f"\n[4/7] RATE CARD AGENT - Validating costs...")
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
    print(f"\n[5/7] MODALITY AGENT - Refining service types...")
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
        "status": "OK" if m_stats['Unknown'] == 0 else "OK",
        "issues": modality_issues
    })
    
    # =========================================================================
    # AGENT 6: QA
    # =========================================================================
    print(f"\n[6/7] QA AGENT - Finding duplicates and outliers...")
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
    # AGENT 7: AGGREGATOR
    # =========================================================================
    print(f"\n[7/7] AGGREGATOR AGENT - Creating baseline...")
    logger.log("Aggregator Agent", "Started aggregation", {"input_records": len(records)})
    
    aggregator = AggregatorAgent()
    baseline_table = aggregator.create_baseline(records)
    
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
    
    logger.set_summary("Aggregator Agent", {
        "key_metric": f"${total_cost:,.2f} total spend",
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
    v1_path = os.path.join(base_dir, "baseline_v1_output.csv")
    baseline_table.to_csv(v1_path, index=False)
    print(f"  Baseline saved to: baseline_v1_output.csv")
    
    # Save transactions
    transactions_df = pd.DataFrame([vars(r) for r in records])
    if 'date' in transactions_df.columns:
        transactions_df['date'] = transactions_df['date'].astype(str)
    trans_path = os.path.join(base_dir, "baseline_transactions.csv")
    transactions_df.to_csv(trans_path, index=False)
    print(f"  Transactions saved to: baseline_transactions.csv")
    
    # Save Activity Log
    log_path = os.path.join(base_dir, "AGENT_ACTIVITY_LOG.md")
    logger.save_report(log_path)
    print(f"  Activity log saved to: AGENT_ACTIVITY_LOG.md")
    
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
