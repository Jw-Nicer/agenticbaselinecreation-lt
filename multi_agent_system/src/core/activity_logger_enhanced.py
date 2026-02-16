
"""
Enhanced Agent Activity Logger
Tracks agent activities with exact references and consultant-friendly reporting.
"""

import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
import json


@dataclass
class Finding:
    """A finding with exact reference to source data."""
    agent: str
    finding_type: str
    description: str
    reference: str  # e.g., "Healthpoint.xlsx:Sheet1:Row45:ColB"
    impact: str
    severity: str = "info"  # info, warning, critical, success
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AgentMessage:
    """A message from one agent, optionally to another."""
    agent: str
    message: str
    message_type: str = "status"  # status, finding, handoff, alert, success
    to_agent: Optional[str] = None
    findings: List[Finding] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    data_passed: Optional[Dict[str, Any]] = None
    decision: Optional[str] = None
    status_badge: str = "PASS"  # PASS, FLAG, SKIP
    confidence: Optional[float] = None  # 0.0-1.0
    dollar_impact: Optional[float] = None

    def to_dict(self) -> Dict:
        d = asdict(self)
        d['findings'] = [f.to_dict() if isinstance(f, Finding) else f for f in self.findings]
        return d


@dataclass
class ImpactMetric:
    """Tracks impact on baseline creation."""
    name: str
    value: Any
    delta: Optional[Any] = None
    direction: str = "neutral"  # positive, negative, neutral
    description: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


