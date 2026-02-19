# BIA App (Streamlit)

A minimal Streamlit application for a guided Business Impact Analysis (BIA) workflow, including:
- Product prioritization with simplified fuzzy BWM-TOPSIS
- Physical asset criticality with PARAM-style fuzzy likelihood/impact scoring

## Steps

- Welcome
- Organization
- Processes
- Dependencies
- Impacts
- Assets
- Asset Risk (PARAM)
- Prioritization (Fuzzy BWM-TOPSIS)
- Review / Export

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The app persists data in memory via `st.session_state` and can save/load JSON at `data/project.json`.
