from __future__ import annotations

import streamlit as st

from engine.models import BIAProject
from engine.storage import load_project, save_project
from ui.forms import (
    STEPS,
    render_dependencies,
    render_impacts,
    render_organization,
    render_processes,
    render_review_export,
    render_welcome,
)


st.set_page_config(page_title="BIA Wizard", layout="wide")

if "project" not in st.session_state:
    st.session_state.project = load_project()
if "step" not in st.session_state:
    st.session_state.step = STEPS[0]

project: BIAProject = st.session_state.project

st.sidebar.title("BIA Workflow")
st.session_state.step = st.sidebar.radio("Navigate", STEPS, index=STEPS.index(st.session_state.step))

col1, col2 = st.columns([3, 1])
with col2:
    if st.button("Save to data/project.json", use_container_width=True):
        path = save_project(project)
        st.success(f"Saved project to {path}")

with col1:
    step = st.session_state.step
    if step == "Welcome":
        render_welcome(project)
    elif step == "Organization":
        render_organization(project)
    elif step == "Processes":
        render_processes(project)
    elif step == "Dependencies":
        render_dependencies(project)
    elif step == "Impacts":
        render_impacts(project)
    elif step == "Review/Export":
        render_review_export(project)

st.session_state.project = project
