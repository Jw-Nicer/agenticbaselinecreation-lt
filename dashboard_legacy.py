
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import shutil
import io
import time
import sys
import json
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()

# Add parent dir to path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.abspath(os.path.join(BASE_DIR, '..')))
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
from core.memory_store import load_json, save_json
from multi_agent_system.src.core.activity_logger_enhanced import (
    EnhancedActivityLogger, Finding, AgentMessage, ImpactMetric
)

# ============================================================================
# AGENT PERSONA DEFINITIONS - Making agents feel like real team members
# ============================================================================

@dataclass
class AgentPersona:
    name: str
    role: str
    avatar: str
    color: str
    expertise: str

AGENT_PERSONAS = {
    "intake": AgentPersona("DataBot", "Data Intake Specialist", "📦", "#3498db", "File parsing & validation"),
    "schema": AgentPersona("SchemaDetective", "Schema Mapping Expert", "🕵️", "#9b59b6", "Column recognition & AI mapping"),
    "standardizer": AgentPersona("Transformer", "Data Standardization Engineer", "⚙️", "#1abc9c", "Record normalization"),
    "rate_card": AgentPersona("CostAnalyst", "Rate Card Specialist", "💵", "#f39c12", "Cost imputation & validation"),
    "modality": AgentPersona("ServiceClassifier", "Modality Expert", "🎯", "#e74c3c", "Service type classification"),
    "qa": AgentPersona("QualityGuard", "Quality Assurance Lead", "🛡️", "#2ecc71", "Data integrity & outlier detection"),
    "reconciliation": AgentPersona("Reconciler", "Financial Reconciliation Agent", "⚖️", "#34495e", "Invoice matching"),
    "aggregator": AgentPersona("Consolidator", "Aggregation Specialist", "📊", "#16a085", "Data consolidation"),
    "analyst": AgentPersona("InsightEngine", "Variance Analyst", "📈", "#8e44ad", "Price-Volume-Mix analysis"),
    "simulator": AgentPersona("OpportunityFinder", "Savings Simulator", "💡", "#27ae60", "ROI identification"),
    "reporter": AgentPersona("ReportWriter", "Executive Report Generator", "📝", "#2980b9", "Consultant-grade reporting"),
}

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Baseline Factory | Agent Control Center",
    layout="wide",
    page_icon="🏭",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS FOR PROFESSIONAL STYLING
# ============================================================================

