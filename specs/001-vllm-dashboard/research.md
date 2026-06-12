# Research: Dashboard Technology for vLLM Metrics

## Decision: Streamlit

**Chosen:** Streamlit (Python, reactive web framework)

### Rationale

| Approach | Pros | Cons | Verdict |
|----------|------|------|---------|
| **Streamlit** | Python-native, minimal boilerplate, built-in charts + Plotly integration, easy to add as subcommand | Requires ~80MB install. No built-in auth/roles. Single-process — concurrent users share one Python runtime. | ✅ **Chosen** |
| Grafana | Production-grade, alerting, rich auth, multi-user, persistent dashboards | Requires Grafana server + SQLite datasource plugin, more infra | ❌ Overkill for local/ops dashboard; Grafana is better for org-wide deployments |
| Static HTML + FastAPI | Lightweight, no third-party runtime | More boilerplate, need to build chart rendering + API layer | ❌ More code for same outcome |

### Multi-User & Public Access

Streamlit **can** serve multiple concurrent users and **can** be exposed on a public IP behind a reverse proxy. However:

- No built-in authentication — an auth proxy (oauth2-proxy, nginx basic auth, Cloudflare Access) is required for public exposure, same as any unauthenticated web app.
- Single-process Python runtime means heavy queries by one user block all others. For an ops dashboard with 1-5 users viewing cached metrics, this is negligible.
- Grafana would be the right choice if this becomes an org-wide deployment with roles, alerting, and dashboard-sharing requirements.

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
