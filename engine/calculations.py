from __future__ import annotations

from math import sqrt

from engine.models import BIAProject, DecisionMatrix, Impact, TriangularFuzzyNumber


# --- Existing BIA placeholders ---
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


# --- Fuzzy arithmetic utilities ---
def fuzzy_add(a: TriangularFuzzyNumber, b: TriangularFuzzyNumber) -> TriangularFuzzyNumber:
    return TriangularFuzzyNumber(a.lower + b.lower, a.middle + b.middle, a.upper + b.upper)


def fuzzy_multiply(a: TriangularFuzzyNumber, b: TriangularFuzzyNumber) -> TriangularFuzzyNumber:
    # Assumes non-negative TFNs for simplified product prioritization.
    return TriangularFuzzyNumber(a.lower * b.lower, a.middle * b.middle, a.upper * b.upper)


def defuzzify(a: TriangularFuzzyNumber) -> float:
    """Centroid defuzzification."""
    return (a.lower + a.middle + a.upper) / 3.0


def fuzzy_distance(a: TriangularFuzzyNumber, b: TriangularFuzzyNumber) -> float:
    """Vertex distance between two TFNs."""
    return sqrt(((a.lower - b.lower) ** 2 + (a.middle - b.middle) ** 2 + (a.upper - b.upper) ** 2) / 3.0)


# --- Fuzzy BWM placeholder ---
def calculate_fuzzy_bwm_weights(best_to_others: list[TriangularFuzzyNumber]) -> list[float]:
    """
    Simplified structured placeholder for fuzzy BWM-derived weights.

    Args:
        best_to_others: Pairwise fuzzy preferences from best criterion to each criterion.

    Returns:
        Normalized crisp weights.
    """
    # TODO: Replace with full optimization-based fuzzy BWM solver.
    if not best_to_others:
        return []

    inverted = []
    for pref in best_to_others:
        crisp = max(defuzzify(pref), 1e-9)
        inverted.append(1.0 / crisp)

    total = sum(inverted)
    return [value / total for value in inverted]


# --- Fuzzy TOPSIS ---
def normalize_decision_matrix(matrix: DecisionMatrix) -> list[list[TriangularFuzzyNumber]]:
    if not matrix.products or not matrix.criteria:
        return []

    normalized: list[list[TriangularFuzzyNumber]] = []
    for i, _ in enumerate(matrix.products):
        row: list[TriangularFuzzyNumber] = []
        for j, criterion in enumerate(matrix.criteria):
            cell = matrix.evaluations[i][j]
            col = [matrix.evaluations[r][j] for r in range(len(matrix.products))]

            if criterion.criterion_type == "cost":
                min_l = min(c.lower for c in col)
                row.append(
                    TriangularFuzzyNumber(
                        lower=min_l / max(cell.upper, 1e-9),
                        middle=min_l / max(cell.middle, 1e-9),
                        upper=min_l / max(cell.lower, 1e-9),
                    )
                )
            else:
                max_u = max(c.upper for c in col)
                row.append(
                    TriangularFuzzyNumber(
                        lower=cell.lower / max(max_u, 1e-9),
                        middle=cell.middle / max(max_u, 1e-9),
                        upper=cell.upper / max(max_u, 1e-9),
                    )
                )
        normalized.append(row)

    return normalized


def compute_weighted_matrix(
    normalized_matrix: list[list[TriangularFuzzyNumber]], weights: list[float]
) -> list[list[TriangularFuzzyNumber]]:
    weighted: list[list[TriangularFuzzyNumber]] = []
    for row in normalized_matrix:
        weighted_row = []
        for j, cell in enumerate(row):
            w = TriangularFuzzyNumber(weights[j], weights[j], weights[j])
            weighted_row.append(fuzzy_multiply(cell, w))
        weighted.append(weighted_row)
    return weighted


def determine_fpis_fnis(
    weighted_matrix: list[list[TriangularFuzzyNumber]],
) -> tuple[list[TriangularFuzzyNumber], list[TriangularFuzzyNumber]]:
    if not weighted_matrix:
        return [], []

    cols = len(weighted_matrix[0])
    fpis: list[TriangularFuzzyNumber] = []
    fnis: list[TriangularFuzzyNumber] = []

    for j in range(cols):
        col = [weighted_matrix[i][j] for i in range(len(weighted_matrix))]
        fpis.append(
            TriangularFuzzyNumber(
                lower=max(c.lower for c in col),
                middle=max(c.middle for c in col),
                upper=max(c.upper for c in col),
            )
        )
        fnis.append(
            TriangularFuzzyNumber(
                lower=min(c.lower for c in col),
                middle=min(c.middle for c in col),
                upper=min(c.upper for c in col),
            )
        )

    return fpis, fnis


def calculate_closeness_coefficients(
    weighted_matrix: list[list[TriangularFuzzyNumber]],
    fpis: list[TriangularFuzzyNumber],
    fnis: list[TriangularFuzzyNumber],
) -> list[float]:
    coefficients: list[float] = []
    for row in weighted_matrix:
        d_pos = sum(fuzzy_distance(cell, fpis[j]) for j, cell in enumerate(row))
        d_neg = sum(fuzzy_distance(cell, fnis[j]) for j, cell in enumerate(row))
        cc = d_neg / max(d_neg + d_pos, 1e-9)
        coefficients.append(cc)
    return coefficients


def rank_products_fuzzy_topsis(matrix: DecisionMatrix, weights: list[float]) -> list[dict]:
    if not matrix.products or not matrix.criteria or not matrix.evaluations:
        return []

    normalized = normalize_decision_matrix(matrix)
    weighted = compute_weighted_matrix(normalized, weights)
    fpis, fnis = determine_fpis_fnis(weighted)
    closeness = calculate_closeness_coefficients(weighted, fpis, fnis)

    ranked = [
        {"product": matrix.products[i].name, "closeness": closeness[i]} for i in range(len(matrix.products))
    ]
    ranked.sort(key=lambda x: x["closeness"], reverse=True)
    return ranked
