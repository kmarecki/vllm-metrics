# Research: Dashboard Technology for vLLM Metrics

## Decision: Streamlit

**Chosen:** Streamlit (Python, reactive web framework)

### Rationale

| Approach | Pros | Cons | Verdict |
|----------|------|------|---------|
| **Streamlit** | Python-native, minimal boilerplate, built-in charts + Plotly integration, easy to add as subcommand | Requires ~80MB install, not suitable for multi-user web serving | ✅ **Chosen** |
| Grafana | Production-grade, alerting, rich dashboard ecosystem | Requires Grafana server + SQLite datasource plugin, more infra | ❌ Overkill for single-user local dashboard |
| Static HTML + FastAPI | Lightweight, no third-party runtime | More boilerplate, need to build chart rendering + API layer | ❌ More code for same outcome |

### Constitution Alignment

- **Minimal Dependencies**: Core (scrape/daemon) has NO streamlit dependency — only the `dashboard` subcommand imports it. Fails gracefully with import error.
- **Transparency**: All queries match the report command's logic. Calculations documented inline.

### Dependencies (optional — dashboard only)

- `streamlit` — web framework
- `plotly` — interactive charts (streamlit ships with altair but plotly is more flexible)
- Both are pip-installable, documented as optional in README

### Risks

- Streamlit launches a local web server on a random port — must document port discovery
- No session isolation — only one user can view at a time
