from __future__ import annotations

import json

import streamlit as st

from engine.calculations import (
    calculate_fuzzy_bwm_weights,
    compute_param_scores,
    rank_products_fuzzy_topsis,
    summarize_risk,
)
from engine.models import (
    Asset,
    BIAProject,
    Criterion,
    DecisionMatrix,
    Dependency,
    Impact,
    ImpactInputs,
    LikelihoodInputs,
    Process,
    Product,
    TriangularFuzzyNumber,
)


STEPS = [
    "Welcome",
    "Organization",
    "Processes",
    "Dependencies",
    "Impacts",
    "Assets",
    "Asset Risk (PARAM)",
    "Prioritization",
    "Review/Export",
]


def render_welcome(project: BIAProject) -> None:
    st.header("Guided Business Impact Analysis")
    st.write("Use the sidebar to move through each step.")
    project.title = st.text_input("Project title", value=project.title)


def render_organization(project: BIAProject) -> None:
    st.header("Organization")
    with st.form("organization_form"):
        project.organization.name = st.text_input("Organization name", value=project.organization.name)
        project.organization.industry = st.text_input("Industry", value=project.organization.industry)
        project.organization.headquarters = st.text_input("Headquarters", value=project.organization.headquarters)
        submitted = st.form_submit_button("Save organization")
    if submitted:
        st.success("Organization details saved")


def render_processes(project: BIAProject) -> None:
    st.header("Processes")
    with st.form("process_form"):
        name = st.text_input("Process name")
        owner = st.text_input("Owner")
        description = st.text_area("Description")
        submitted = st.form_submit_button("Add process")
    if submitted and name:
        project.processes.append(Process(name=name, owner=owner, description=description))


def render_dependencies(project: BIAProject) -> None:
    st.header("Dependencies")
    if not project.processes:
        st.info("Add at least one process first.")
        return
    process_names = [p.name for p in project.processes]
    with st.form("dependency_form"):
        selected_process = st.selectbox("Process", process_names)
        dep_name = st.text_input("Dependency name")
        dep_category = st.selectbox("Category", ["Internal", "Vendor", "Technology", "Facility"])
        dep_criticality = st.slider("Criticality (1-5)", 1, 5, 3)
        submitted = st.form_submit_button("Add dependency")
    if submitted and dep_name:
        for proc in project.processes:
            if proc.name == selected_process:
                proc.dependencies.append(Dependency(name=dep_name, category=dep_category, criticality=dep_criticality))
                break


def render_impacts(project: BIAProject) -> None:
    st.header("Impacts")
    if not project.processes:
        st.info("Add at least one process first.")
        return
    process_names = [p.name for p in project.processes]
    with st.form("impact_form"):
        process_name = st.selectbox("Process", process_names)
        financial = st.slider("Financial impact (1-5)", 1, 5, 2)
        operational = st.slider("Operational impact (1-5)", 1, 5, 2)
        reputational = st.slider("Reputational impact (1-5)", 1, 5, 2)
        submitted = st.form_submit_button("Save impact")
    if submitted:
        existing = next((i for i in project.impacts if i.process_name == process_name), None)
        if existing:
            existing.financial_score = financial
            existing.operational_score = operational
            existing.reputational_score = reputational
        else:
            project.impacts.append(
                Impact(
                    process_name=process_name,
                    financial_score=financial,
                    operational_score=operational,
                    reputational_score=reputational,
                )
            )