st.markdown("""
<style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        max-width: 1400px;
    }

    /* Agent message bubbles */
    .agent-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 15px 20px;
        margin: 10px 0;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }

    .agent-message-light {
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        border-radius: 0 10px 10px 0;
        padding: 12px 18px;
        margin: 8px 0;
        color: #333;
    }

    /* Agent avatar styling */
    .agent-avatar {
        font-size: 2rem;
        margin-right: 10px;
    }

    /* Finding reference styling */
    .finding-ref {
        background: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 5px;
        padding: 3px 8px;
        font-family: monospace;
        font-size: 0.85em;
        color: #856404;
    }

    /* Impact indicator cards */
    .impact-positive {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border-left: 4px solid #28a745;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }

    .impact-negative {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border-left: 4px solid #dc3545;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }

    .impact-neutral {
        background: linear-gradient(135deg, #e2e3e5 0%, #d6d8db 100%);
        border-left: 4px solid #6c757d;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }

    /* Progress stage indicators */
    .stage-active {
        background: #007bff;
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: bold;
    }

    .stage-complete {
        background: #28a745;
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
    }

    .stage-pending {
        background: #e9ecef;
        color: #6c757d;
        padding: 8px 16px;
        border-radius: 20px;
    }

    /* Metric cards */
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        text-align: center;
    }

    /* Chat-like agent communication */
    .agent-chat {
        max-height: 500px;
        overflow-y: auto;
        padding: 15px;
        background: #f8f9fa;
        border-radius: 10px;
        border: 1px solid #dee2e6;
    }

    /* Timeline styling */
    .timeline-item {
        border-left: 3px solid #007bff;
        padding-left: 20px;
        margin-left: 10px;
        padding-bottom: 20px;
    }

    .timeline-item:last-child {
        border-left: 3px solid transparent;
    }

    /* Agent conversation table badges */
    .conv-badge-pass { background: #28a745; color: white; padding: 2px 10px; border-radius: 12px; font-size: 0.8em; font-weight: bold; }
    .conv-badge-flag { background: #ffc107; color: #333; padding: 2px 10px; border-radius: 12px; font-size: 0.8em; font-weight: bold; }
    .conv-badge-skip { background: #dc3545; color: white; padding: 2px 10px; border-radius: 12px; font-size: 0.8em; font-weight: bold; }

    /* Agent status board cards */
    .agent-card {
        background: white; border-radius: 12px; padding: 15px; margin: 5px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08); text-align: center;
        transition: transform 0.2s;
    }
    .agent-card:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0,0,0,0.15); }

    /* Reconciliation styling */
    .recon-match { background: #d4edda; border-left: 4px solid #28a745; border-radius: 8px; padding: 15px; margin: 10px 0; }
    .recon-alert { background: #f8d7da; border-left: 4px solid #dc3545; border-radius: 8px; padding: 15px; margin: 10px 0; }

    /* Sign-off section */
    .signoff-section { background: #f8f9fa; border: 2px solid #dee2e6; border-radius: 10px; padding: 20px; margin: 15px 0; }

    /* Pulse animation for active agents */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    .agent-status-working { animation: pulse 1.5s infinite; }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'baseline_data' not in st.session_state:
    st.session_state.baseline_data = None
if 'baseline_report_text' not in st.session_state:
    st.session_state.baseline_report_text = ""
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'agent_communications' not in st.session_state:
    st.session_state.agent_communications = []
if 'pipeline_progress' not in st.session_state:
    st.session_state.pipeline_progress = 0
if 'findings_log' not in st.session_state:
    st.session_state.findings_log = []
if 'impact_metrics' not in st.session_state:
    st.session_state.impact_metrics = {}
if 'pipeline_summary' not in st.session_state:
    st.session_state.pipeline_summary = {}
if 'enhanced_logger' not in st.session_state:
    st.session_state.enhanced_logger = EnhancedActivityLogger()
if 'recon_results' not in st.session_state:
    st.session_state.recon_results = {}
if 'signoff_data' not in st.session_state:
    st.session_state.signoff_data = {"reviewer": "", "status": "Pending", "notes": "", "date": None}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def add_agent_message(agent_key: str, message: str, message_type: str = "status",
                     findings: List[Dict] = None, to_agent: str = None):
    """Add a message from an agent to the communication log."""
    persona = AGENT_PERSONAS.get(agent_key)
    entry = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "agent_key": agent_key,
        "agent_name": persona.name if persona else agent_key,
        "avatar": persona.avatar if persona else "🤖",
        "color": persona.color if persona else "#666",
        "message": message,
        "type": message_type,  # status, finding, handoff, alert, success
        "findings": findings or [],
        "to_agent": to_agent
    }
    st.session_state.agent_communications.append(entry)

def add_finding(agent_key: str, finding_type: str, description: str,
                reference: str, impact: str, severity: str = "info"):
    """Add a finding with exact reference."""
    entry = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "agent": AGENT_PERSONAS[agent_key].name if agent_key in AGENT_PERSONAS else agent_key,
        "type": finding_type,
        "description": description,
        "reference": reference,  # e.g., "Healthpoint.xlsx:Sheet1:Row45:ColB"
        "impact": impact,
        "severity": severity  # info, warning, critical, success
    }
    st.session_state.findings_log.append(entry)

def update_impact_metric(metric_name: str, value: Any, delta: Any = None,
                        direction: str = "neutral"):
    """Track impact metrics for baseline creation."""
    st.session_state.impact_metrics[metric_name] = {
        "value": value,
        "delta": delta,
        "direction": direction  # positive, negative, neutral
    }

def render_agent_message(msg: Dict, container, display_name: Optional[str] = None):
    """Render a single agent message in chat format."""
    with container:
        name_text = display_name or msg["agent_name"]
        # Determine message styling based on type
        if msg["type"] == "handoff":
            icon = "🤝"
            bg_color = "#e3f2fd"
        elif msg["type"] == "alert":
            icon = "⚠️"
            bg_color = "#fff3cd"
        elif msg["type"] == "success":
            icon = "✅"
            bg_color = "#d4edda"
        elif msg["type"] == "finding":
            icon = "🔍"
            bg_color = "#f8d7da"
        else:
            icon = ""
            bg_color = "#f8f9fa"

        # Build message HTML
        to_text = f" → <strong>{AGENT_PERSONAS[msg['to_agent']].name}</strong>" if msg.get('to_agent') else ""

        st.markdown(f"""
        <div style="background: {bg_color}; border-left: 4px solid {msg['color']};
                    border-radius: 0 10px 10px 0; padding: 12px 18px; margin: 8px 0;">
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 1.5rem; margin-right: 10px;">{msg['avatar']}</span>
                <strong style="color: {msg['color']};">{name_text}</strong>
                <span style="color: #999; margin-left: 10px; font-size: 0.8em;">{msg['timestamp']}</span>
                {to_text}
            </div>
            <div style="margin-left: 40px;">
                {icon} {msg['message']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Render findings if any
        if msg.get("findings"):
            for f in msg["findings"]:
                st.markdown(f"""
                <div style="margin-left: 60px; background: #fff3cd; border: 1px solid #ffc107;
                            border-radius: 5px; padding: 8px 12px; margin: 5px 0; font-size: 0.9em;">
                    <strong>📍 Reference:</strong> <code>{f.get('reference', 'N/A')}</code><br>
                    <strong>Finding:</strong> {f.get('description', '')}<br>
                    <strong>Impact:</strong> {f.get('impact', '')}
                </div>
                """, unsafe_allow_html=True)

def render_progress_pipeline(current_stage: int, stages: List[str]):
    """Render a visual pipeline progress indicator."""
    cols = st.columns(len(stages))
    for i, (col, stage) in enumerate(zip(cols, stages)):
        with col:
            if i < current_stage:
                st.markdown(f"""
                <div style="text-align: center;">
                    <div style="background: #28a745; color: white; padding: 8px;
                                border-radius: 50%; width: 40px; height: 40px;
                                margin: 0 auto; line-height: 24px;">✓</div>
                    <div style="font-size: 0.8em; margin-top: 5px; color: #28a745;">{stage}</div>
                </div>
                """, unsafe_allow_html=True)
            elif i == current_stage:
                st.markdown(f"""
                <div style="text-align: center;">
                    <div style="background: #007bff; color: white; padding: 8px;
                                border-radius: 50%; width: 40px; height: 40px;
                                margin: 0 auto; line-height: 24px; animation: pulse 1s infinite;">●</div>
                    <div style="font-size: 0.8em; margin-top: 5px; color: #007bff; font-weight: bold;">{stage}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="text-align: center;">
                    <div style="background: #e9ecef; color: #6c757d; padding: 8px;
                                border-radius: 50%; width: 40px; height: 40px;
                                margin: 0 auto; line-height: 24px;">○</div>
                    <div style="font-size: 0.8em; margin-top: 5px; color: #6c757d;">{stage}</div>
                </div>
                """, unsafe_allow_html=True)

def render_consultant_stage(title: str, what: str, result_lines: List[str],
                            confidence: str, next_step: Optional[str] = None,
                            status: str = "good"):
    """Render a plain-English consultant stage card."""
    colors = {
        "good": ("#d4edda", "#28a745"),
        "warn": ("#fff3cd", "#ffc107"),
        "bad": ("#f8d7da", "#dc3545")
    }
    bg_color, border_color = colors.get(status, ("#e2e3e5", "#6c757d"))
    results_html = "<br>".join(result_lines) if result_lines else "N/A"
    next_text = next_step if next_step else "No action needed."

    st.markdown(f"""
    <div style="background: {bg_color}; border-left: 5px solid {border_color};
                border-radius: 10px; padding: 16px; margin: 10px 0;">
        <div style="font-weight: bold; font-size: 1.05em; margin-bottom: 6px;">{title}</div>
        <div style="margin: 6px 0;"><strong>What we did:</strong> {what}</div>
        <div style="margin: 6px 0;"><strong>Result:</strong> {results_html}</div>
        <div style="margin: 6px 0;"><strong>Confidence:</strong> {confidence}</div>
        <div style="margin: 6px 0;"><strong>What happens next:</strong> {next_text}</div>
    </div>
    """, unsafe_allow_html=True)

def create_impact_gauge(value: float, title: str, max_val: float = 100):
    """Create a gauge chart for impact visualization."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'size': 14}},
        gauge={
            'axis': {'range': [0, max_val]},
            'bar': {'color': "#007bff"},
            'steps': [
                {'range': [0, max_val*0.33], 'color': "#f8d7da"},
                {'range': [max_val*0.33, max_val*0.66], 'color': "#fff3cd"},
                {'range': [max_val*0.66, max_val], 'color': "#d4edda"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 2},
                'thickness': 0.75,
                'value': max_val * 0.9
            }
        }
    ))
    fig.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=20))
    return fig

def build_client_summary_text(story: Dict[str, str], metrics: Dict[str, Any], actions: List[str]) -> str:
    lines = [
        "Baseline Factory - Client Summary",
        f"Date: {datetime.now().strftime('%Y-%m-%d')}",
        "",
        "Story Summary",
        f"- What changed: {story.get('what_changed', 'N/A')}",
        f"- Where the spend is: {story.get('where_spend', 'N/A')}",
        f"- What needs attention: {', '.join(actions) if actions else 'No action needed.'}",
        "",
        "Key Metrics",
        f"- Files processed: {metrics.get('files_processed', 'N/A')}",
        f"- Clean records: {metrics.get('records_clean', 'N/A')}",
        f"- Total spend: {metrics.get('total_spend', 'N/A')}",
        f"- Savings identified: {metrics.get('savings_found', 'N/A')}",
        f"- Data quality score: {metrics.get('quality_score', 'N/A')}",
        f"- Cost coverage: {metrics.get('cost_coverage', 'N/A')}",
        f"- Baseline rows: {metrics.get('baseline_rows', 'N/A')}"
    ]
    return "\n".join(lines)

def build_client_summary_pdf_bytes(summary_text: str) -> bytes:
    try:
        from reportlab.lib.pagesizes import LETTER
        from reportlab.pdfgen import canvas
    except Exception:
        return b""

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    width, height = LETTER
    x = 40
    y = height - 50
    for line in summary_text.splitlines():
        c.drawString(x, y, line)
        y -= 14
        if y < 40:
            c.showPage()
            y = height - 50
    c.save()
    buffer.seek(0)
    return buffer.read()

# ============================================================================
# NEW RENDERING FUNCTIONS - Agent Team Room, Financial Director, Audit Trail
# ============================================================================

def render_agent_status_board(logger: EnhancedActivityLogger):
    """Visual grid of agent cards showing current status."""
    agent_states = {}
    for key in AGENT_PERSONAS:
        agent_states[key] = {"status": "idle", "last_message": None, "exchanges": 0, "flags": 0}

    for msg in logger.messages:
        if msg.agent in agent_states:
            agent_states[msg.agent]["status"] = "complete"
            agent_states[msg.agent]["last_message"] = msg.message
            agent_states[msg.agent]["exchanges"] += 1
            if msg.status_badge == "FLAG":
                agent_states[msg.agent]["flags"] += 1

    agent_items = list(AGENT_PERSONAS.items())
    for row_start in range(0, len(agent_items), 4):
        row_items = agent_items[row_start:row_start + 4]
        cols = st.columns(len(row_items))
        for col, (key, persona) in zip(cols, row_items):
            state = agent_states[key]
            status_colors = {"idle": "#e9ecef", "working": "#007bff", "complete": "#28a745", "flagged": "#ffc107"}
            bg = status_colors.get(state["status"], "#e9ecef")
            flag_html = f'<span style="background:#dc3545;color:white;border-radius:50%;padding:2px 6px;font-size:0.7em;margin-left:5px;">{state["flags"]}</span>' if state["flags"] > 0 else ""
            with col:
                st.markdown(f"""
                <div style="background:white;border-radius:12px;padding:15px;margin:5px 0;
                            box-shadow:0 2px 8px rgba(0,0,0,0.1);border-top:4px solid {persona.color};text-align:center;min-height:160px;">
                    <div style="font-size:2rem;">{persona.avatar}</div>
                    <div style="font-weight:bold;color:{persona.color};font-size:0.95em;">{persona.name}{flag_html}</div>
                    <div style="font-size:0.75em;color:#666;">{persona.role}</div>
                    <div style="margin-top:8px;">
                        <span style="background:{bg};color:white;padding:3px 10px;border-radius:10px;font-size:0.75em;">
                            {state['status'].upper()}
                        </span>
                    </div>
                    <div style="font-size:0.7em;color:#999;margin-top:5px;">{state['exchanges']} exchanges</div>
                </div>
                """, unsafe_allow_html=True)


def _format_data_summary(data: dict) -> str:
    """Format data_passed dict into a short summary string."""
    if not data:
        return "-"
    parts = []
    for k, v in data.items():
        if isinstance(v, float):
            if abs(v) >= 1000:
                parts.append(f"{k}: ${v:,.0f}" if "cost" in k.lower() or "spend" in k.lower() or "dollar" in k.lower() or "charge" in k.lower() or "variance" in k.lower() or "savings" in k.lower() else f"{k}: {v:,.0f}")
            else:
                parts.append(f"{k}: {v:.2f}")
        elif isinstance(v, int):
            parts.append(f"{k}: {v:,}")
        else:
            parts.append(f"{k}: {v}")
    return " | ".join(parts)


def render_conversation_table(logger: EnhancedActivityLogger):
    """Render the structured agent conversation table."""
    if not logger.messages:
        st.info("Run the pipeline to see agent conversations.")
        return

    rows = []
    for msg in logger.messages:
        from_persona = AGENT_PERSONAS.get(msg.agent)
        to_persona = AGENT_PERSONAS.get(msg.to_agent) if msg.to_agent else None

        rows.append({
            "Time": msg.timestamp.split("T")[1][:8] if "T" in msg.timestamp else msg.timestamp,
            "From": f"{from_persona.avatar} {from_persona.name}" if from_persona else msg.agent,
            "To": f"{to_persona.avatar} {to_persona.name}" if to_persona else "Team",
            "Message": msg.message[:120],
            "Data Passed": _format_data_summary(msg.data_passed),
            "Decision": msg.decision or "-",
            "Status": msg.status_badge,
            "Confidence": f"{msg.confidence:.0%}" if msg.confidence is not None else "-",
            "$ Impact": f"${msg.dollar_impact:,.2f}" if msg.dollar_impact is not None else "-"
        })

    conv_df = pd.DataFrame(rows)

    def color_status(val):
        colors = {"PASS": "background-color: #28a745; color: white;",
                  "FLAG": "background-color: #ffc107; color: #333;",
                  "SKIP": "background-color: #dc3545; color: white;"}
        return colors.get(val, "")

    styled = conv_df.style.applymap(color_status, subset=["Status"])
    st.dataframe(styled, use_container_width=True, height=450)


def render_agent_flow_sankey(logger: EnhancedActivityLogger):
    """Plotly Sankey diagram showing agent-to-agent data flow."""
    agent_keys = list(AGENT_PERSONAS.keys())
    agent_labels = [f"{p.avatar} {p.name}" for p in AGENT_PERSONAS.values()]
    agent_colors = [p.color for p in AGENT_PERSONAS.values()]

    sources, targets, values, link_labels = [], [], [], []

    for msg in logger.messages:
        if msg.to_agent and msg.agent in agent_keys and msg.to_agent in agent_keys:
            sources.append(agent_keys.index(msg.agent))
            targets.append(agent_keys.index(msg.to_agent))
            records = msg.data_passed.get("records", 1) if msg.data_passed else 1
            values.append(max(records, 1))
            link_labels.append(msg.message[:60])

    if not sources:
        st.info("No agent-to-agent exchanges recorded yet.")
        return

    def hex_to_rgba(hex_color, alpha=0.3):
        h = hex_color.lstrip('#')
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"

    link_colors = [hex_to_rgba(agent_colors[s]) for s in sources]

    fig = go.Figure(go.Sankey(
        node=dict(pad=15, thickness=20, label=agent_labels, color=agent_colors),
        link=dict(source=sources, target=targets, value=values,
                  label=link_labels, color=link_colors)
    ))
    fig.update_layout(title="Agent Data Flow", height=420,
                      font=dict(size=11),
                      plot_bgcolor='rgba(0,0,0,0)',
                      paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)


def render_agent_heatmap(logger: EnhancedActivityLogger):
    """Heatmap of agent-to-agent communication volume."""
    agent_keys = list(AGENT_PERSONAS.keys())
    agent_labels = [p.name for p in AGENT_PERSONAS.values()]
    n = len(agent_keys)
    matrix = [[0]*n for _ in range(n)]

    for msg in logger.messages:
        if msg.agent in agent_keys and msg.to_agent and msg.to_agent in agent_keys:
            i = agent_keys.index(msg.agent)
            j = agent_keys.index(msg.to_agent)
            matrix[i][j] += 1

    fig = go.Figure(go.Heatmap(
        z=matrix, x=agent_labels, y=agent_labels,
        colorscale="Blues", text=matrix, texttemplate="%{text}",
        hovertemplate="From: %{y}<br>To: %{x}<br>Exchanges: %{z}<extra></extra>"
    ))
    fig.update_layout(title="Agent Communication Matrix", height=420,
                      xaxis_title="Receiving Agent", yaxis_title="Sending Agent",
                      plot_bgcolor='rgba(0,0,0,0)',
                      paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)


def render_threaded_conversations(logger: EnhancedActivityLogger):
    """Render conversations grouped by agent handoff chains."""
    if not logger.messages:
        st.info("Run the pipeline to see agent conversations.")
        return

    chains = {}
    for msg in logger.messages:
        if msg.to_agent:
            chain_key = f"{msg.agent} -> {msg.to_agent}"
        else:
            chain_key = f"{msg.agent} (broadcast)"
        chains.setdefault(chain_key, []).append(msg)

    for chain_key, chain_msgs in chains.items():
        agents_in_chain = chain_key.split(" -> ")
        from_p = AGENT_PERSONAS.get(agents_in_chain[0])
        to_p = AGENT_PERSONAS.get(agents_in_chain[1]) if len(agents_in_chain) > 1 and " (broadcast)" not in chain_key else None

        header = f"{from_p.avatar if from_p else '?'} {from_p.name if from_p else agents_in_chain[0]}"
        if to_p:
            header += f"  -->  {to_p.avatar} {to_p.name}"

        flag_count = sum(1 for m in chain_msgs if m.status_badge == "FLAG")
        flag_text = f"  ({flag_count} flags)" if flag_count > 0 else ""

        with st.expander(f"{header}  |  {len(chain_msgs)} exchanges{flag_text}", expanded=False):
            for m in chain_msgs:
                p = AGENT_PERSONAS.get(m.agent)
                badge_colors = {"PASS": "#28a745", "FLAG": "#ffc107", "SKIP": "#dc3545"}
                badge_bg = badge_colors.get(m.status_badge, "#6c757d")
                conf_text = f" | Confidence: {m.confidence:.0%}" if m.confidence is not None else ""
                dollar_text = f" | Impact: ${m.dollar_impact:,.2f}" if m.dollar_impact is not None else ""
                time_str = m.timestamp.split("T")[1][:8] if "T" in m.timestamp else m.timestamp

                st.markdown(f"""
                <div style="background:#f8f9fa;border-left:4px solid {p.color if p else '#666'};
                            border-radius:0 10px 10px 0;padding:12px 18px;margin:8px 0;">
                    <div style="display:flex;align-items:center;margin-bottom:6px;">
                        <span style="font-size:1.3rem;margin-right:8px;">{p.avatar if p else '?'}</span>
                        <strong style="color:{p.color if p else '#333'};">{p.name if p else m.agent}</strong>
                        <span style="color:#999;margin-left:10px;font-size:0.8em;">{time_str}</span>
                        <span style="background:{badge_bg};color:white;padding:2px 8px;border-radius:10px;font-size:0.75em;margin-left:10px;">{m.status_badge}</span>
                    </div>
                    <div style="margin-left:36px;color:#333;">{m.message}</div>
                    <div style="margin-left:36px;margin-top:4px;font-size:0.85em;color:#666;">
                        {f"Decision: {m.decision}" if m.decision else ""}{conf_text}{dollar_text}
                    </div>
                </div>
                """, unsafe_allow_html=True)


def render_reconciliation_dashboard(recon_results: Dict):
    """Financial reconciliation summary for director review."""
    if not recon_results or not recon_results.get("vendors"):
        st.info("Reconciliation data not available. Run the pipeline with source files to generate reconciliation results.")
        return

    overall = recon_results.get("overall_status", "UNKNOWN")
    if overall == "MATCH":
        st.markdown("""
        <div class="recon-match">
            <strong>ALL VENDORS RECONCILED</strong> -- Calculated totals match billed totals within 2% threshold.
        </div>
        """, unsafe_allow_html=True)
    else:
        disc = recon_results.get('vendors_with_discrepancy', 0)
        miss = recon_results.get('vendors_missing_invoice', 0)
        st.markdown(f"""
        <div class="recon-alert">
            <strong>RECONCILIATION ALERT</strong> -- {disc} vendor(s) with discrepancies, {miss} missing invoice totals.
        </div>
        """, unsafe_allow_html=True)

    rows = []
    for vendor, data in recon_results.get("vendors", {}).items():
        rows.append({
            "Vendor": vendor,
            "Calculated Total": data["calculated"],
            "Billed Total": data["billed"],
            "Variance ($)": data["variance"],
            "Variance (%)": data["variance_pct"],
            "Records": data["record_count"],
            "Status": data["status"]
        })

    if rows:
        recon_df = pd.DataFrame(rows)

        def highlight_status(val):
            if val == "MATCH":
                return "background-color: #d4edda; color: #155724;"
            if val == "DISCREPANCY":
                return "background-color: #f8d7da; color: #721c24;"
            if val == "NO_INVOICE_FOUND":
                return "background-color: #fff3cd; color: #856404;"
            return ""

        styled = recon_df.style.format({
            "Calculated Total": "${:,.2f}",
            "Billed Total": "${:,.2f}",
            "Variance ($)": "${:,.2f}",
            "Variance (%)": "{:.2f}%"
        }).applymap(highlight_status, subset=["Status"])

        st.dataframe(styled, use_container_width=True)


def render_materiality_thresholds(total_spend: float, recon_results: Dict):
    """Display materiality thresholds with current status."""
    if not total_spend or total_spend == 0:
        st.info("Total spend data not available.")
        return

    total_variance = abs(recon_results.get("total_variance", 0))

    thresholds = [
        ("Planning Materiality (2%)", total_spend * 0.02),
        ("Performance Materiality (1.5%)", total_spend * 0.015),
        ("Trivial Threshold (0.5%)", total_spend * 0.005),
    ]

    st.markdown("### Materiality Assessment")
    for name, threshold in thresholds:
        if total_variance > threshold:
            st.error(f"{name}: ${threshold:,.0f} -- EXCEEDED (variance: ${total_variance:,.0f})")
        else:
            st.success(f"{name}: ${threshold:,.0f} -- Within threshold (variance: ${total_variance:,.0f})")

    planning_mat = total_spend * 0.02
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=total_variance,
        number={"prefix": "$", "valueformat": ",.0f"},
        delta={'reference': planning_mat, "prefix": "$", "valueformat": ",.0f"},
        title={'text': "Total Variance vs. Planning Materiality"},
        gauge={
            'axis': {'range': [0, planning_mat * 2], 'tickprefix': "$", 'tickformat': ",.0f"},
            'bar': {'color': "#dc3545" if total_variance > planning_mat else "#28a745"},
            'steps': [
                {'range': [0, total_spend * 0.005], 'color': "#d4edda"},
                {'range': [total_spend * 0.005, total_spend * 0.015], 'color': "#fff3cd"},
                {'range': [total_spend * 0.015, planning_mat * 2], 'color': "#f8d7da"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 3},
                'thickness': 0.75,
                'value': planning_mat
            }
        }
    ))
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)


def render_stage_confidence_chart(pipeline_summary: Dict, audit_logs: Dict):
    """Horizontal bar chart of confidence at each pipeline stage."""
    stages = []
    confidences = []

    files = pipeline_summary.get("files_processed", 0)
    stages.append("Intake")
    confidences.append(100.0 if files and files > 0 else 0.0)

    schema_df = audit_logs.get('schema')
    if schema_df is not None and hasattr(schema_df, 'empty') and not schema_df.empty and 'Confidence' in schema_df.columns:
        try:
            avg_conf = schema_df["Confidence"].astype(str).str.rstrip("%").astype(float).mean()
            stages.append("Schema Mapping")
            confidences.append(avg_conf)
        except Exception:
            stages.append("Schema Mapping")
            confidences.append(0.0)
    else:
        stages.append("Schema Mapping")
        confidences.append(0.0)

    extracted = pipeline_summary.get("records_extracted", 0)
    clean = pipeline_summary.get("records_clean", 0)
    if extracted and extracted > 0:
        stages.append("Standardization")
        confidences.append(min((clean or 0) / extracted * 100, 100))
    else:
        stages.append("Standardization")
        confidences.append(0.0)

    cost_with = pipeline_summary.get("cost_with", 0)
    if extracted and extracted > 0:
        stages.append("Cost Validation")
        confidences.append(min((cost_with or 0) / extracted * 100, 100))
    else:
        stages.append("Cost Validation")
        confidences.append(0.0)

    qa_dupes = pipeline_summary.get("qa_duplicates_removed", 0)
    qa_outliers = pipeline_summary.get("qa_outliers_flagged", 0)
    if clean and clean > 0:
        qa_conf = max(0, 100 - ((qa_dupes or 0) + (qa_outliers or 0)) / clean * 100)
        stages.append("Quality Assurance")
        confidences.append(min(qa_conf, 100))
    else:
        stages.append("Quality Assurance")
        confidences.append(0.0)

    stages.append("Reconciliation")
    recon = st.session_state.get("recon_results", {})
    if recon and recon.get("vendors"):
        match_count = sum(1 for v in recon["vendors"].values() if v["status"] == "MATCH")
        total_vendors = len(recon["vendors"])
        confidences.append(match_count / total_vendors * 100 if total_vendors > 0 else 0)
    else:
        confidences.append(0.0)

    colors = ["#28a745" if c >= 90 else "#ffc107" if c >= 70 else "#dc3545" for c in confidences]

    fig = go.Figure(go.Bar(
        x=confidences, y=stages, orientation='h',
        marker_color=colors,
        text=[f"{c:.0f}%" for c in confidences], textposition='inside'
    ))
    fig.update_layout(title="Confidence by Pipeline Stage", xaxis_range=[0, 105],
                      height=350, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)


def render_data_lineage(audit_logs: Dict):
    """Trace any metric back to its source."""
    st.markdown("### Data Lineage")
    st.caption("Trace any figure to its source. Select a metric to see the full audit chain.")

    lineage_choice = st.selectbox("Select metric to trace", [
        "Total Spend", "Record Count", "Cost Coverage", "Duplicate Count"
    ], key="lineage_select")

    if lineage_choice == "Total Spend":
        st.markdown("""
**Lineage Chain:**
1. **Source Files** -- Raw vendor invoices uploaded
2. **Intake Agent** -- File parsed, sheets identified
3. **Schema Agent** -- Cost column mapped (see confidence below)
4. **Standardizer** -- `total_charge` extracted per record
5. **Rate Card Agent** -- Missing costs flagged (not imputed in strict mode)
6. **QA Agent** -- Outlier costs validated via z-score analysis
7. **Aggregator** -- Summed to baseline `Cost` column
        """)
        schema_df = audit_logs.get('schema')
        if schema_df is not None and hasattr(schema_df, 'empty') and not schema_df.empty:
            st.markdown("**Cost Column Mapping Confidence by File:**")
            display_cols = [c for c in ["File", "Cost Col", "Confidence", "Source"] if c in schema_df.columns]
            if display_cols:
                st.dataframe(schema_df[display_cols], use_container_width=True)

    elif lineage_choice == "Record Count":
        st.markdown("""
**Lineage Chain:**
1. **Source Files** -- Raw rows in vendor spreadsheets
2. **Intake Agent** -- Sheets identified and loaded
3. **Schema Agent** -- Columns mapped, low-confidence sheets skipped
4. **Standardizer** -- Rows parsed into CanonicalRecord objects (rows with missing date/language dropped)
5. **QA Agent** -- Duplicates removed, critical errors quarantined
6. **Aggregator** -- Records grouped by Month/Vendor/Language/Modality
        """)
        std_df = audit_logs.get('standardizer')
        if std_df is not None and hasattr(std_df, 'empty') and not std_df.empty:
            st.markdown("**Extraction Results by File:**")
            st.dataframe(std_df, use_container_width=True)

    elif lineage_choice == "Cost Coverage":
        st.markdown("""
**Lineage Chain:**
1. **Schema Agent** -- Detects whether file has a cost/charge column
2. **Standardizer** -- Extracts `total_charge` from mapped column
3. **Rate Card Agent** -- Flags records missing cost as `MISSING` (strict mode: no imputation)
4. **Coverage** = Records with cost / Total records
        """)

    elif lineage_choice == "Duplicate Count":
        st.markdown("""
**Lineage Chain:**
1. **QA Agent** -- Detects duplicates by composite key: date + vendor + language + minutes + charge
2. **Threshold** -- Exact match on all 5 fields = duplicate
3. **Action** -- Duplicates removed from clean record set
        """)


def render_exception_summary(logger: EnhancedActivityLogger):
    """Table of findings sorted by dollar impact."""
    findings = logger.findings
    warn_critical = [f for f in findings if f.severity in ("warning", "critical")]
    if not warn_critical:
        st.success("No exceptions or risks detected.")
        return

    rows = []
    for f in warn_critical:
        rows.append({
            "Agent": f.agent,
            "Issue": f.description,
            "Impact": f.impact,
            "Reference": f.reference,
            "Severity": f.severity.upper()
        })

    exc_df = pd.DataFrame(rows)

    def color_severity(val):
        if val == "CRITICAL":
            return "background-color: #f8d7da; color: #721c24;"
        if val == "WARNING":
            return "background-color: #fff3cd; color: #856404;"
        return ""

    styled = exc_df.style.applymap(color_severity, subset=["Severity"])
    st.dataframe(styled, use_container_width=True)


def render_signoff_section():
    """Sign-off ready format for financial director."""
    st.markdown("### Sign-Off")
    st.markdown('<div class="signoff-section">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Prepared By:**")
        st.text_input("System", value="Baseline Factory Automated System", disabled=True, key="prepared_by")
        st.text_input("Date", value=datetime.now().strftime("%Y-%m-%d"), disabled=True, key="prepared_date")

    with col2:
        st.markdown("**Reviewed By:**")
        reviewer = st.text_input("Reviewer Name", value=st.session_state.signoff_data.get("reviewer", ""), key="reviewer_name")
        review_date = st.date_input("Review Date", key="review_date")
        review_status = st.selectbox("Review Status",
            ["Pending Review", "Approved", "Approved with Exceptions", "Rejected"],
            key="review_status")

    review_notes = st.text_area("Review Notes / Exceptions", key="review_notes", height=100)

    st.session_state.signoff_data = {
        "reviewer": reviewer,
        "status": review_status,
        "notes": review_notes,
        "date": str(review_date)
    }
    st.markdown('</div>', unsafe_allow_html=True)


def render_audit_trail(logger: EnhancedActivityLogger, audit_logs: Dict):
    """Complete audit trail - every decision, every reasoning."""
    st.markdown("### Complete Agent Decision Log")
    st.caption("Every decision made by every agent, with reasoning and source references.")

    col1, col2 = st.columns(2)
    with col1:
        all_agent_names = [p.name for p in AGENT_PERSONAS.values()]
        agent_filter = st.multiselect("Filter by Agent", all_agent_names, default=all_agent_names, key="audit_agent_filter")
    with col2:
        severity_filter = st.multiselect("Filter by Type",
            ["status", "handoff", "success", "alert", "finding"],
            default=["status", "handoff", "success", "alert", "finding"],
            key="audit_type_filter")

    agent_name_to_key = {p.name: k for k, p in AGENT_PERSONAS.items()}
    selected_keys = {agent_name_to_key.get(n) for n in agent_filter}

    for msg in logger.messages:
        if msg.agent not in selected_keys:
            continue
        if msg.message_type not in severity_filter:
            continue

        p = AGENT_PERSONAS.get(msg.agent)
        badge_colors = {"PASS": "#28a745", "FLAG": "#ffc107", "SKIP": "#dc3545"}
        badge_bg = badge_colors.get(msg.status_badge, "#6c757d")
        time_str = msg.timestamp.split("T")[1][:8] if "T" in msg.timestamp else msg.timestamp
        to_text = ""
        if msg.to_agent:
            to_p = AGENT_PERSONAS.get(msg.to_agent)
            to_text = f" --> {to_p.avatar} {to_p.name}" if to_p else f" --> {msg.to_agent}"

        st.markdown(f"""
        <div style="border-left:4px solid {p.color if p else '#666'};padding:10px 15px;margin:6px 0;background:#f8f9fa;border-radius:0 8px 8px 0;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                <span style="font-size:1.2rem;">{p.avatar if p else '?'}</span>
                <strong style="color:{p.color if p else '#333'};">{p.name if p else msg.agent}</strong>
                <span style="color:#999;font-size:0.8em;">{time_str}</span>
                <span style="background:{badge_bg};color:white;padding:1px 8px;border-radius:8px;font-size:0.75em;">{msg.status_badge}</span>
                <span style="color:#007bff;font-size:0.85em;">{to_text}</span>
            </div>
            <div style="margin-left:30px;color:#333;">{msg.message}</div>
            {f'<div style="margin-left:30px;margin-top:3px;font-size:0.85em;color:#555;">Decision: {msg.decision}</div>' if msg.decision else ''}
            {f'<div style="margin-left:30px;font-size:0.85em;color:#555;">Data: {_format_data_summary(msg.data_passed)}</div>' if msg.data_passed else ''}
        </div>
        """, unsafe_allow_html=True)

    # Schema Mapping Decisions
    st.markdown("---")
    st.markdown("### Schema Mapping Decisions")
    schema_df = audit_logs.get('schema')
    if schema_df is not None and hasattr(schema_df, 'empty') and not schema_df.empty:
        st.dataframe(schema_df, use_container_width=True)
        for _, row in schema_df.iterrows():
            reasoning = row.get("AI Reasoning")
            if reasoning and str(reasoning) not in ("", "None", "nan"):
                with st.expander(f"AI Reasoning: {row.get('File', '?')} / {row.get('Sheet', '?')}"):
                    st.markdown(str(reasoning))
    else:
        st.info("No schema audit data available.")

    # QA Decision Detail
    st.markdown("---")
    st.markdown("### QA Decision Thresholds")
    config_path = os.path.join(BASE_DIR, "config", "agent_config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            agent_config = json.load(f)
        qa_config = agent_config.get("QAgent", {})
        q1, q2, q3, q4 = st.columns(4)
        with q1:
            st.metric("Z-Score Threshold", qa_config.get("rate_std_dev_threshold", "N/A"))
        with q2:
            st.metric("Max Duration (min)", qa_config.get("duration_max_minutes", "N/A"))
        with q3:
            st.metric("Min Rate ($/min)", f"${qa_config.get('min_rate_threshold', 0):.2f}")
        with q4:
            st.metric("Max Rate ($/min)", f"${qa_config.get('max_rate_threshold', 0):.2f}")
    else:
        st.info("Agent configuration file not found.")

    # Standardization Results
    st.markdown("---")
    st.markdown("### Standardization Results")
    std_df = audit_logs.get('standardizer')
    if std_df is not None and hasattr(std_df, 'empty') and not std_df.empty:
        st.dataframe(std_df, use_container_width=True)
    else:
        st.info("No standardization audit data available.")

    # Intake Diagnostics
    st.markdown("---")
    st.markdown("### Intake Diagnostics")
    intake_data = audit_logs.get('intake', {})
    if intake_data and isinstance(intake_data, dict) and len(intake_data) > 0:
        intake_rows = []
        for f_key, diag in intake_data.items():
            intake_rows.append({
                "File": diag.get('file', f_key),
                "Best Sheet": diag.get('best_sheet', 'N/A'),
                "Sheets Scanned": len(diag.get('sheets_analyzed', [])),
                "Error": diag.get('error', 'None')
            })
        st.dataframe(pd.DataFrame(intake_rows), use_container_width=True)
    else:
        st.info("No intake diagnostics available.")


# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.image("https://via.placeholder.com/200x60?text=Baseline+Factory", use_container_width=True)
    st.markdown("---")

    st.header("📂 Data Input")
    uploaded_files = st.file_uploader(
        "Upload Vendor Files",
        type=['xlsx', 'xls', 'csv'],
        accept_multiple_files=True,
        help="Support for Excel and CSV files"
    )

    st.markdown("---")

    # Load Previous Analysis
    if os.path.exists(BASELINE_CSV):
        if st.button("📂 Load Previous Analysis", use_container_width=True):
            try:
                df_load = pd.read_csv(BASELINE_CSV)
                st.session_state.baseline_data = df_load
                st.session_state.processing_complete = True

                if os.path.exists(REPORT_TXT):
                    with open(REPORT_TXT, "r", encoding="utf-8") as f:
                        st.session_state.baseline_report_text = f.read()

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

    st.markdown("---")

    use_local = st.checkbox(
        "Use existing files in 'data_files/'",
        value=False,
        help="Process files already stored on the server"
    )

    run_btn = st.button(
        "🚀 Run Agent Pipeline",
        type="primary",
        disabled=(not uploaded_files and not use_local),
        use_container_width=True
    )

    st.markdown("---")

    # System Status
    st.markdown("### 📡 System Status")
    if st.session_state.processing_complete:
        st.success("✅ Pipeline Complete")
    else:
        st.info("⏳ Awaiting Data")

    # Agent Team Panel
    st.markdown("### 👥 Agent Team")
    for key, persona in list(AGENT_PERSONAS.items())[:6]:
        st.markdown(f"{persona.avatar} **{persona.name}** - {persona.role}")

    st.markdown("---")
    if st.checkbox("Learning controls", value=False, help="Approve or correct learned mappings."):
        mem_dir = Path(BASE_DIR) / "agent_memory"
        pending_path = mem_dir / "pending_mappings.json"
        pending = load_json(pending_path, [])
        if not isinstance(pending, list):
            pending = []

        st.markdown("### 🧠 Learning Queue")
        st.metric("Pending mappings", len(pending))
        if not hasattr(SchemaAgent, "track_mapping_success"):
            st.warning("Learning stats are disabled (missing `track_mapping_success`). Approvals will still save mappings.")

        if pending:
            auto_cfg = schema_detective.config if 'schema_detective' in locals() else None
            auto_field = None
            auto_data = None
            if auto_cfg:
                auto_field = auto_cfg.get("auto_approve_field_confidence")
                auto_data = auto_cfg.get("auto_approve_data_confidence")
            if auto_field is None:
                auto_field = 0.90
            if auto_data is None:
                auto_data = 0.85

            auto_label = f"Auto-approve high confidence (field ≥ {auto_field:.2f}, data ≥ {auto_data:.2f})"
            auto_mode = st.checkbox(auto_label, value=False, help="When enabled, auto-approves mappings above thresholds.")

            if auto_mode:
                agent = SchemaAgent()
                remaining = []
                approved_count = 0
                for entry in pending:
                    field_conf = float(entry.get("field_confidence", 0.0))
                    data_conf = float(entry.get("data_confidence", 0.0))
                    if field_conf >= auto_field and data_conf >= auto_data:
                        agent.save_approved_mapping(entry)
                        if hasattr(agent, "track_mapping_success"):
                            agent.track_mapping_success(source=entry.get('source'))
                        approved_count += 1
                    else:
                        remaining.append(entry)
                if approved_count > 0:
                    save_json(pending_path, remaining)
                    st.success(f"Auto-approved {approved_count} mappings.")
                    st.rerun()
            # Group duplicates to keep UI small
            grouped = {}
            for idx, entry in enumerate(pending):
                vendor = entry.get("vendor", "UNKNOWN")
                sig = entry.get("columns_signature")
                mapping = entry.get("mapping", {})
                key = (vendor, sig, json.dumps(mapping, sort_keys=True))
                if key not in grouped:
                    grouped[key] = {"entry": entry, "indices": []}
                grouped[key]["indices"].append(idx)

            unique_entries = list(grouped.values())

            if st.button("✅ Approve All", use_container_width=True):
                agent = SchemaAgent()
                for item in unique_entries:
                    entry = item["entry"]
                    agent.save_approved_mapping(entry)
                    if hasattr(agent, "track_mapping_success"):
                        agent.track_mapping_success(source=entry.get('source'))
                save_json(pending_path, [])
                st.success("Approved all pending mappings.")
                st.rerun()

            option_labels = []
            for i, item in enumerate(unique_entries):
                entry = item["entry"]
                vendor = entry.get("vendor", "UNKNOWN")
                field_conf = entry.get("field_confidence", 0)
                data_conf = entry.get("data_confidence", 0)
                count = len(item["indices"])
                option_labels.append(f"[{i}] {vendor} (field {field_conf:.2f}, data {data_conf:.2f}, x{count})")

            selected_label = st.selectbox("Review a mapping", option_labels)
            selected_index = int(selected_label.split("]")[0].strip("["))
            selected_item = unique_entries[selected_index]
            selected_entry = selected_item["entry"]
            selected_indices = set(selected_item["indices"])

            with st.expander("Mapping details", expanded=False):
                cols = selected_entry.get("columns", [])
                st.markdown("**Columns**")
                st.write(cols)
                st.markdown("**Current mapping**")
                st.write(selected_entry.get("mapping", {}))
                reasoning = selected_entry.get("ai_reasoning")
                if reasoning:
                    st.markdown("**AI explanation**")
                    st.write(reasoning)

            edit_mode = st.checkbox("Edit mapping before approval", value=False)
            corrected_mapping = dict(selected_entry.get("mapping", {}))
            if edit_mode:
                cols = selected_entry.get("columns", [])
                options = ["(not mapped)"] + cols
                for field in ["date", "language", "minutes", "charge", "rate", "modality"]:
                    current = corrected_mapping.get(field, "(not mapped)")
                    choice = st.selectbox(
                        f"{field}",
                        options,
                        index=options.index(current) if current in options else 0,
                        key=f"learn_{selected_index}_{field}"
                    )
                    if choice == "(not mapped)":
                        corrected_mapping.pop(field, None)
                    else:
                        corrected_mapping[field] = choice

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Approve as-is", use_container_width=True):
                    agent = SchemaAgent()
                    agent.save_approved_mapping(selected_entry)
                    if hasattr(agent, "track_mapping_success"):
                        agent.track_mapping_success(source=selected_entry.get('source'))
                    pending = [e for i, e in enumerate(pending) if i not in selected_indices]
                    save_json(pending_path, pending)
                    st.success("Mapping approved.")
                    st.rerun()
            with col_b:
                if st.button("Approve with edits", use_container_width=True):
                    agent = SchemaAgent()
                    original = dict(selected_entry.get("mapping", {}))
                    if corrected_mapping != original:
                        agent.record_correction(
                            source_columns=selected_entry.get("columns", []),
                            original_mapping=original,
                            corrected_mapping=corrected_mapping,
                            vendor=selected_entry.get("vendor")
                        )
                    selected_entry["mapping"] = corrected_mapping
                    agent.save_approved_mapping(selected_entry)
                    pending = [e for i, e in enumerate(pending) if i not in selected_indices]
                    save_json(pending_path, pending)
                    st.success("Mapping approved with edits.")
                    st.rerun()
        else:
            st.info("No pending mappings to approve.")

# ============================================================================
# MAIN AREA - HEADER
# ============================================================================

st.markdown("""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px; border-radius: 15px; margin-bottom: 20px;">
    <h1 style="color: white; margin: 0;">🏭 Multi-Agent Baseline Factory</h1>
    <p style="color: rgba(255,255,255,0.8); margin: 10px 0 0 0;">
        Intelligent data processing with transparent agent collaboration
    </p>
</div>
""", unsafe_allow_html=True)

# Welcome message when no data
if not st.session_state.processing_complete and not uploaded_files and not use_local:
    st.info("👋 **Welcome!** Upload vendor files in the sidebar or select 'Use existing files' to activate the Agent Team.")

    # Show agent team introduction
    st.markdown("### 👥 Meet Your Agent Team")
    cols = st.columns(4)
    for i, (key, persona) in enumerate(list(AGENT_PERSONAS.items())[:8]):
        with cols[i % 4]:
            st.markdown(f"""
            <div style="background: white; border-radius: 10px; padding: 15px;
                        margin: 5px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center;">
                <div style="font-size: 2rem;">{persona.avatar}</div>
                <div style="font-weight: bold; color: {persona.color};">{persona.name}</div>
                <div style="font-size: 0.8em; color: #666;">{persona.role}</div>
            </div>
            """, unsafe_allow_html=True)

# ============================================================================
# PROCESSING PIPELINE
# ============================================================================

if run_btn:
    # Reset State
    st.session_state.baseline_data = None
    st.session_state.baseline_report_text = ""
    st.session_state.processing_complete = False
    st.session_state.agent_communications = []
    st.session_state.findings_log = []
    st.session_state.impact_metrics = {}
    st.session_state.enhanced_logger = EnhancedActivityLogger()
    st.session_state.recon_results = {}
    elogger = st.session_state.enhanced_logger

    # Setup Temp Dir
    upload_dir = UPLOAD_DIR
    if os.path.exists(upload_dir):
        shutil.rmtree(upload_dir)
    os.makedirs(upload_dir)

    # Pipeline Stages
    PIPELINE_STAGES = ["Intake", "Schema", "Transform", "Validate", "Reconcile", "Analyze", "Report"]

    # Create main layout
    col_progress, col_chat = st.columns([2, 1])

    with col_progress:
        st.markdown("### 📊 Pipeline Progress")
        progress_placeholder = st.empty()
        stage_placeholder = st.empty()
        detail_placeholder = st.container()

    with col_chat:
        st.markdown("### 💬 Agent Communications")
        chat_placeholder = st.container()

    # Progress bar
    main_progress = st.progress(0, text="Initializing Agent Swarm...")

    # ========== STAGE 1: INTAKE ==========
    with detail_placeholder:
        with st.status("📦 **Stage 1: Data Intake**", expanded=True) as status:
            current_stage = 0
            with stage_placeholder:
                render_progress_pipeline(current_stage, PIPELINE_STAGES)

            file_paths = []
            loaded_files = []

            elogger.add_message("intake", "Initializing data intake protocols...", "status")
            add_agent_message("intake", "Initializing data intake protocols...", "status")

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
                for root, dirs, files in os.walk(DATA_DIR):
                    for f in files:
                        if f.endswith(('.xlsx', '.xls', '.csv')) and not f.startswith('~$'):
                            src = os.path.join(root, f)
                            dst = os.path.join(upload_dir, f)
                            shutil.copy2(src, dst)
                            file_paths.append(dst)
                            loaded_files.append(f)

            if not loaded_files:
                st.error("No files found! Please upload or check 'data_files'.")
                st.stop()

            # Log intake results
            elogger.add_conversation_exchange(
                "intake", "schema",
                f"Successfully ingested {len(loaded_files)} files for processing.",
                data_passed={"files": len(loaded_files)},
                decision=f"INGESTED {len(loaded_files)} files",
                status_badge="PASS",
                confidence=1.0
            )
            add_agent_message(
                "intake",
                f"Successfully ingested **{len(loaded_files)} files** for processing.",
                "success",
                findings=[{
                    "reference": f"Source Directory: {DATA_DIR if use_local else 'Upload'}",
                    "description": f"Files detected: {', '.join(loaded_files[:3])}{'...' if len(loaded_files) > 3 else ''}",
                    "impact": "All files queued for schema detection"
                }]
            )

            # Display files found
            st.markdown("**Files Ingested:**")
            for f in loaded_files:
                st.markdown(f"- ✅ `{f}`")

            time.sleep(0.5)
            main_progress.progress(10, text="Files ingested...")

            # Initialize agents
            intake = IntakeAgent(upload_dir)
            schema_detective = SchemaAgent()
            standardizer = StandardizerAgent()
            all_records = []

            # Handoff message
            add_agent_message(
                "intake",
                f"Handing off {len(loaded_files)} files for schema detection.",
                "handoff",
                to_agent="schema"
            )

            status.update(label="✅ Stage 1 Complete: Data Intake", state="complete")

    # ========== STAGE 2: SCHEMA DETECTION ==========
    with detail_placeholder:
        with st.status("🕵️ **Stage 2: Schema Detection**", expanded=True) as status:
            current_stage = 1
            with stage_placeholder:
                render_progress_pipeline(current_stage, PIPELINE_STAGES)

            schema_audit_log = []
            std_audit_log = []

            elogger.add_message("schema", "Analyzing column structures across all files...", "status")
            add_agent_message("schema", "Analyzing column structures across all files...", "status")

            files_processed = 0
            total_files = len(file_paths)

            for idx, fp in enumerate(file_paths):
                vendor_name = os.path.basename(fp).split('.')[0].split('-')[0].strip()
                file_name = os.path.basename(fp)

                # Load Sheets
                sheets = intake.load_clean_sheet(fp)

                for sheet_name, df in sheets.items():
                    if len(df) < 5:
                        continue

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
                        # Success - add finding with exact reference
                        add_finding(
                            "schema",
                            "Column Mapping",
                            f"Mapped {len(mapping)} canonical fields using {source.upper()} detection",
                            f"{file_name}:{sheet_name}:Headers:A1-Z1",
                            f"Confidence: {int(confidence*100)}% (Field: {int(conf['field_confidence']*100)}%, Data: {int(conf['data_confidence']*100)}%)",
                            "success"
                        )

                        st.markdown(f"""
                        <div style="background: #d4edda; border-left: 4px solid #28a745;
                                    padding: 10px 15px; margin: 5px 0; border-radius: 0 8px 8px 0;">
                            <strong>✅ {file_name}</strong> → Sheet: <code>{sheet_name}</code><br>
                            <span style="color: #666;">Confidence: {int(confidence*100)}% | Source: {source} | Mapped: {list(mapping.keys())}</span>
                        </div>
                        """, unsafe_allow_html=True)

                        schema_audit_log.append({
                            "File": file_name,
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

                        # Handoff to Standardizer
                        elogger.add_conversation_exchange(
                            "schema", "standardizer",
                            f"Schema mapped for {sheet_name}. Passing {len(mapping)} canonical fields.",
                            data_passed={"records": len(df), "fields_mapped": len(mapping), "confidence": round(confidence, 2), "source": source},
                            decision=f"MAPPED {len(mapping)} fields via {source.upper()}",
                            status_badge="PASS" if confidence > 0.8 else "FLAG",
                            confidence=confidence
                        )
                        add_agent_message(
                            "schema",
                            f"Passing `{sheet_name}` with {len(mapping)} mapped fields to Transformer.",
                            "handoff",
                            to_agent="standardizer"
                        )

                        # Standardize
                        new_records = standardizer.process_dataframe(df, mapping, fp, vendor_name)

                        elogger.add_conversation_exchange(
                            "standardizer", "rate_card",
                            f"Extracted {len(new_records):,} canonical records from {sheet_name}",
                            data_passed={"records": len(new_records), "input_rows": len(df), "dropped": len(df) - len(new_records)},
                            decision=f"EXTRACTED {len(new_records):,} of {len(df):,} rows",
                            status_badge="PASS" if len(new_records) > 0 else "SKIP",
                            confidence=len(new_records) / len(df) if len(df) > 0 else 0
                        )
                        add_agent_message(
                            "standardizer",
                            f"Extracted **{len(new_records):,}** canonical records from `{sheet_name}`",
                            "success",
                            findings=[{
                                "reference": f"{file_name}:{sheet_name}:Rows:1-{len(df)}",
                                "description": f"Transformed {len(df):,} raw rows → {len(new_records):,} records",
                                "impact": f"Data loss: {len(df) - len(new_records):,} rows ({(1-len(new_records)/len(df))*100:.1f}%)" if len(df) > 0 else "N/A"
                            }]
                        )

                        all_records.extend(new_records)

                        std_audit_log.append({
                            "File": file_name,
                            "Sheet": sheet_name,
                            "Input Rows": len(df),
                            "Extracted Records": len(new_records),
                            "Dropped Rows": len(df) - len(new_records),
                            "Status": "Success"
                        })
                    else:
                        # Low confidence - add warning finding
                        add_finding(
                            "schema",
                            "Low Confidence Skip",
                            f"Sheet skipped due to low mapping confidence",
                            f"{file_name}:{sheet_name}:Headers:A1-Z1",
                            f"Only {int(confidence*100)}% confidence (threshold: {int(min_final*100)}%)",
                            "warning"
                        )

                        st.markdown(f"""
                        <div style="background: #fff3cd; border-left: 4px solid #ffc107;
                                    padding: 10px 15px; margin: 5px 0; border-radius: 0 8px 8px 0;">
                            <strong>⚠️ {file_name}</strong> → Sheet: <code>{sheet_name}</code><br>
                            <span style="color: #856404;">Skipped (Low confidence: {int(confidence*100)}%)</span>
                        </div>
                        """, unsafe_allow_html=True)

                files_processed += 1
                progress_pct = 10 + int((files_processed / total_files) * 30)
                main_progress.progress(progress_pct, text=f"Processing file {files_processed}/{total_files}...")

            # Update impact metrics
            update_impact_metric("Records Extracted", len(all_records), direction="positive")
            update_impact_metric("Files Processed", len(file_paths), direction="positive")

            add_agent_message(
                "schema",
                f"Schema detection complete. **{len(all_records):,}** total records ready for validation.",
                "success"
            )

            status.update(label=f"✅ Stage 2 Complete: {len(all_records):,} Records Mapped", state="complete")

    # ========== STAGE 3: TRANSFORMATION & ENRICHMENT ==========
    with detail_placeholder:
        with st.status("⚙️ **Stage 3: Data Transformation**", expanded=True) as status:
            current_stage = 2
            with stage_placeholder:
                render_progress_pipeline(current_stage, PIPELINE_STAGES)

            main_progress.progress(45, text="Enriching records...")

            # Rate Card Agent
            elogger.add_message("rate_card", "Analyzing cost data and validating rates...", "status")
            add_agent_message("rate_card", "Analyzing cost data and imputing missing rates...", "status")

            rate_card = RateCardAgent()
            all_records, stats_imp = rate_card.batch_impute(all_records)

            cost_coverage_pct = (stats_imp.get('with_cost', 0) / len(all_records) * 100) if len(all_records) > 0 else 0
            elogger.add_conversation_exchange(
                "rate_card", "modality",
                f"Cost analysis complete. {stats_imp.get('with_cost', 0):,} records with cost data.",
                data_passed={"records": len(all_records), "with_cost": stats_imp.get('with_cost', 0), "imputed": stats_imp['imputed_count']},
                decision=f"VALIDATED {stats_imp.get('with_cost', 0):,} costs, imputed {stats_imp['imputed_count']:,}",
                status_badge="PASS" if cost_coverage_pct >= 98 else "FLAG",
                confidence=cost_coverage_pct / 100,
                dollar_impact=stats_imp['imputed_total_cost']
            )
            add_agent_message(
                "rate_card",
                f"Cost analysis complete. Imputed **{stats_imp['imputed_count']:,}** missing costs.",
                "success",
                findings=[{
                    "reference": f"Records with cost: {stats_imp.get('with_cost', 0):,}",
                    "description": f"Recovered ${stats_imp['imputed_total_cost']:,.2f} in previously missing cost data",
                    "impact": f"Cost coverage: {cost_coverage_pct:.1f}%"
                }]
            )

            st.markdown(f"""
            **Rate Card Analysis:**
            - Records with cost: `{stats_imp.get('with_cost', 0):,}`
            - Records imputed: `{stats_imp['imputed_count']:,}`
            - Recovered value: `${stats_imp['imputed_total_cost']:,.2f}`
            """)

            main_progress.progress(55, text="Classifying modalities...")

            # Modality Agent
            add_agent_message(
                "rate_card",
                "Passing enriched records to ServiceClassifier for modality detection.",
                "handoff",
                to_agent="modality"
            )

            modality = ModalityRefinementAgent()
            m_stats = modality.refine_records(all_records)

            unknown_count = m_stats.get('Unknown', 0) + m_stats.get('UNKNOWN', 0)
            elogger.add_conversation_exchange(
                "modality", "qa",
                f"Service classification complete. OPI: {m_stats.get('OPI', 0):,}, VRI: {m_stats.get('VRI', 0):,}, Unknown: {unknown_count:,}",
                data_passed={"records": len(all_records), "OPI": m_stats.get('OPI', 0), "VRI": m_stats.get('VRI', 0), "Translation": m_stats.get('Translation', 0), "Unknown": unknown_count},
                decision=f"CLASSIFIED all records into {len([k for k,v in m_stats.items() if v > 0])} modalities",
                status_badge="PASS" if unknown_count == 0 else "FLAG",
                confidence=1.0 - (unknown_count / len(all_records) if len(all_records) > 0 else 0)
            )
            add_agent_message(
                "modality",
                f"Service classification complete. Distribution: OPI({m_stats['OPI']}), VRI({m_stats['VRI']}), Translation({m_stats.get('Translation', 0)})",
                "success"
            )

            st.markdown(f"""
            **Modality Classification:**
            - OPI (Phone): `{m_stats['OPI']:,}`
            - VRI (Video): `{m_stats['VRI']:,}`
            - Translation: `{m_stats.get('Translation', 0):,}`
            """)

            status.update(label="✅ Stage 3 Complete: Data Enriched", state="complete")

    # ========== STAGE 4: QUALITY ASSURANCE ==========
    with detail_placeholder:
        with st.status("🛡️ **Stage 4: Quality Assurance**", expanded=True) as status:
            current_stage = 3
            with stage_placeholder:
                render_progress_pipeline(current_stage, PIPELINE_STAGES)

            main_progress.progress(65, text="Running quality checks...")

            add_agent_message(
                "modality",
                f"Handing off {len(all_records):,} records for quality validation.",
                "handoff",
                to_agent="qa"
            )

            qa = QAgent()
            all_records_clean, qa_stats = qa.process_records(all_records)

            removed = qa_stats['duplicates_removed']
            issues = qa_stats['outliers_flagged'] + qa_stats.get('critical_errors_quarantined', 0)

            # Add detailed findings for QA
            if removed > 0:
                add_finding(
                    "qa",
                    "Duplicate Detection",
                    f"Removed {removed:,} duplicate records",
                    "All Files:All Sheets:Duplicate Key Analysis",
                    f"Data reduction: {removed:,} rows ({removed/len(all_records)*100:.1f}%)",
                    "warning"
                )

            if issues > 0:
                add_finding(
                    "qa",
                    "Outlier Detection",
                    f"Flagged {issues:,} anomalous records for review",
                    "Statistical Analysis:Z-Score > 3.0",
                    "Potential data quality issues identified",
                    "warning"
                )

            add_agent_message(
                "qa",
                f"Quality scan complete. Removed **{removed:,}** duplicates, flagged **{issues:,}** anomalies.",
                "alert" if issues > 1000 else "success",
                findings=[{
                    "reference": "QA Analysis Summary",
                    "description": f"Input: {len(all_records):,} → Output: {len(all_records_clean):,} clean records",
                    "impact": f"Quality improvement: {(1 - len(all_records_clean)/len(all_records))*100:.1f}% data cleaned"
                }]
            )

            st.markdown(f"""
            **Quality Assurance Results:**
            - Input records: `{len(all_records):,}`
            - Duplicates removed: `{removed:,}` 🗑️
            - Outliers flagged: `{qa_stats['outliers_flagged']:,}` 🚩
            - Clean records: `{len(all_records_clean):,}` ✅
            """)

            # Data quality gauge
            quality_score = (len(all_records_clean) / len(all_records) * 100) if len(all_records) > 0 else 0
            update_impact_metric("Data Quality Score", f"{quality_score:.1f}%", direction="positive")

            elogger.add_conversation_exchange(
                "qa", "reconciliation",
                f"Quality scan complete. {len(all_records_clean):,} clean records, {removed:,} duplicates removed, {issues:,} anomalies flagged.",
                data_passed={"records_clean": len(all_records_clean), "duplicates_removed": removed, "outliers_flagged": issues},
                decision=f"CLEANED {len(all_records):,} -> {len(all_records_clean):,} records",
                status_badge="PASS" if issues < 1000 else "FLAG",
                confidence=quality_score / 100
            )
            if removed > 0:
                elogger.add_finding("qa", "Duplicate Detection", f"Removed {removed:,} duplicate records",
                                   "All Files:Duplicate Key Analysis", f"Data reduction: {removed:,} rows", "warning")
            if issues > 0:
                elogger.add_finding("qa", "Outlier Detection", f"Flagged {issues:,} anomalous records",
                                   "Statistical Analysis:Z-Score > 3.0", "Potential data quality issues", "warning")

            status.update(label=f"✅ Stage 4 Complete: {len(all_records_clean):,} Clean Records", state="complete")

    # ========== STAGE 4.5: RECONCILIATION ==========
    with detail_placeholder:
        with st.status("⚖️ **Stage 5: Reconciliation**", expanded=True) as status:
            current_stage = 4
            with stage_placeholder:
                render_progress_pipeline(current_stage, PIPELINE_STAGES)

            main_progress.progress(72, text="Running financial reconciliation...")

            add_agent_message("reconciliation", "Running bottom-up vs top-down invoice reconciliation...", "status")

            reconciler = ReconciliationAgent()

            # Extract invoice totals from all files
            for fp in file_paths:
                try:
                    sheets = intake.load_clean_sheet(fp)
                    vendor_name = os.path.basename(fp).split('.')[0].split('-')[0].strip()
                    reconciler.extract_totals_from_sheets(sheets, vendor_name)
                except Exception:
                    pass

            recon_results = reconciler.run_reconciliation(all_records_clean)
            st.session_state.recon_results = recon_results

            overall_status = recon_results.get("overall_status", "UNKNOWN")
            total_var = recon_results.get("total_variance", 0)
            disc_count = recon_results.get("vendors_with_discrepancy", 0)
            miss_count = recon_results.get("vendors_missing_invoice", 0)

            elogger.add_conversation_exchange(
                "reconciliation", "aggregator",
                f"Reconciliation complete. {len(recon_results.get('vendors', {})):,} vendors checked. Status: {overall_status}.",
                data_passed={"vendors_checked": len(recon_results.get('vendors', {})), "total_variance": round(total_var, 2), "discrepancies": disc_count, "missing_invoices": miss_count},
                decision=f"RECONCILED {len(recon_results.get('vendors', {}))} vendors - {overall_status}",
                status_badge="PASS" if overall_status == "MATCH" else "FLAG",
                confidence=1.0 if overall_status == "MATCH" else 0.7,
                dollar_impact=total_var
            )

            if overall_status == "MATCH":
                st.success(f"All vendors reconciled within 2% threshold. Total variance: ${total_var:,.2f}")
            else:
                st.warning(f"Reconciliation alert: {disc_count} discrepancies, {miss_count} missing invoices. Variance: ${total_var:,.2f}")

            add_agent_message(
                "reconciliation",
                f"Reconciliation {overall_status}. {disc_count} discrepancies, total variance: ${total_var:,.2f}",
                "success" if overall_status == "MATCH" else "alert",
                to_agent="aggregator"
            )

            status.update(label=f"✅ Stage 5 Complete: Reconciliation {overall_status}", state="complete")

    # ========== STAGE 6: ANALYSIS ==========
    with detail_placeholder:
        with st.status("📈 **Stage 6: Strategic Analysis**", expanded=True) as status:
            current_stage = 5
            with stage_placeholder:
                render_progress_pipeline(current_stage, PIPELINE_STAGES)

            main_progress.progress(80, text="Running strategic analysis...")

            add_agent_message(
                "qa",
                f"Passing {len(all_records_clean):,} validated records for strategic analysis.",
                "handoff",
                to_agent="aggregator"
            )

            # Aggregator
            aggregator = AggregatorAgent()
            baseline_df = aggregator.create_baseline(all_records_clean)

            total_spend = float(baseline_df['Cost'].sum()) if not baseline_df.empty else 0
            elogger.add_conversation_exchange(
                "aggregator", "analyst",
                f"Created baseline with {len(baseline_df):,} aggregated rows. Total spend: ${total_spend:,.2f}",
                data_passed={"baseline_rows": len(baseline_df), "total_spend": round(total_spend, 2), "total_minutes": float(baseline_df['Minutes'].sum()) if 'Minutes' in baseline_df.columns else 0},
                decision=f"AGGREGATED {len(all_records_clean):,} records -> {len(baseline_df):,} baseline rows",
                status_badge="PASS",
                confidence=1.0,
                dollar_impact=total_spend
            )
            add_agent_message(
                "aggregator",
                f"Created baseline with **{len(baseline_df):,}** aggregated rows.",
                "success"
            )

            # Analyst
            add_agent_message(
                "aggregator",
                "Passing baseline to InsightEngine for variance decomposition.",
                "handoff",
                to_agent="analyst"
            )

            analyst = AnalystAgent()
            variance_results = analyst.analyze_variance(baseline_df)

            # Extract key variance findings
            for period, data in variance_results.items():
                if isinstance(data, dict) and 'total_variance' in data:
                    add_finding(
                        "analyst",
                        "Variance Analysis",
                        f"Period {period}: ${data['total_variance']:,.2f} total variance",
                        f"Baseline Analysis:{period}",
                        f"Price: ${data['price_impact']:,.2f} | Volume: ${data['volume_impact']:,.2f} | Mix: ${data['mix_impact']:,.2f}",
                        "info"
                    )

            total_var_sum = sum(abs(d.get('total_variance', 0)) for d in variance_results.values() if isinstance(d, dict))
            elogger.add_conversation_exchange(
                "analyst", "simulator",
                f"Variance decomposition complete. {len(variance_results)} periods analyzed.",
                data_passed={"periods_analyzed": len(variance_results), "total_variance": round(total_var_sum, 2)},
                decision=f"ANALYZED {len(variance_results)} periods with Price-Volume-Mix decomposition",
                status_badge="PASS",
                confidence=1.0,
                dollar_impact=total_var_sum
            )
            add_agent_message(
                "analyst",
                "Variance decomposition complete. Price-Volume-Mix analysis ready.",
                "success"
            )

            # Simulator
            add_agent_message(
                "analyst",
                "Passing analysis to OpportunityFinder for savings simulation.",
                "handoff",
                to_agent="simulator"
            )

            simulator = SimulatorAgent()
            sim_res = simulator.run_scenarios(baseline_df)
            savings_found = sum(s['annual_impact'] for s in sim_res['scenarios'].values() if 'annual_impact' in s)

            elogger.add_conversation_exchange(
                "simulator", "reporter",
                f"Identified ${savings_found:,.2f} in potential efficiency opportunities.",
                data_passed={"scenarios": len(sim_res.get('scenarios', {})), "total_savings": round(savings_found, 2)},
                decision=f"IDENTIFIED ${savings_found:,.0f}/year in savings across {len(sim_res.get('scenarios', {}))} scenarios",
                status_badge="PASS" if savings_found > 0 else "FLAG",
                confidence=0.85,
                dollar_impact=savings_found
            )
            add_agent_message(
                "simulator",
                f"Identified **${savings_found:,.2f}** in potential efficiency opportunities.",
                "success" if savings_found > 0 else "status"
            )

            st.markdown(f"""
            **Strategic Analysis Summary:**
            - Baseline rows: `{len(baseline_df):,}`
            - Total spend analyzed: `${baseline_df['Cost'].sum():,.2f}`
            - Potential savings: `${savings_found:,.2f}`
            """)

            update_impact_metric("Total Spend", f"${baseline_df['Cost'].sum():,.2f}")
            update_impact_metric("Savings Identified", f"${savings_found:,.2f}", direction="positive")

            status.update(label="✅ Stage 6 Complete: Analysis Done", state="complete")

    # ========== STAGE 7: REPORT GENERATION ==========
    with detail_placeholder:
        with st.status("📝 **Stage 7: Report Generation**", expanded=True) as status:
            current_stage = 6
            with stage_placeholder:
                render_progress_pipeline(current_stage, PIPELINE_STAGES)

            main_progress.progress(95, text="Generating executive report...")

            add_agent_message(
                "simulator",
                "Passing all analysis results to ReportWriter for final compilation.",
                "handoff",
                to_agent="reporter"
            )

            reporter = ReportGeneratorAgent()
            reporter.baseline = baseline_df
            report_text = reporter.generate_full_report()

            elogger.add_message("reporter", "Executive Baseline Report generated. Ready for consultant review.", "success")
            add_agent_message(
                "reporter",
                "**Executive Baseline Report generated successfully!** Ready for consultant review.",
                "success"
            )

            st.success("✅ Report generation complete!")

            status.update(label="✅ Stage 7 Complete: Report Ready", state="complete")

    # ========== FINALIZE ==========
    main_progress.progress(100, text="✅ Pipeline Complete!")

    # Store results
    st.session_state.baseline_data = baseline_df
    st.session_state.baseline_report_text = report_text
    st.session_state.audit_logs = {
        'intake': intake.file_diagnostics,
        'schema': pd.DataFrame(schema_audit_log),
        'standardizer': pd.DataFrame(std_audit_log)
    }
    stats_imp_safe = stats_imp if isinstance(stats_imp, dict) else {}
    m_stats_safe = m_stats if isinstance(m_stats, dict) else {}
    qa_stats_safe = qa_stats if isinstance(qa_stats, dict) else {}
    schema_skipped = len([r for r in schema_audit_log if "Skipped" in str(r.get("Status", ""))])
    st.session_state.pipeline_summary = {
        "run_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "files_processed": len(file_paths),
        "schema_total": len(schema_audit_log),
        "schema_skipped": schema_skipped,
        "records_extracted": len(all_records),
        "records_clean": len(all_records_clean),
        "cost_with": stats_imp_safe.get("with_cost", 0),
        "cost_imputed": stats_imp_safe.get("imputed_count", 0),
        "cost_imputed_total": stats_imp_safe.get("imputed_total_cost", 0.0),
        "modality_unknown": m_stats_safe.get("Unknown", 0),
        "qa_duplicates_removed": qa_stats_safe.get("duplicates_removed", 0),
        "qa_outliers_flagged": qa_stats_safe.get("outliers_flagged", 0),
        "qa_critical": qa_stats_safe.get("critical_errors_quarantined", 0),
        "baseline_rows": len(baseline_df),
        "total_spend": float(baseline_df['Cost'].sum()) if not baseline_df.empty else 0.0,
        "savings_found": float(savings_found)
    }
    st.session_state.processing_complete = True

    # Save audit logs
    audit_export = {
        'intake': intake.file_diagnostics,
        'schema': schema_audit_log,
        'standardizer': std_audit_log
    }
    with open(os.path.join(BASE_DIR, "audit_logs.json"), "w") as f:
        json.dump(audit_export, f, indent=2, default=str)

    time.sleep(1)
    st.rerun()

# ============================================================================
# RESULTS DASHBOARD
# ============================================================================

if st.session_state.processing_complete and st.session_state.baseline_data is not None:
    df = st.session_state.baseline_data
    sim_def = SimulatorAgent()
    res_def = sim_def.run_scenarios(df)
    total_sav = sum(s['annual_impact'] for s in res_def['scenarios'].values() if 'annual_impact' in s)

    # Detailed Tabs
    audit_logs = st.session_state.get('audit_logs', {})

    elogger = st.session_state.enhanced_logger

    tab_labels = [
        "👥 Agent Team Room",
        "💰 Financial Director View",
        "📋 Audit Trail",
        "🧭 Consultant View",
        "📄 Executive Report",
        "📈 Spend Trends",
        "💡 Savings Opportunities",
        "💾 Data Table"
    ]

    tab_objs = st.tabs(tab_labels)
    tab_map = {label: tab for label, tab in zip(tab_labels, tab_objs)}

    # ========== AGENT TEAM ROOM TAB ==========
    with tab_map["👥 Agent Team Room"]:
        st.subheader("👥 Agent Team Room")
        st.caption("Watch your agent team communicate, make decisions, and pass data to each other in real-time.")

        # Agent Status Board
        st.markdown("#### Agent Status Board")
        render_agent_status_board(elogger)

        st.markdown("---")

        # Conversation Table
        st.markdown("#### Agent Conversation Log")
        st.caption("Every exchange between agents -- what was passed, what was decided, and the financial impact.")
        render_conversation_table(elogger)

        st.markdown("---")

        # Visualizations side by side
        viz_col1, viz_col2 = st.columns(2)
        with viz_col1:
            render_agent_flow_sankey(elogger)
        with viz_col2:
            render_agent_heatmap(elogger)

        st.markdown("---")

        # Threaded Conversations
        st.markdown("#### Threaded Conversations")
        st.caption("Drill into the full dialogue between each pair of agents.")
        render_threaded_conversations(elogger)

    # ========== FINANCIAL DIRECTOR VIEW TAB ==========
    with tab_map["💰 Financial Director View"]:
        st.subheader("💰 Financial Director View")
        st.caption("Reconciliation, materiality assessment, data lineage, and sign-off -- purpose-built for CPA review.")

        # Executive KPIs
        total_spend_val = float(df['Cost'].sum()) if not df.empty else 0
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.metric("Total Portfolio Spend", f"${total_spend_val:,.0f}")
        with k2:
            st.metric("Clean Records", f"{len(df):,}" if not df.empty else "0")
        with k3:
            st.metric("Identified Savings", f"${total_sav:,.0f}")
        with k4:
            quality_pct = st.session_state.get('pipeline_summary', {}).get('records_clean', 0)
            extracted = st.session_state.get('pipeline_summary', {}).get('records_extracted', 1)
            q_score = (quality_pct / extracted * 100) if extracted and quality_pct else 99.9
            st.metric("Data Quality", f"{q_score:.1f}%")

        st.markdown("---")

        # Reconciliation Dashboard
        st.markdown("### Reconciliation Summary")
        recon_data = st.session_state.get("recon_results", {})
        render_reconciliation_dashboard(recon_data)

        st.markdown("---")

        # Materiality
        render_materiality_thresholds(total_spend_val, recon_data)

        st.markdown("---")

        # Confidence by Stage
        st.markdown("### Confidence by Pipeline Stage")
        render_stage_confidence_chart(
            st.session_state.get("pipeline_summary", {}),
            audit_logs
        )

        st.markdown("---")

        # Data Lineage
        render_data_lineage(audit_logs)

        st.markdown("---")

        # Exception Summary
        st.markdown("### Exception Summary")
        st.caption("All warnings and critical findings, sorted by impact.")
        render_exception_summary(elogger)

        st.markdown("---")

        # Sign-Off
        render_signoff_section()

    # ========== AUDIT TRAIL TAB ==========
    with tab_map["📋 Audit Trail"]:
        st.subheader("📋 Complete Audit Trail")
        st.caption("Every agent decision with reasoning, confidence scores, and source references. Nothing is hidden.")
        render_audit_trail(elogger, audit_logs)

    if "📄 Executive Report" in tab_map:
        with tab_map["📄 Executive Report"]:
            st.subheader("📝 Executive Report")
            st.caption("Auto-generated consultant-grade report from the full transaction dataset.")
            st.text_area("Report Content", st.session_state.baseline_report_text, height=500)
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "📥 Download Report (TXT)",
                    st.session_state.baseline_report_text,
                    "BASELINE_REPORT.txt",
                    use_container_width=True
                )
            with col2:
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Download Baseline (CSV)",
                    data=csv,
                    file_name="baseline_final.csv",
                    mime="text/csv",
                    use_container_width=True
                )

    if "🧭 Consultant View" in tab_map:
        with tab_map["🧭 Consultant View"]:
            st.subheader("🧭 Consultant View")
            st.caption("Plain-English explanation of what happened and what to do next.")

            summary = dict(st.session_state.get("pipeline_summary", {}) or {})

            def _fmt_int(value):
                return f"{value:,}" if value is not None else "N/A"

            def _fmt_money(value):
                return f"${value:,.2f}" if value is not None else "N/A"

            def _fmt_pct(value):
                return f"{value:.1f}%" if value is not None else "N/A"

            files_processed = summary.get("files_processed")
            if files_processed is None and 'intake' in audit_logs and audit_logs['intake']:
                files_processed = len(audit_logs['intake'])

            intake_errors = summary.get("intake_errors")
            if intake_errors is None and 'intake' in audit_logs and audit_logs['intake']:
                intake_errors = sum(
                    1 for d in audit_logs['intake'].values()
                    if d.get('error') not in (None, "", "None")
                )
            intake_errors = intake_errors or 0

            schema_total = summary.get("schema_total")
            schema_skipped = summary.get("schema_skipped")
            if ('schema' in audit_logs) and (schema_total is None or schema_skipped is None):
                schema_df = audit_logs['schema']
                if hasattr(schema_df, 'empty') and not schema_df.empty:
                    schema_total = len(schema_df)
                    if 'Status' in schema_df.columns:
                        schema_skipped = int(schema_df['Status'].str.contains("Skipped", na=False).sum())
                    else:
                        schema_skipped = 0

            records_extracted = summary.get("records_extracted")
            if records_extracted is None and 'standardizer' in audit_logs and not audit_logs['standardizer'].empty:
                records_extracted = int(audit_logs['standardizer']['Extracted Records'].sum())

            records_clean = summary.get("records_clean")
            cost_with = summary.get("cost_with")
            cost_imputed = summary.get("cost_imputed")
            cost_imputed_total = summary.get("cost_imputed_total")
            modality_unknown = summary.get("modality_unknown")
            qa_duplicates_removed = summary.get("qa_duplicates_removed")
            qa_outliers_flagged = summary.get("qa_outliers_flagged")
            qa_critical = summary.get("qa_critical")
            baseline_rows = summary.get("baseline_rows", len(df))
            total_spend = summary.get("total_spend", float(df['Cost'].sum()))
            savings_found = summary.get("savings_found")
            if records_clean is None:
                records_clean = len(df)
            if savings_found is None:
                savings_found = total_sav

            quality_score = None
            if records_extracted and records_clean is not None:
                quality_score = (records_clean / records_extracted) * 100

            cost_coverage = None
            if records_extracted and cost_with is not None:
                cost_coverage = (cost_with / records_extracted) * 100

            # Build stage summaries and next steps
            stage_items = []

            intake_status = "good" if files_processed and intake_errors == 0 else ("warn" if files_processed else "bad")
            intake_confidence = "High" if intake_status == "good" else ("Medium" if intake_status == "warn" else "Low")
            intake_result = []
            if files_processed is not None:
                intake_result.append(f"{files_processed:,} file(s) processed.")
            if intake_errors:
                intake_result.append(f"{intake_errors} file(s) had read issues.")
            intake_next = None
            if not files_processed:
                intake_next = "Add vendor files in the sidebar or enable 'Use existing files'."
            elif intake_errors:
                intake_next = (
                    "Review the Audit Trail tab for files that failed to read."
                )
            stage_items.append({
                "title": "Stage 1: Intake",
                "what": "Collected vendor files and confirmed we could open them.",
                "results": intake_result,
                "confidence": intake_confidence,
                "next": intake_next,
                "status": intake_status,
                "action_label": "Intake"
            })

            schema_status = "good" if schema_total and (schema_skipped or 0) == 0 else ("warn" if schema_total else "bad")
            schema_confidence = "High" if schema_status == "good" else ("Medium" if schema_status == "warn" else "Low")
            schema_result = []
            if schema_total is not None:
                schema_result.append(f"{schema_total} sheet(s) evaluated.")
            if schema_skipped:
                schema_result.append(f"{schema_skipped} sheet(s) skipped due to low confidence.")
            if schema_skipped:
                schema_next = "Review the Audit Trail tab for skipped sheets and column mapping details."
            else:
                schema_next = None
            stage_items.append({
                "title": "Stage 2: Column Matching",
                "what": "Matched vendor columns to the standard baseline format.",
                "results": schema_result,
                "confidence": schema_confidence,
                "next": schema_next,
                "status": schema_status,
                "action_label": "Column Matching"
            })

            transform_result = []
            if cost_coverage is not None:
                transform_result.append(f"Cost coverage: {cost_coverage:.1f}%.")
            if cost_imputed:
                transform_result.append(f"Missing costs filled: {cost_imputed:,}.")
            if cost_imputed_total:
                transform_result.append(f"Recovered cost value: ${cost_imputed_total:,.2f}.")
            if modality_unknown:
                transform_result.append(f"Unknown service type records: {modality_unknown:,}.")

            transform_status = "good"
            if cost_coverage is not None and cost_coverage < 98.0:
                transform_status = "warn"
            if modality_unknown:
                transform_status = "warn"
            if not transform_result:
                transform_status = "warn"
                transform_result.append("Transformation metrics not available.")

            transform_confidence = "High" if transform_status == "good" else "Medium"
            transform_next = None
            if cost_coverage is not None and cost_coverage < 98.0:
                transform_next = "Add missing vendor rates to improve cost coverage."
            if modality_unknown:
                transform_next = "Review service type rules for unknown records."
            stage_items.append({
                "title": "Stage 3: Fill Missing Data",
                "what": "Filled missing costs and classified each service type.",
                "results": transform_result,
                "confidence": transform_confidence,
                "next": transform_next,
                "status": transform_status,
                "action_label": "Fill Missing Data"
            })

            validate_result = []
            if qa_duplicates_removed is not None:
                validate_result.append(f"Duplicates removed: {qa_duplicates_removed:,}.")
            if qa_outliers_flagged is not None:
                validate_result.append(f"Anomalies flagged: {qa_outliers_flagged:,}.")
            if records_clean is not None:
                validate_result.append(f"Clean records: {records_clean:,}.")

            validate_status = "good"
            if (qa_outliers_flagged or 0) > 0 or (qa_critical or 0) > 0:
                validate_status = "warn"
            if not validate_result:
                validate_status = "warn"
                validate_result.append("Quality metrics not available.")

            validate_confidence = "High" if validate_status == "good" else "Medium"
            validate_next = None
            if (qa_outliers_flagged or 0) > 0 or (qa_critical or 0) > 0:
                validate_next = "Review the Audit Trail tab for flagged anomalies and QA thresholds."
            stage_items.append({
                "title": "Stage 4: Quality Check",
                "what": "Removed duplicates and flagged anomalies for review.",
                "results": validate_result,
                "confidence": validate_confidence,
                "next": validate_next,
                "status": validate_status,
                "action_label": "Quality Check"
            })

            analysis_result = []
            if baseline_rows is not None:
                analysis_result.append(f"Baseline rows: {baseline_rows:,}.")
            if total_spend is not None:
                analysis_result.append(f"Total spend analyzed: ${total_spend:,.2f}.")
            if savings_found is not None:
                analysis_result.append(f"Potential savings identified: ${savings_found:,.2f}.")

            analysis_status = "good" if baseline_rows else "warn"
            analysis_confidence = "High" if analysis_status == "good" else "Medium"
            analysis_next = None
            if not baseline_rows:
                analysis_next = "Run the pipeline with valid input files to generate analysis."
            stage_items.append({
                "title": "Stage 5: Spend & Savings",
                "what": "Aggregated the baseline and calculated variance and savings.",
                "results": analysis_result,
                "confidence": analysis_confidence,
                "next": analysis_next,
                "status": analysis_status,
                "action_label": "Spend & Savings"
            })

            report_ready = bool(st.session_state.baseline_report_text)
            report_status = "good" if report_ready else "warn"
            report_confidence = "High" if report_ready else "Medium"
            report_result = ["Executive report generated."] if report_ready else ["Report not generated yet."]
            report_next = None if report_ready else "Complete a pipeline run to generate the report."
            stage_items.append({
                "title": "Stage 6: Executive Report",
                "what": "Compiled the executive report for stakeholder review.",
                "results": report_result,
                "confidence": report_confidence,
                "next": report_next,
                "status": report_status,
                "action_label": "Executive Report"
            })

            next_steps = [
                f"{item['action_label']}: {item['next']}"
                for item in stage_items
                if item.get("next")
            ]

            # Executive overview cards
            st.markdown("#### Executive Overview")
            run_stamp = st.session_state.get("pipeline_summary", {}).get("run_timestamp")
            if run_stamp:
                st.caption(f"Last run: {run_stamp}")

            total_spend_display = f"${total_spend:,.0f}" if total_spend is not None else "N/A"
            clean_records_display = f"{records_clean:,}" if records_clean is not None else "N/A"
            savings_display = f"${savings_found:,.0f}" if savings_found is not None else "N/A"
            quality_display = f"{quality_score:.1f}%" if quality_score is not None else "N/A"

            k1, k2, k3, k4 = st.columns(4)
            with k1:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            padding: 20px; border-radius: 12px; color: white; text-align: center;">
                    <div style="font-size: 0.9em; opacity: 0.9;">Total Portfolio Spend</div>
                    <div style="font-size: 1.8em; font-weight: bold;">{total_spend_display}</div>
                </div>
                """, unsafe_allow_html=True)

            with k2:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                            padding: 20px; border-radius: 12px; color: white; text-align: center;">
                    <div style="font-size: 0.9em; opacity: 0.9;">Clean Records</div>
                    <div style="font-size: 1.8em; font-weight: bold;">{clean_records_display}</div>
                </div>
                """, unsafe_allow_html=True)

            with k3:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                            padding: 20px; border-radius: 12px; color: white; text-align: center;">
                    <div style="font-size: 0.9em; opacity: 0.9;">Identified Savings</div>
                    <div style="font-size: 1.8em; font-weight: bold;">{savings_display}</div>
                </div>
                """, unsafe_allow_html=True)

            with k4:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                            padding: 20px; border-radius: 12px; color: white; text-align: center;">
                    <div style="font-size: 0.9em; opacity: 0.9;">Data Quality Score</div>
                    <div style="font-size: 1.8em; font-weight: bold;">{quality_display}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")

            # Story summary
            what_changed = "Not enough monthly history to compare yet."
            if "Month" in df.columns and "Cost" in df.columns:
                monthly = df.groupby("Month")["Cost"].sum().sort_index()
                if len(monthly) >= 2:
                    latest_month = monthly.index[-1]
                    prev_month = monthly.index[-2]
                    latest_spend = monthly.iloc[-1]
                    prev_spend = monthly.iloc[-2]
                    delta = latest_spend - prev_spend
                    direction = "increased" if delta >= 0 else "decreased"
                    if prev_spend != 0:
                        pct = abs(delta) / prev_spend * 100
                        what_changed = (
                            f"Spend {direction} by ${abs(delta):,.0f} ({pct:.1f}%) "
                            f"in {latest_month} vs {prev_month}."
                        )
                    else:
                        what_changed = f"Spend {direction} by ${abs(delta):,.0f} in {latest_month} vs {prev_month}."
                elif len(monthly) == 1:
                    only_month = monthly.index[-1]
                    what_changed = f"Only one month of data ({only_month}). No month-over-month comparison yet."

            where_spend = "No spend breakdown available."
            if "Vendor" in df.columns and total_spend:
                vendor_totals = df.groupby("Vendor")["Cost"].sum().sort_values(ascending=False)
                if len(vendor_totals) > 0:
                    top_vendor = vendor_totals.index[0]
                    top_vendor_cost = vendor_totals.iloc[0]
                    top_vendor_pct = top_vendor_cost / total_spend * 100
                    where_spend = f"Top vendor: {top_vendor} at ${top_vendor_cost:,.0f} ({top_vendor_pct:.1f}%)."
                    if len(vendor_totals) > 1:
                        second_vendor = vendor_totals.index[1]
                        second_vendor_cost = vendor_totals.iloc[1]
                        second_vendor_pct = second_vendor_cost / total_spend * 100
                        where_spend += f" Next: {second_vendor} at ${second_vendor_cost:,.0f} ({second_vendor_pct:.1f}%)."

            if "Modality" in df.columns and total_spend:
                modality_totals = df.groupby("Modality")["Cost"].sum().sort_values(ascending=False)
                if len(modality_totals) > 0:
                    top_modality = modality_totals.index[0]
                    top_modality_cost = modality_totals.iloc[0]
                    top_modality_pct = top_modality_cost / total_spend * 100
                    modality_line = (
                        f"Top service type: {top_modality} at ${top_modality_cost:,.0f} "
                        f"({top_modality_pct:.1f}%)."
                    )
                    if where_spend == "No spend breakdown available.":
                        where_spend = modality_line
                    else:
                        where_spend += f" {modality_line}"

            st.markdown("#### Story Summary")
            st.markdown(f"**What changed:** {what_changed}")
            st.markdown(f"**Where the spend is:** {where_spend}")
            if next_steps:
                st.markdown("**What needs attention:**")
                for step in next_steps:
                    st.markdown(f"- {step}")
            else:
                st.markdown("**What needs attention:** No action needed.")

            st.markdown("---")
            st.markdown("#### Risks & Exceptions")
            findings = st.session_state.get("findings_log", [])
            if findings:
                risk_items = [f for f in findings if f.get("severity") in ("warning", "critical")]
                if not risk_items:
                    risk_items = findings[:3]
                else:
                    risk_items = risk_items[:5]
                for item in risk_items:
                    st.markdown(f"- {item.get('description', 'Issue')} — {item.get('impact', '')}")
            else:
                st.success("No risks or exceptions detected.")

            story_summary = {
                "what_changed": what_changed,
                "where_spend": where_spend
            }
            metrics_summary = {
                "files_processed": _fmt_int(files_processed),
                "records_clean": _fmt_int(records_clean),
                "total_spend": _fmt_money(total_spend),
                "savings_found": _fmt_money(savings_found),
                "quality_score": _fmt_pct(quality_score),
                "cost_coverage": _fmt_pct(cost_coverage),
                "baseline_rows": _fmt_int(baseline_rows)
            }
            client_summary_text = build_client_summary_text(story_summary, metrics_summary, next_steps)
            col_a, col_b = st.columns(2)
            with col_a:
                st.download_button(
                    "📥 Download Client Summary (TXT)",
                    client_summary_text,
                    "CLIENT_SUMMARY.txt",
                    use_container_width=True
                )
            with col_b:
                pdf_bytes = build_client_summary_pdf_bytes(client_summary_text)
                if pdf_bytes:
                    st.download_button(
                        "📥 Download Client Summary (PDF)",
                        pdf_bytes,
                        "CLIENT_SUMMARY.pdf",
                        use_container_width=True
                    )
                else:
                    st.info("PDF export requires `reportlab` to be installed.")

            st.markdown("---")

            st.markdown("#### Operational Snapshot")
            g1, g2, g3 = st.columns(3)
            with g1:
                st.metric("Files processed", _fmt_int(files_processed))
            with g2:
                st.metric("Cost coverage", _fmt_pct(cost_coverage))
            with g3:
                st.metric("Baseline rows", _fmt_int(baseline_rows))

            st.markdown("---")

            for item in stage_items:
                render_consultant_stage(
                    item["title"],
                    item["what"],
                    item["results"],
                    item["confidence"],
                    item["next"],
                    item["status"]
                )

            st.markdown("#### Next Actions")
            if next_steps:
                for step in next_steps:
                    st.markdown(f"- {step}")
            else:
                st.success("No action needed. All stages completed cleanly.")

    if "📈 Spend Trends" in tab_map:
        with tab_map["📈 Spend Trends"]:
            st.subheader("📈 Spend Trends")

            c1, c2 = st.columns([2, 1])
            with c1:
                trend_data = df.groupby(['Month', 'Vendor'])['Cost'].sum().reset_index()
                fig = px.bar(
                    trend_data, x='Month', y='Cost', color='Vendor',
                    title='Monthly Spend Trend by Vendor',
                    template="plotly_white"
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig, use_container_width=True)

            with c2:
                mod_data = df.groupby('Modality')['Cost'].sum().reset_index()
                fig2 = px.pie(
                    mod_data, values='Cost', names='Modality', hole=0.4,
                    title='Spend by Service Type',
                    template="plotly_white"
                )
                st.plotly_chart(fig2, use_container_width=True)

            # Variance Analysis
            st.markdown("#### 🔍 Variance Decomposition")
            a_agent = AnalystAgent()
            var_res = a_agent.analyze_variance(df)

            var_rows = []
            for p, d in var_res.items():
                if isinstance(d, dict) and 'total_variance' in d:
                    var_rows.append({
                        "Period": p,
                        "Net Change": d['total_variance'],
                        "Due to Price": d['price_impact'],
                        "Due to Volume": d['volume_impact'],
                        "Due to Mix": d['mix_impact']
                    })

            if var_rows:
                vdf = pd.DataFrame(var_rows)
                st.dataframe(
                    vdf.style.format({
                        "Net Change": "${:,.0f}",
                        "Due to Price": "${:,.0f}",
                        "Due to Volume": "${:,.0f}",
                        "Due to Mix": "${:,.0f}"
                    }).background_gradient(cmap="RdYlGn", subset=["Net Change"]),
                    use_container_width=True
                )

    if "💡 Savings Opportunities" in tab_map:
        with tab_map["💡 Savings Opportunities"]:
            st.subheader("💡 Savings Opportunities")
            st.markdown("Identified efficiency projects and estimated annual impact:")

            for k, v in res_def['scenarios'].items():
                if 'annual_impact' in v:
                    savings_pct = v.get('savings_pct', 0)
                    st.markdown(f"""
                    <div style="background: white; border-radius: 12px; padding: 20px; margin: 15px 0;
                                box-shadow: 0 4px 15px rgba(0,0,0,0.1); border-left: 5px solid #28a745;">
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            <span style="font-size: 2rem; margin-right: 15px;">💰</span>
                            <div>
                                <div style="font-size: 1.2em; font-weight: bold;">{v['name']}</div>
                                <div style="color: #666; font-size: 0.9em;">{v['description']}</div>
                            </div>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 15px;">
                            <div>
                                <span style="font-size: 1.5em; font-weight: bold; color: #28a745;">
                                    ${v['annual_impact']:,.0f}
                                </span>
                                <span style="color: #666;"> / year</span>
                            </div>
                            <div style="background: #e9ecef; border-radius: 20px; padding: 5px 15px;">
                                {savings_pct:.1f}% of spend
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Progress bar
                    st.progress(min(savings_pct / 5.0, 1.0))

    if "💾 Data Table" in tab_map:
        with tab_map["💾 Data Table"]:
            st.subheader("💾 Data Table")
            st.caption("Browse and export the complete baseline dataset.")

            # Quick filters
            col1, col2, col3 = st.columns(3)
            with col1:
                vendors = ['All'] + list(df['Vendor'].unique())
                selected_vendor = st.selectbox("Filter by Vendor", vendors)
            with col2:
                modalities = ['All'] + list(df['Modality'].unique())
                selected_modality = st.selectbox("Filter by Modality", modalities)
            with col3:
                months = ['All'] + sorted(list(df['Month'].unique()))
                selected_month = st.selectbox("Filter by Month", months)

            # Apply filters
            filtered_df = df.copy()
            if selected_vendor != 'All':
                filtered_df = filtered_df[filtered_df['Vendor'] == selected_vendor]
            if selected_modality != 'All':
                filtered_df = filtered_df[filtered_df['Modality'] == selected_modality]
            if selected_month != 'All':
                filtered_df = filtered_df[filtered_df['Month'] == selected_month]

            st.dataframe(filtered_df, use_container_width=True)

            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download Filtered Data (CSV)",
                data=csv,
                file_name="baseline_filtered.csv",
                mime="text/csv",
                type="primary"
            )
