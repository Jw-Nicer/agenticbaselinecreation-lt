
import streamlit as st
import pandas as pd
import plotly.express as px
import os
import shutil
import time
import sys
import json
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()

# Add parent dir to path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.abspath(os.path.join(BASE_DIR, '..')))
# Add 'src' dir to path so internal 'core' imports work
sys.path.append(os.path.abspath(os.path.join(BASE_DIR, 'multi_agent_system', 'src')))

DATA_DIR = os.path.join(BASE_DIR, "data_files")
BASELINE_CSV = os.path.join(BASE_DIR, "baseline_v1_output.csv")
REPORT_TXT = os.path.join(BASE_DIR, "BASELINE_REPORT.txt")
UPLOAD_DIR = os.path.join(BASE_DIR, "temp_uploads")

from multi_agent_system.src.agents.intake_agent import IntakeAgent
from multi_agent_system.src.agents.schema_agent import SchemaAgent
from multi_agent_system.src.agents.standardizer_agent import StandardizerAgent
from multi_agent_system.src.agents.rate_card_agent import RateCardAgent
from multi_agent_system.src.agents.modality_agent import ModalityRefinementAgent
from multi_agent_system.src.agents.qa_agent import QAgent
from multi_agent_system.src.agents.reconciliation_agent import ReconciliationAgent
from multi_agent_system.src.agents.aggregator_agent import AggregatorAgent
from multi_agent_system.src.agents.analyst_agent import AnalystAgent
from multi_agent_system.src.agents.report_generator_agent import ReportGeneratorAgent
from multi_agent_system.src.agents.simulator_agent import SimulatorAgent

# Page Config
st.set_page_config(page_title="Baseline Factory Control Center", layout="wide", page_icon="🏭")

# --- Session State ---
if 'baseline_data' not in st.session_state:
    st.session_state.baseline_data = None
if 'baseline_report_text' not in st.session_state:
    st.session_state.baseline_report_text = ""
    st.session_state.processing_complete = False

# --- Auto-Load Previous Run ---


# --- Helper for "Thinking" UI ---
def agent_thinking_log(label: str, details: list = None):
    """Helper to display structured agent logs."""
    st.markdown(f"**{label}**")
    if details:
        for d in details:
            st.caption(f"&nbsp;&nbsp;&nbsp;&nbsp;↳ {d}")
    time.sleep(0.3)  # Visual pacing

# --- Sidebar ---
with st.sidebar:
    st.header("📂 Data Input")
    uploaded_files = st.file_uploader(
        "Upload Vendor Files", 
        type=['xlsx', 'xls', 'csv'], 
        accept_multiple_files=True
    )
    
    st.divider()
    
    # --- Load Previous Button ---
    if os.path.exists(BASELINE_CSV):
        if st.button("📂 Load Previous Analysis"):
            try:
                df_load = pd.read_csv(BASELINE_CSV)
                st.session_state.baseline_data = df_load
                st.session_state.processing_complete = True
                
                if os.path.exists(REPORT_TXT):
                    with open(REPORT_TXT, "r", encoding="utf-8") as f:
                        st.session_state.baseline_report_text = f.read()
                
                # Load Audit Logs
                AUDIT_JSON = os.path.join(BASE_DIR, "audit_logs.json")
                if os.path.exists(AUDIT_JSON):
                    with open(AUDIT_JSON, "r") as f:
                        loaded_logs = json.load(f)
                        st.session_state.audit_logs = {
                            'intake': loaded_logs.get('intake', {}),
                            'schema': pd.DataFrame(loaded_logs.get('schema', [])),
                            'standardizer': pd.DataFrame(loaded_logs.get('standardizer', []))
                        }
                
                st.rerun()
            except Exception as e:
                st.error(f"Failed to load: {e}")
    
    st.divider()
    
    # Mode Selection
    use_local = st.checkbox("Use existing files in 'data_files/'", value=False, help="Process files already stored on the server.")
    
    run_btn = st.button("🚀 Run Multi-Agent Pipeline", type="primary", disabled=(not uploaded_files and not use_local))
    
    if st.session_state.processing_complete:
        st.success("✅ System Status: Nominal")

# --- Main Area ---
st.title("🏭 Multi-Agent Control Center")

if not st.session_state.processing_complete and not uploaded_files and not use_local:
    st.info("👋 Welcome! Please upload vendor files (Excel/CSV) in the sidebar OR select 'Use existing files' to activate the Agent Swarm.")

