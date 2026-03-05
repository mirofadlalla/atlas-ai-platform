# Atlas AI Monitoring & Observability

This directory manages Prometheus metric scraping, container health, and interactive Grafana dashboards.

## Stack Overview

- **Prometheus** (`prometheus.yml`): Configured to scrape `/metrics` from the FastAPI backend at `host.docker.internal:8000`.
- **Grafana Dashboards**: Included via `.json` representations of charts and panels. Automatically provisioned via the `provisioning/` folder to the local grafana container.

## Grafana Dashboard: `atlas-monitoring.json`

The central dashboard visualizes critical KPIs of the system in real-time.

1. **System Health**: RAM usage, System CPU (0-100%), Memory, Disk constraints.
2. **API Traffic**: Overall rates per second, endpoint split, HTTP code breakdown, latency percentiles (`p95`, `p99`).
3. **LLM Consumption**: Tokens Generated, Tokens Consumed, Cost (USD), API calls separated by model (`Qwen2.5-1.5B`).
4. **Agent Analytics**: Average step count per LangGraph query, Sub-questions parsed, Agent reasoning latency.
5. **RAG Insights**: Vector DB performance, Retrieved Chunk hit counts, LLM Cache Hit Rate (`RedisSemanticCache`).

### Extending Dashboards

New counters and gauges must be registered inside `app/core/monitors.py` first, then incremented during the FastAPI route logic.

Run `python update_dashboard.py` (or manually edit local Grafana and export the new JSON overlay to replace the file).