def render_assets(project: BIAProject) -> None:
    st.header("Assets")
    with st.form("asset_form"):
        name = st.text_input("Asset name")
        category = st.selectbox("Asset category", ["Facility", "Equipment", "IT", "People", "Utility"])
        owner = st.text_input("Asset owner")
        submitted = st.form_submit_button("Add asset")
    if submitted and name:
        project.assets.append(Asset(name=name, category=category, owner=owner))
        if name not in project.likelihood_inputs:
            project.likelihood_inputs[name] = LikelihoodInputs(
                dpf=TriangularFuzzyNumber(1, 1, 1),
                ddf=TriangularFuzzyNumber(1, 1, 1),
                ucf=TriangularFuzzyNumber(1, 1, 1),
                def_=TriangularFuzzyNumber(1, 1, 1),
            )
        if name not in project.impact_inputs:
            project.impact_inputs[name] = ImpactInputs(
                sf=TriangularFuzzyNumber(1, 1, 1),
                pf=TriangularFuzzyNumber(1, 1, 1),
                rc=TriangularFuzzyNumber(1, 1, 1),
                ls=TriangularFuzzyNumber(1, 1, 1),
            )

    if project.assets:
        st.subheader("Registered assets")
        for a in project.assets:
            st.write(f"- {a.name} ({a.category}) owner: {a.owner or 'N/A'}")


def _tfn_editor(prefix: str, base_key: str, value: TriangularFuzzyNumber) -> TriangularFuzzyNumber:
    c1, c2, c3 = st.columns(3)
    with c1:
        l = st.number_input(f"{prefix} l", min_value=0.0, value=float(value.lower), key=f"{base_key}_l")
    with c2:
        m = st.number_input(f"{prefix} m", min_value=0.0, value=float(value.middle), key=f"{base_key}_m")
    with c3:
        u = st.number_input(f"{prefix} u", min_value=0.0, value=float(value.upper), key=f"{base_key}_u")
    return TriangularFuzzyNumber(l, max(l, m), max(max(l, m), u))


def render_asset_risk_param(project: BIAProject) -> None:
    st.header("Asset Risk (PARAM)")
    if not project.assets:
        st.info("Add assets first.")
        return

    st.subheader("Continuity thresholds")
    project.continuity_params.watch_threshold = st.number_input(
        "Watch threshold", min_value=0.0, value=float(project.continuity_params.watch_threshold)
    )
    project.continuity_params.criticality_threshold = st.number_input(
        "Critical threshold", min_value=0.0, value=float(project.continuity_params.criticality_threshold)
    )

    for asset in project.assets:
        st.markdown(f"### {asset.name}")
        lin = project.likelihood_inputs.get(asset.name, LikelihoodInputs())
        iin = project.impact_inputs.get(asset.name, ImpactInputs())

        st.markdown("Likelihood inputs")
        lin.dpf = _tfn_editor("DPF", f"{asset.name}_dpf", lin.dpf)
        lin.ddf = _tfn_editor("DDF", f"{asset.name}_ddf", lin.ddf)
        lin.ucf = _tfn_editor("UCF", f"{asset.name}_ucf", lin.ucf)
        lin.def_ = _tfn_editor("DeF", f"{asset.name}_def", lin.def_)

        st.markdown("Impact inputs")
        iin.sf = _tfn_editor("SF", f"{asset.name}_sf", iin.sf)
        iin.pf = _tfn_editor("PF", f"{asset.name}_pf", iin.pf)
        iin.rc = _tfn_editor("RC", f"{asset.name}_rc", iin.rc)
        iin.ls = _tfn_editor("LS", f"{asset.name}_ls", iin.ls)

        project.likelihood_inputs[asset.name] = lin
        project.impact_inputs[asset.name] = iin

    if st.button("Compute PARAM risk", type="primary"):
        project.risk_scores = compute_param_scores(project)

    if project.risk_scores:
        st.subheader("PARAM results")
        rows = [
            {
                "Asset": r.asset_name,
                "L": round(r.likelihood, 4),
                "I": round(r.impact, 4),
                "Critical": r.critical,
                "wpa": round(r.wpa, 4),
            }
            for r in project.risk_scores
        ]
        st.table(rows)


