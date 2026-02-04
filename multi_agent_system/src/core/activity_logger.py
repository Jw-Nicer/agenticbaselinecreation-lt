
"""
Agent Activity Logger
Tracks what each agent does and generates a report for boss visibility.
"""

import datetime
from typing import List, Dict, Any

class AgentActivityLogger:
    """
    Centralized logger that captures agent activities for transparency.
    Each agent reports what it did, and this generates a boss-friendly report.
    """
    
    def __init__(self):
        self.start_time = datetime.datetime.now()
        self.activities = []
        self.agent_summaries = {}
    
    def log(self, agent_name: str, action: str, details: Dict[str, Any] = None):
        """Log an agent activity."""
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
    
    def generate_report(self) -> str:
        """Generate a markdown report for boss review."""
        end_time = datetime.datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        report = []
        report.append("# AGENT PIPELINE ACTIVITY LOG")
        report.append(f"\n**Processing Date:** {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**Duration:** {duration:.1f} seconds")
        report.append("\n---\n")
        
        # Agent Summaries
        report.append("## AGENT SUMMARY\n")
        report.append("| Agent | Key Metric | Status |")
        report.append("|-------|------------|--------|")
        
        for agent, summary in self.agent_summaries.items():
            metric = summary.get("key_metric", "N/A")
            status = summary.get("status", "OK")
            status_icon = "OK" if status == "OK" else "ISSUE"
            report.append(f"| {agent} | {metric} | {status_icon} |")
        
        report.append("\n---\n")
        
        # Detailed Activity Log
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
        
        # Issues Section
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


# Global logger instance
_logger = None

def get_logger() -> AgentActivityLogger:
    """Get the global logger instance."""
    global _logger
    if _logger is None:
        _logger = AgentActivityLogger()
    return _logger

def reset_logger():
    """Reset the logger for a new run."""
    global _logger
    _logger = AgentActivityLogger()
    return _logger
