
import sys
import os
import pandas as pd

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'multi_agent_system', 'src'))

from agents.intake_agent import IntakeAgent
from agents.schema_agent import SchemaAgent
from agents.standardizer_agent import StandardizerAgent
from agents.rate_card_agent import RateCardAgent
from agents.modality_agent import ModalityRefinementAgent
from agents.qa_agent import QAgent
from agents.aggregator_agent import AggregatorAgent

def process_single_file(file_path):
    """Process a single Excel or CSV file through the multi-agent pipeline."""
    
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found: {file_path}")
        return
    
    print(f"\n{'='*60}")
    print(f"🚀 Processing Single File: {os.path.basename(file_path)}")
    print(f"{'='*60}\n")
    
    # Get vendor name from filename
    vendor = os.path.basename(file_path).split(' ')[0].split('-')[0]
    
    # Initialize agents
    intake = IntakeAgent(os.path.dirname(file_path))
    schema_agent = SchemaAgent()
    standardizer = StandardizerAgent()
    rate_card = RateCardAgent()
    modality_agent = ModalityRefinementAgent()
    qa_agent = QAgent()
    aggregator = AggregatorAgent()
    
    records = []
    
    # 1. INTAKE - Load file
    print(f"[1/7] 📦 Intake Agent loading file...")
    sheets = intake.load_clean_sheet(file_path)
    print(f"  ✓ Loaded {len(sheets)} sheets")
    
    # 2. SCHEMA & STANDARDIZATION
    print(f"\n[2/7] 🗺️ Schema Agent + Standardizer processing...")
    for sheet_name, df in sheets.items():
        print(f"  > Sheet: '{sheet_name}' ({len(df)} rows)")
        
        # Schema detection
        cols = list(df.columns)
        mapping = schema_agent.infer_mapping(
            cols,
            df.iloc[0] if len(df) > 0 else None,
            vendor=vendor,
            df=df
        )
        conf = schema_agent.assess_mapping(df, mapping)
        confidence = conf["final_confidence"]
        source = schema_agent.get_last_source()
        ai_reason = schema_agent.get_last_ai_reasoning()

        print(f"    Confidence: {confidence:.1%} (field {conf['field_confidence']:.0%}, data {conf['data_confidence']:.0%}, source {source})")
        if ai_reason:
            print(f"    AI reasoning: {ai_reason}")
        
        min_final = schema_agent.min_final_confidence
        if confidence < min_final:
            print(f"    ⚠️ Skipped (low confidence)")
            continue
        
        schema_agent.confirm_mapping(
            source_columns=cols,
            mapping=mapping,
            vendor=vendor,
            data_confidence=conf["data_confidence"],
            field_confidence=conf["field_confidence"]
        )
        
        # Standardize
        new_records = standardizer.process_dataframe(df, mapping, file_path, vendor)
        print(f"    ✓ Extracted {len(new_records)} records")
        records.extend(new_records)
    
    print(f"\n  Total records extracted: {len(records)}")
    
    # 3. RATE CARD
    print(f"\n[3/7] 💰 Rate Card Agent imputing costs...")
    records, imp_stats = rate_card.batch_impute(records)
    print(f"  ✓ Imputed {imp_stats['imputed_count']} records (${imp_stats['imputed_total_cost']:,.2f})")
    
    # 4. MODALITY
    print(f"\n[4/7] 🏷️ Modality Agent classifying services...")
    m_stats = modality_agent.refine_records(records)
    print(f"  ✓ OPI: {m_stats['OPI']}, VRI: {m_stats['VRI']}, OnSite: {m_stats['OnSite']}")
    
    # 5. QA
    print(f"\n[5/7] 🛡️ QA Agent validating quality...")
    records, qa_stats = qa_agent.process_records(records)
    print(f"  ✓ Removed {qa_stats['duplicates_removed']} duplicates")
    print(f"  ✓ Flagged {qa_stats['outliers_flagged']} outliers")
    print(f"  ✓ Clean records: {len(records)}")
    
    # 6. AGGREGATION
    print(f"\n[6/7] 📊 Aggregator Agent creating baseline...")
    baseline_df = aggregator.create_baseline(records)
    print(f"  ✓ Created {len(baseline_df)} aggregated rows")
    
    # 7. EXPORT
    print(f"\n[7/7] 💾 Exporting results...")
    
    # Save transactions
    trans_df = pd.DataFrame([vars(r) for r in records])
    if 'date' in trans_df.columns:
        trans_df['date'] = trans_df['date'].astype(str)
    
    output_name = os.path.splitext(os.path.basename(file_path))[0]
    trans_path = f"{output_name}_transactions.csv"
    baseline_path = f"{output_name}_baseline.csv"
    
    trans_df.to_csv(trans_path, index=False)
    baseline_df.to_csv(baseline_path, index=False)
    
    print(f"  ✓ Saved transactions to: {trans_path}")
    print(f"  ✓ Saved baseline to: {baseline_path}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"✅ PROCESSING COMPLETE")
    print(f"{'='*60}")
    print(f"📊 Summary:")
    print(f"  • Total Spend: ${baseline_df['Cost'].sum():,.2f}")
    print(f"  • Total Minutes: {baseline_df['Minutes'].sum():,.0f}")
    print(f"  • Total Calls: {baseline_df['Calls'].sum():,.0f}")
    print(f"  • Avg CPM: ${baseline_df['Cost'].sum() / baseline_df['Minutes'].sum():.3f}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n📋 Usage: python process_single_file.py <path_to_file>")
        print("\nExample:")
        print('  python process_single_file.py "data_files/Language Services/Healthpoint-Q1-2024.xlsx"')
        print('  python process_single_file.py "data_files/Language Services/Peak Vista OPI.csv"')
        print()
    else:
        file_path = sys.argv[1]
        process_single_file(file_path)
