from __future__ import annotations

import json

import streamlit as st

from engine.calculations import summarize_risk
from engine.models import BIAProject, Dependency, Impact, Process


STEPS = [
    "Welcome",
    "Organization",
    "Processes",
    "Dependencies",
    "Impacts",
    "Review/Export",
]


def render_welcome(project: BIAProject) -> None:
    st.header("Guided Business Impact Analysis")
    st.write(
        "Use the sidebar to move through each step. Your progress is held in session "
        "state and can be saved to JSON from the Review/Export step."
    )
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
        st.success(f"Added process: {name}")

    if project.processes:
        st.subheader("Current processes")
        for idx, proc in enumerate(project.processes, start=1):
            st.markdown(f"{idx}. **{proc.name}** — owner: {proc.owner or 'N/A'}")


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
                proc.dependencies.append(
                    Dependency(name=dep_name, category=dep_category, criticality=dep_criticality)
                )
                st.success(f"Added dependency to {selected_process}")
                break

    for proc in project.processes:
        if proc.dependencies:
            st.markdown(f"**{proc.name}** dependencies")
            for d in proc.dependencies:
                st.write(f"- {d.name} ({d.category}) criticality: {d.criticality}")


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
            st.success(f"Updated impact for {process_name}")
        else:
            project.impacts.append(
                Impact(
                    process_name=process_name,
                    financial_score=financial,
                    operational_score=operational,
                    reputational_score=reputational,
                )
            )
            st.success(f"Added impact for {process_name}")

    if project.impacts:
        st.subheader("Impact register")
        for impact in project.impacts:
            st.write(
                f"- {impact.process_name}: financial {impact.financial_score}, "
                f"operational {impact.operational_score}, reputational {impact.reputational_score}"
            )


def render_review_export(project: BIAProject) -> None:
    st.header("Review / Export")
    summary = summarize_risk(project)
    st.metric("Processes", summary.get("process_count", 0))
    st.metric("Average impact score", f"{summary.get('average_score', 0):.2f}")

    st.subheader("Project JSON preview")
    st.code(json.dumps(project.to_dict(), indent=2), language="json")
