from __future__ import annotations

from engine.models import BIAProject, Impact


def calculate_process_priority(impact: Impact) -> float:
    """Return a placeholder weighted score for one process."""
    # TODO: Replace with configurable weighting model.
    return (impact.financial_score * 0.4) + (impact.operational_score * 0.4) + (impact.reputational_score * 0.2)


def summarize_risk(project: BIAProject) -> dict:
    """Generate simple aggregate metrics used by Review step."""
    # TODO: Add richer analytics (RTO/RPO, dependency-adjusted impact, scenarios).
    if not project.impacts:
        return {"process_count": len(project.processes), "average_score": 0.0}

    scores = [calculate_process_priority(i) for i in project.impacts]
    return {
        "process_count": len(project.processes),
        "average_score": sum(scores) / len(scores),
        "max_score": max(scores),
    }