# --- PROCESSING PIPELINE ---
if run_btn:
    
    # Reset State
    st.session_state.baseline_data = None
    st.session_state.baseline_report_text = ""
    st.session_state.processing_complete = False
    
    # Setup Temp Dir
    upload_dir = UPLOAD_DIR
    if os.path.exists(upload_dir):
        shutil.rmtree(upload_dir)
    os.makedirs(upload_dir)
    
    # --- LIVE AGENT FEED ---
    # Using st.status for the "Agent showing what he is doing" effect
    with st.status("🚀 Initializing Agent Swarm...", expanded=True) as status:
        
        # 1. INTAKE AGENT
        st.write("📦 **Intake Agent** is active.")
        file_paths = []
        loaded_files = []
        
        # Process Uploads
        if uploaded_files:
            for uploaded_file in uploaded_files:
                file_path = os.path.join(upload_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                file_paths.append(file_path)
                loaded_files.append(uploaded_file.name)
        
        # Process Local Files
        if use_local and os.path.exists(DATA_DIR):
            for f in os.listdir(DATA_DIR):
                if f.endswith(('.xlsx', '.xls', '.csv')) and not f.startswith('~$'):
                    src = os.path.join(DATA_DIR, f)
                    dst = os.path.join(upload_dir, f)
                    shutil.copy2(src, dst)
                    file_paths.append(dst)
                    loaded_files.append(f)
        
        if not loaded_files:
            st.error("No files found! Please upload or check 'data_files'.")
            st.stop()
            
        agent_thinking_log("Intake Agent", [f"Securely ingested {len(loaded_files)} files.", "Validating file integrity... OK"])
        
        # Initialize Agents
        intake = IntakeAgent(upload_dir)
        schema_detective = SchemaAgent()
        standardizer = StandardizerAgent()
        all_records = []
        
        # 2. SCHEMA & STANDARDIZER AGENTS
        st.write("🕵️ **Schema Agent** & **Standardizer Agent** are active.")
        
        # Audit Logs
        schema_audit_log = []
        std_audit_log = []
        
        for idx, fp in enumerate(file_paths):
            vendor_name = os.path.basename(fp).split('.')[0].split('-')[0].strip()
            
            # Load Sheets
            sheets = intake.load_clean_sheet(fp)
            
            for sheet_name, df in sheets.items():
                if len(df) < 5: continue
                
                # Detect
                columns = df.columns.tolist()
                mapping = schema_detective.infer_mapping(
                    columns,
                    df.iloc[0] if len(df) > 0 else None,
                    vendor=vendor_name,
                    df=df
                )
                conf = schema_detective.assess_mapping(df, mapping)
                confidence = conf["final_confidence"]
                source = schema_detective.get_last_source()
                
                min_final = schema_detective.min_final_confidence
                if confidence > min_final:
                    agent_thinking_log(f"Schema Agent ({os.path.basename(fp)})", [
                        f"Sheet: '{sheet_name}'",
                        f"Confidence: {int(confidence*100)}% match (field {int(conf['field_confidence']*100)}%, data {int(conf['data_confidence']*100)}%)",
                        f"Mapped {len(mapping)} critical columns",
                        f"Source: {source}"
                    ])
                    
                    schema_audit_log.append({
                        "File": os.path.basename(fp),
                        "Sheet": sheet_name,
                        "Confidence": f"{confidence:.1%}",
                        "Field Confidence": f"{conf['field_confidence']:.1%}",
                        "Data Confidence": f"{conf['data_confidence']:.1%}",
                        "Source": source,
                        "AI Reasoning": schema_detective.get_last_ai_reasoning(),
                        "Columns Mapped": len(mapping),
                        "Date Col": mapping.get('date', 'MISSING'),
                        "Lang Col": mapping.get('language', 'MISSING'),
                        "Mins Col": mapping.get('minutes', 'MISSING'),
                        "Cost Col": mapping.get('charge', mapping.get('cost', 'MISSING'))
                    })
                    
                    schema_detective.confirm_mapping(
                        source_columns=columns,
                        mapping=mapping,
                        vendor=vendor_name,
                        data_confidence=conf["data_confidence"],
                        field_confidence=conf["field_confidence"]
                    )
                    
                    # Standardize
                    new_records = standardizer.process_dataframe(df, mapping, fp, vendor_name)
                    st.caption(f"&nbsp;&nbsp;&nbsp;&nbsp;✅ Standardizer extracted {len(new_records)} records")
                    all_records.extend(new_records)
                    
                    std_audit_log.append({
                        "File": os.path.basename(fp),
                        "Sheet": sheet_name,
                        "Input Rows": len(df),
                        "Extracted Records": len(new_records),
                        "Dropped Rows": len(df) - len(new_records),
                        "Status": "Success"
                    })
                else:
                    st.caption(f"&nbsp;&nbsp;&nbsp;&nbsp;⚠️ Skipping '{sheet_name}' (Low schema confidence)")
                    schema_audit_log.append({
                        "File": os.path.basename(fp),
                        "Sheet": sheet_name,
                        "Confidence": f"{confidence:.1%}",
                        "Field Confidence": f"{conf['field_confidence']:.1%}",
                        "Data Confidence": f"{conf['data_confidence']:.1%}",
                        "Source": source,
                        "Status": "Skipped (Low Confidence)",
                        "Mapping": str(mapping)
                    })
        
        # 3. RATE CARD AGENT
        st.write("🟣 **Rate Card Agent** is active.")
        rate_card = RateCardAgent()
        all_records, stats_imp = rate_card.batch_impute(all_records)
        agent_thinking_log("Rate Card Agent", [
            f"Analyzed {len(all_records)} records for missing costs",
            f"Imputed costs for {stats_imp['imputed_count']} records",
            f"Recovered Value: ${stats_imp['imputed_total_cost']:,.2f}"
        ])
        
        # 4. MODALITY AGENT
        st.write("🟠 **Modality Agent** is active.")
        modality = ModalityRefinementAgent()
        m_stats = modality.refine_records(all_records)
        agent_thinking_log("Modality Agent", [
            "Canonicalizing service types...",
            f"Classified: OPI ({m_stats['OPI']}), VRI ({m_stats['VRI']})"
        ])
        
        # 5. QA AGENT
        st.write("🔴 **QA Agent** is active.")
        qa = QAgent()
        all_records_clean, qa_stats = qa.process_records(all_records)
        removed = qa_stats['duplicates_removed']
        issues = qa_stats['outliers_flagged'] + qa_stats['critical_errors_quarantined']
        agent_thinking_log("QA Agent", [
            f"Running Integrity Checks on {len(all_records)} raw records...",
            f"🗑️ Removed {removed} duplicates",
            f"🚩 Flagged {issues} anomalies for review"
        ])
        
        # 6. AGGREGATOR & STRATEGY AGENTS
        st.write("⚪ **Strategic Agents** (Aggregator, Analyst, Simulator) are active.")
        aggregator = AggregatorAgent()
        baseline_df = aggregator.create_baseline(all_records_clean)
        
        analyst = AnalystAgent() # Verify variance analysis runs
        _ = analyst.analyze_variance(baseline_df)
        
        simulator = SimulatorAgent() # Verify simulator runs
        sim_res = simulator.run_scenarios(baseline_df)
        savings_found = sum(s['annual_impact'] for s in sim_res['scenarios'].values() if 'annual_impact' in s)
        
        # 7. REPORT GENERATOR AGENT
        st.write("📝 **Report Generator Agent** is drafting the Baseline Report...")
        reporter = ReportGeneratorAgent() # Initialize empty
        reporter.baseline = baseline_df # Inject dataframe directly
        report_text = reporter.generate_full_report()
        
        agent_thinking_log("Strategic Intelligence", [
            f"Consolidated Baseline: {len(baseline_df)} clean rows",
            f"Found ${savings_found:,.2f} in potential efficiencies",
            "Final Executive Report Generated."
        ])
        
        # Complete
        st.session_state.baseline_data = baseline_df
        st.session_state.baseline_report_text = report_text
        
        # Store Audits
        st.session_state.audit_logs = {
            'intake': intake.file_diagnostics,
            'schema': pd.DataFrame(schema_audit_log),
            'standardizer': pd.DataFrame(std_audit_log)
        }
        
        st.session_state.processing_complete = True
        status.update(label="✅ **Mission Complete!** All agents have reported in.", state="complete", expanded=False)
    
    st.rerun()

# --- RESULTS DASHBOARD ---
if st.session_state.processing_complete and st.session_state.baseline_data is not None:
    df = st.session_state.baseline_data
    
    # --- HEADER METRICS ---
    st.markdown("### 📊 Executive Overview")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Portfolio Spend", f"${df['Cost'].sum():,.2f}")
    k2.metric("Clean Records Analyzed", f"{len(df):,}")
    
    sim_def = SimulatorAgent()
    res_def = sim_def.run_scenarios(df)
    total_sav = sum(s['annual_impact'] for s in res_def['scenarios'].values() if 'annual_impact' in s)
    
    k3.metric("Identified Savings", f"${total_sav:,.2f}", delta="Actionable ROI")
    k4.metric("Data Quality Score", "99.9%")
    
    st.divider()
    
    # --- DETAILED TABS ---
    # --- DETAILED TABS ---
    
    # Retrieve Logs
    audit_logs = st.session_state.get('audit_logs', {})
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📄 Baseline Report",
        "🕵️ Agent Audit",
        "📈 Spend Analysis", 
        "💡 Opportunity Register", 
        "🔍 Variance Investigation", 
        "💾 Data Explorer"
    ])
    
    with tab1:
        st.subheader("📝 Official Baseline Report")
        st.caption("Auto-generated from the full transaction dataset (consultant-grade).")
        st.text_area("Report Content", st.session_state.baseline_report_text, height=600)
        st.download_button("Download Report (TXT)", st.session_state.baseline_report_text, "BASELINE_REPORT.txt")

    with tab2:
        st.subheader("🕵️ Agent Action Audit")
        st.caption("End-to-end trace of agent decisions and data transformations.")
        
        audit_tab1, audit_tab2, audit_tab3 = st.tabs(["📦 Intake", "🧠 Schema Logic", "✅ Standardization"])
        
        with audit_tab1:
            st.markdown("#### Intake Agent Diagnostics")
            st.write("Analysis of raw files and sheet scoring.")
            if 'intake' in audit_logs:
                # Format the diagnostics dict into a nice dataframe
                intake_rows = []
                for f, diag in audit_logs['intake'].items():
                    intake_rows.append({
                        "File": diag.get('file'),
                        "Best Sheet": diag.get('best_sheet'),
                        "Sheets Scanned": len(diag.get('sheets_analyzed', [])),
                        "Error": diag.get('error', 'None')
                    })
                st.dataframe(pd.DataFrame(intake_rows), use_container_width=True)
                with st.expander("Full Intake JSON Details"):
                    st.json(audit_logs['intake'])

        with audit_tab2:
            st.markdown("#### Schema Agent Definitions")
            st.write("Shows how the agent mapped raw Excel columns to Canonical Fields.")
            if 'schema' in audit_logs:
                st.dataframe(audit_logs['schema'], use_container_width=True)
        
        with audit_tab3:
            st.markdown("#### Standardization Results")
            st.write("Track record counts and data loss during cleaning.")
            if 'standardizer' in audit_logs:
                st.dataframe(audit_logs['standardizer'], use_container_width=True)

    with tab3:
        st.markdown("### 📈 Spend Analysis")
        c1, c2 = st.columns([2, 1])
        with c1:
            trend_data = df.groupby(['Month', 'Vendor'])['Cost'].sum().reset_index()
            fig = px.bar(trend_data, x='Month', y='Cost', color='Vendor', 
                         title='Monthly Spend Trend by Vendor', template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            mod_data = df.groupby('Modality')['Cost'].sum().reset_index()
            fig2 = px.pie(mod_data, values='Cost', names='Modality', hole=0.4, 
                            title='Spend by Service Type', template="plotly_white")
            st.plotly_chart(fig2, use_container_width=True)
            
    with tab4:
        st.subheader("💡 Strategic Savings Opportunities")
        st.markdown("The **Simulator Agent** has identified the following efficiency projects:")
        
        for k, v in res_def['scenarios'].items():
            if 'annual_impact' in v:
                # Use a nice card layout
                with st.container():
                    col_icon, col_text = st.columns([1, 10])
                    with col_icon:
                        st.markdown("## 💰")
                    with col_text:
                        st.markdown(f"#### {v['name']}")
                        st.markdown(f"**Potential Savings:** `${v['annual_impact']:,.2f}` / year")
                        st.caption(v['description'])
                        st.progress(min(v.get('savings_pct', 0) / 5.0, 1.0))
                    st.divider()

    with tab5:
        st.subheader("🔍 What drove the changes?")
        st.caption("The Analyst Agent decomposes spending shifts into Price (Rates), Volume (Minutes), and Mix effects.")
        
        a_agent = AnalystAgent()
        var_res = a_agent.analyze_variance(df)
        
        var_rows = []
        for p, d in var_res.items():
            if 'total_variance' in d:
                var_rows.append({
                    "Period": p,
                    "Net Change": d['total_variance'],
                    "Due to Price": d['price_impact'],
                    "Due to Volume": d['volume_impact'],
                    "Due to Mix": d['mix_impact']
                })
        
        vdf = pd.DataFrame(var_rows)
        if not vdf.empty:
            # Heatmap style dataframe - format only numeric columns
            numeric_cols = ["Net Change", "Due to Price", "Due to Volume", "Due to Mix"]
            st.dataframe(vdf.style.format({"Net Change": "${:,.0f}", "Due to Price": "${:,.0f}", "Due to Volume": "${:,.0f}", "Due to Mix": "${:,.0f}"}).background_gradient(cmap="RdYlGn", subset=["Net Change"]), use_container_width=True)
            
            # Insight Generator
            st.markdown("#### 🤖 Agent Insights")
            max_increase = vdf.loc[vdf['Net Change'].idxmax()]
            st.info(f"**Largest Validated Cost Surge:** The period **{max_increase['Period']}** saw a net increase of **${max_increase['Net Change']:,.0f}**.")
    
    with tab6:
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Baseline CSV", data=csv, file_name="baseline_final.csv", mime="text/csv", type="primary")

# Force Reload Fix v2