def _ensure_matrix_shape(dm: DecisionMatrix) -> None:
    if len(dm.evaluations) != len(dm.products):
        dm.evaluations = [[TriangularFuzzyNumber(1, 1, 1) for _ in dm.criteria] for _ in dm.products]
        return
    for i in range(len(dm.evaluations)):
        row = dm.evaluations[i]
        if len(row) < len(dm.criteria):
            row.extend(TriangularFuzzyNumber(1, 1, 1) for _ in range(len(dm.criteria) - len(row)))
        elif len(row) > len(dm.criteria):
            dm.evaluations[i] = row[: len(dm.criteria)]


def render_prioritization(project: BIAProject) -> None:
    st.header("Product Prioritization (Fuzzy BWM-TOPSIS)")
    dm = project.decision_matrix

    c1, c2 = st.columns(2)
    with c1:
        with st.form("criterion_form"):
            c_name = st.text_input("Criterion name")
            c_type = st.selectbox("Type", ["benefit", "cost"])
            add_criterion = st.form_submit_button("Add criterion")
        if add_criterion and c_name:
            dm.criteria.append(Criterion(name=c_name, criterion_type=c_type))

    with c2:
        with st.form("product_form"):
            p_name = st.text_input("Product name")
            p_desc = st.text_input("Description")
            add_product = st.form_submit_button("Add product")
        if add_product and p_name:
            dm.products.append(Product(name=p_name, description=p_desc))

    _ensure_matrix_shape(dm)

    if dm.criteria and dm.products:
        st.subheader("Fuzzy evaluations (l, m, u)")
        for i, product in enumerate(dm.products):
            st.markdown(f"**{product.name}**")
            cols = st.columns(len(dm.criteria))
            for j, criterion in enumerate(dm.criteria):
                with cols[j]:
                    current = dm.evaluations[i][j]
                    l = st.number_input(f"{criterion.name} l", min_value=0.0, value=float(current.lower), key=f"l_{i}_{j}")
                    m = st.number_input(f"{criterion.name} m", min_value=0.0, value=float(current.middle), key=f"m_{i}_{j}")
                    u = st.number_input(f"{criterion.name} u", min_value=0.0, value=float(current.upper), key=f"u_{i}_{j}")
                    dm.evaluations[i][j] = TriangularFuzzyNumber(lower=l, middle=max(l, m), upper=max(max(l, m), u))

        best_to_others: list[TriangularFuzzyNumber] = []
        for j, criterion in enumerate(dm.criteria):
            l = st.number_input(f"{criterion.name} pref l", min_value=0.1, value=1.0, key=f"bw_l_{j}")
            m = st.number_input(f"{criterion.name} pref m", min_value=0.1, value=1.0, key=f"bw_m_{j}")
            u = st.number_input(f"{criterion.name} pref u", min_value=0.1, value=1.0, key=f"bw_u_{j}")
            best_to_others.append(TriangularFuzzyNumber(l, max(l, m), max(max(l, m), u)))

        if st.button("Compute ranking", type="primary"):
            weights = calculate_fuzzy_bwm_weights(best_to_others)
            ranking = rank_products_fuzzy_topsis(dm, weights)
            st.session_state["prioritization_weights"] = weights
            st.session_state["prioritization_ranking"] = ranking

    weights = st.session_state.get("prioritization_weights", [])
    ranking = st.session_state.get("prioritization_ranking", [])
    if weights:
        for criterion, weight in zip(dm.criteria, weights):
            st.write(f"- {criterion.name}: {weight:.4f}")
    if ranking:
        for idx, row in enumerate(ranking, start=1):
            st.write(f"{idx}. {row['product']} — closeness: {row['closeness']:.4f}")


def render_review_export(project: BIAProject) -> None:
    st.header("Review / Export")
    summary = summarize_risk(project)
    st.metric("Processes", summary.get("process_count", 0))
    st.metric("Average impact score", f"{summary.get('average_score', 0):.2f}")
    st.subheader("Project JSON preview")
    st.code(json.dumps(project.to_dict(), indent=2), language="json")