class EnhancedActivityLogger:
    """
    Enhanced logger that captures:
    - Agent-to-agent communications (like real team members)
    - Findings with exact file:sheet:row:column references
    - Impact metrics for baseline creation
    - Timeline of activities
    """

    def __init__(self):
        self.start_time = datetime.datetime.now()
        self.activities: List[Dict[str, Any]] = []
        self.agent_summaries: Dict[str, Dict[str, Any]] = {}
        self.messages: List[AgentMessage] = []
        self.findings: List[Finding] = []
        self.impact_metrics: Dict[str, ImpactMetric] = {}
        self.pipeline_stages: List[Dict[str, Any]] = []

    # =========================================================================
    # CORE LOGGING
    # =========================================================================

    def log(self, agent_name: str, action: str, details: Dict[str, Any] = None):
        """Log an agent activity (legacy compatibility)."""
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "agent": agent_name,
            "action": action,
            "details": details or {}
        }
        self.activities.append(entry)

    def set_summary(self, agent_name: str, summary: Dict[str, Any]):
        """Set the final summary for an agent."""
        self.agent_summaries[agent_name] = summary

    # =========================================================================
    # AGENT COMMUNICATIONS (Chat-like)
    # =========================================================================

    def add_message(self, agent: str, message: str, message_type: str = "status",
                   to_agent: str = None, findings: List[Finding] = None):
        """Add a message from an agent (like team chat)."""
        msg = AgentMessage(
            agent=agent,
            message=message,
            message_type=message_type,
            to_agent=to_agent,
            findings=findings or []
        )
        self.messages.append(msg)
        return msg

    def add_handoff(self, from_agent: str, to_agent: str, message: str,
                    context: Dict[str, Any] = None):
        """Record when one agent hands off work to another."""
        msg = self.add_message(
            agent=from_agent,
            message=message,
            message_type="handoff",
            to_agent=to_agent
        )

        # Also log as activity
        self.log(from_agent, "HANDOFF", {
            "to_agent": to_agent,
            "message": message,
            **(context or {})
        })
        return msg

    def add_conversation_exchange(self, from_agent: str, to_agent: str,
                                   message: str, data_passed: Dict[str, Any] = None,
                                   decision: str = None, status_badge: str = "PASS",
                                   confidence: float = None, dollar_impact: float = None,
                                   findings: List[Finding] = None) -> AgentMessage:
        """Record a structured conversation exchange between agents."""
        msg = AgentMessage(
            agent=from_agent,
            message=message,
            message_type="handoff",
            to_agent=to_agent,
            findings=findings or [],
            data_passed=data_passed,
            decision=decision,
            status_badge=status_badge,
            confidence=confidence,
            dollar_impact=dollar_impact
        )
        self.messages.append(msg)

        self.log(from_agent, "EXCHANGE", {
            "to_agent": to_agent,
            "message": message,
            "decision": decision or "",
            "status_badge": status_badge,
            "confidence": confidence,
            "dollar_impact": dollar_impact,
            **({"data": str(data_passed)} if data_passed else {})
        })
        return msg

    # =========================================================================
    # FINDINGS WITH REFERENCES
    # =========================================================================

    def add_finding(self, agent: str, finding_type: str, description: str,
                   reference: str, impact: str, severity: str = "info") -> Finding:
        """
        Add a finding with exact reference.

        Reference format examples:
        - "Healthpoint.xlsx:ag-grid:Row45:ColB" (specific cell)
        - "Healthpoint.xlsx:ag-grid:Headers:A1-Z1" (header row)
        - "All Files:Duplicate Analysis:Key=date+vendor+language" (cross-file)
        - "Statistical Analysis:Z-Score>3.0" (computed finding)
        """
        finding = Finding(
            agent=agent,
            finding_type=finding_type,
            description=description,
            reference=reference,
            impact=impact,
            severity=severity
        )
        self.findings.append(finding)

        # Also log as activity
        self.log(agent, f"FINDING: {finding_type}", {
            "description": description,
            "reference": reference,
            "impact": impact,
            "severity": severity
        })

        return finding

    def get_findings_by_severity(self, severity: str) -> List[Finding]:
        """Get all findings of a specific severity."""
        return [f for f in self.findings if f.severity == severity]

    def get_findings_by_agent(self, agent: str) -> List[Finding]:
        """Get all findings from a specific agent."""
        return [f for f in self.findings if f.agent == agent]

    # =========================================================================
    # IMPACT TRACKING
    # =========================================================================

    def track_impact(self, name: str, value: Any, delta: Any = None,
                    direction: str = "neutral", description: str = ""):
        """Track an impact metric for baseline creation."""
        metric = ImpactMetric(
            name=name,
            value=value,
            delta=delta,
            direction=direction,
            description=description
        )
        self.impact_metrics[name] = metric
        return metric

    def get_impact_summary(self) -> Dict[str, Dict]:
        """Get all impact metrics as a summary."""
        return {name: metric.to_dict() for name, metric in self.impact_metrics.items()}

    # =========================================================================
    # PIPELINE STAGE TRACKING
    # =========================================================================

    def start_stage(self, stage_name: str, agent: str):
        """Mark the start of a pipeline stage."""
        stage = {
            "name": stage_name,
            "agent": agent,
            "start_time": datetime.datetime.now().isoformat(),
            "end_time": None,
            "status": "in_progress",
            "metrics": {}
        }
        self.pipeline_stages.append(stage)
        return len(self.pipeline_stages) - 1  # Return stage index

    def complete_stage(self, stage_index: int, status: str = "complete",
                       metrics: Dict[str, Any] = None):
        """Mark the completion of a pipeline stage."""
        if 0 <= stage_index < len(self.pipeline_stages):
            self.pipeline_stages[stage_index]["end_time"] = datetime.datetime.now().isoformat()
            self.pipeline_stages[stage_index]["status"] = status
            if metrics:
                self.pipeline_stages[stage_index]["metrics"].update(metrics)

    # =========================================================================
    # REPORT GENERATION
    # =========================================================================

    def generate_report(self) -> str:
        """Generate a comprehensive markdown report for consultant review."""
        end_time = datetime.datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        report = []
        report.append("# AGENT PIPELINE ACTIVITY LOG")
        report.append(f"\n**Processing Date:** {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**Duration:** {duration:.1f} seconds")
        report.append("\n---\n")

        # Impact Summary
        if self.impact_metrics:
            report.append("## BASELINE IMPACT SUMMARY\n")
            report.append("| Metric | Value | Change | Direction |")
            report.append("|--------|-------|--------|-----------|")
            for name, metric in self.impact_metrics.items():
                direction_icon = {"positive": "📈", "negative": "📉", "neutral": "➡️"}.get(metric.direction, "")
                delta_str = str(metric.delta) if metric.delta else "-"
                report.append(f"| {name} | {metric.value} | {delta_str} | {direction_icon} {metric.direction} |")
            report.append("\n---\n")

        # Agent Summaries
        report.append("## AGENT SUMMARY\n")
        report.append("| Agent | Key Metric | Status |")
        report.append("|-------|------------|--------|")

        for agent, summary in self.agent_summaries.items():
            metric = summary.get("key_metric", "N/A")
            status = summary.get("status", "OK")
            status_icon = "✅ OK" if status == "OK" else "⚠️ ISSUE"
            report.append(f"| {agent} | {metric} | {status_icon} |")

        report.append("\n---\n")

        # Findings with References
        if self.findings:
            report.append("## FINDINGS WITH REFERENCES\n")

            # Group by severity
            for severity in ["critical", "warning", "info", "success"]:
                findings = self.get_findings_by_severity(severity)
                if findings:
                    severity_icon = {"critical": "🚨", "warning": "⚠️", "info": "ℹ️", "success": "✅"}.get(severity, "")
                    report.append(f"\n### {severity_icon} {severity.upper()} Findings\n")

                    for f in findings:
                        report.append(f"**{f.finding_type}** ({f.agent})")
                        report.append(f"- Description: {f.description}")
                        report.append(f"- 📍 Reference: `{f.reference}`")
                        report.append(f"- Impact: {f.impact}")
                        report.append("")

            report.append("\n---\n")

        # Agent Communications Timeline
        if self.messages:
            report.append("## AGENT COMMUNICATIONS TIMELINE\n")

            for msg in self.messages:
                time_str = msg.timestamp.split("T")[1][:8] if "T" in msg.timestamp else msg.timestamp
                to_str = f" → **{msg.to_agent}**" if msg.to_agent else ""
                type_icon = {
                    "handoff": "🤝",
                    "success": "✅",
                    "alert": "⚠️",
                    "finding": "🔍",
                    "status": "💬"
                }.get(msg.message_type, "")

                report.append(f"**[{time_str}]** {type_icon} **{msg.agent}**{to_str}")
                report.append(f"> {msg.message}")

                if msg.findings:
                    for f in msg.findings:
                        report.append(f"  - 📍 `{f.reference}`: {f.description}")

                report.append("")

            report.append("\n---\n")

        # Detailed Activity Log (legacy format)
        report.append("## DETAILED ACTIVITY LOG\n")

        current_agent = None
        for activity in self.activities:
            agent = activity["agent"]
            if agent != current_agent:
                report.append(f"\n### {agent}\n")
                current_agent = agent

            action = activity["action"]
            details = activity["details"]

            if details:
                detail_str = ", ".join([f"{k}: {v}" for k, v in details.items()])
                report.append(f"- **{action}**: {detail_str}")
            else:
                report.append(f"- {action}")

        report.append("\n---\n")

        # Issues Section (from summaries)
        report.append("## ISSUES DETECTED\n")

        issues_found = False
        for agent, summary in self.agent_summaries.items():
            if "issues" in summary and summary["issues"]:
                issues_found = True
                report.append(f"\n### {agent} Issues:\n")
                for issue in summary["issues"]:
                    report.append(f"- {issue}")

        if not issues_found:
            report.append("No critical issues detected.\n")

        return "\n".join(report)

    def save_report(self, filepath: str):
        """Save the report to a file."""
        report = self.generate_report()
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Activity log saved to: {filepath}")

    def export_json(self, filepath: str):
        """Export all data as JSON for programmatic access."""
        data = {
            "start_time": self.start_time.isoformat(),
            "duration_seconds": (datetime.datetime.now() - self.start_time).total_seconds(),
            "impact_metrics": self.get_impact_summary(),
            "agent_summaries": self.agent_summaries,
            "findings": [f.to_dict() for f in self.findings],
            "messages": [m.to_dict() for m in self.messages],
            "pipeline_stages": self.pipeline_stages,
            "activities": self.activities
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        print(f"Activity data exported to: {filepath}")


# Global logger instance
_enhanced_logger: Optional[EnhancedActivityLogger] = None


def get_enhanced_logger() -> EnhancedActivityLogger:
    """Get the global enhanced logger instance."""
    global _enhanced_logger
    if _enhanced_logger is None:
        _enhanced_logger = EnhancedActivityLogger()
    return _enhanced_logger


def reset_enhanced_logger() -> EnhancedActivityLogger:
    """Reset the logger for a new run."""
    global _enhanced_logger
    _enhanced_logger = EnhancedActivityLogger()
    return _enhanced_logger
