# Trading Insights Application — Release 1 PRD (Data & Alerts MVP)

### TL;DR

A single-user, self-hosted web app that connects to the Schwab brokerage API to stream real-time futures, indices, and market internals, store historical data, and generate actionable alerts. Release 1 delivers in-app, sound, and Slack alerts plus full alert logging with a minimal dashboard—optimized for sub‑second signal-to-alert latency. Target user is a day trader (initially just the owner) with an eye to future SaaS expansion.

---

## Goals

### Business Goals

* Ship a reliable MVP that proves end-to-end data→alert→review, enabling future strategy detection (R1.5) and SaaS paths (R2/R3).

* Establish technical foundations: modular ingestion, alert engine, and logs for maintainability and later multitenancy.

* Demonstrate performance targets in live hours: sub‑second alerting and 99% uptime during US market hours.

* Validate a repeatable workflow by reducing missed trades and capturing a complete alert audit trail.

### User Goals

* See real-time status of watched instruments (futures, indices, internals) with confidence.

* Configure simple, reliable alert rules and receive them instantly in preferred channels (app, sound, Slack).

* Review what fired and why via complete logs to refine setups later.

* Keep setup light: single-user, LAB-hosted, minimal UI.

### Non-Goals

* No order execution, advanced charting, or multi-user support in R1.

* No strategy detection/backtesting beyond basic rule triggers (reserved for R1.5).

* No options data/alerts until later releases (SPX in R2; equities in R3).

---

## User Stories

**Persona:** Single-User Trader (also Admin)

* As a trader, I want to connect my Schwab API keys so the app can stream and store data.

* As a trader, I want to create a watchlist (ES, NQ, YM, CL, GC; SPX, NDX, RUT; VIX, TICK, ADD, TRIN) so I can focus on relevant instruments.

* As a trader, I want to define threshold and level-based rules (price/volume/internals) so I’m alerted to key intraday conditions.

* As a trader, I want alerts delivered via in-app, sound, and Slack so I don’t miss signals.

* As a trader, I want a live feed of triggered alerts and a searchable log so I can review performance.

* As an admin, I want basic health indicators (ingestion status, last tick time) so I can detect issues.

---

## Functional Requirements

* **Data Integration (Priority: P0)**

  * Connect to Schwab brokerage API for streaming and historical data.

  * Instruments: Futures (ES, NQ, YM, CL, GC); Indices (SPX, NDX, RUT); Indicators (VIX, TICK, ADD, TRIN).

  * Historical storage: daily + intraday; retention configurable.

* **Alerts (Priority: P0)**

  * Rule types: static thresholds, crossover/level hits, basic rate-of-change; scope by instrument/timeframe.

  * Delivery: in-app notifications, sound notifications, Slack (channel or DM).

  * Logging: persist alert context (rule, timestamp, instrument, value, channel delivery status).

* **User Interface (Priority: P0)**

  * Minimal dashboard: real-time watchlist status, recent alerts list, basic health.

  * Rule management: create/edit/enable/disable rules; per-instrument targeting.

  * Settings: API credentials, Slack connect, data retention, sound toggle.

  * *Secrets Wallet: Connect to Google Cloud Secret Manager (preferred) to store Schwab API keys and Slack tokens; show connection status and last rotation date.*

  * (Optional) Mobile-friendly layout.

  * *Secret Rotation: Toggle to enable/disable automatic rotation and set interval when enabled; manual “Rotate now” button always available. Default: OFF for Release 1.*

**Out of Scope (R1):** order execution, advanced charting/visualizations, multi-user.

---

## User Experience

### Entry Point & First-Time User Experience

* Launch local web UI. Guided setup asks for Schwab keys, Slack connect, and selects starter instruments.

* Test connections and show ingestion health; pre-create sample rules the user can toggle.

### Core Experience

1. **Monitor dashboard:** Live tiles for each watched instrument; show last tick time/price, internals summary. If ingestion stalls, warn and link to diagnostics.

2. **Create/edit a rule:** Start from instrument detail (e.g., ES price crosses level; TICK exceeds threshold). Validate input; show estimated firing example from recent data.

3. **Receive alerts:** Channels per user config (in-app, sound, Slack). Payload includes instrument, condition, values, timestamp. One-tap acknowledge and link to details/log.

4. **Review alerts:** Alerts tab with filters by time, instrument, rule; export CSV for analysis.

5. **Manage settings:** Rotate keys, update Slack/channel, toggle sound, adjust retention.

### Advanced Features & Edge Cases

* API rate-limit: degrade gracefully—reduce refresh frequency, queue rule checks, warn user.

* Connectivity loss: buffer events, auto-reconnect, show degraded state, send recovery notice.

* Duplicate-alert suppression per rule; retries/status per delivery channel.

### UI/UX Highlights

* High-contrast, latency-conscious UI. Subtle, distinct sound cues. Non-blocking toasts. Fully keyboard accessible.

---

## Narrative

On a volatile open, the trader starts the app on LAB. The dashboard shows ES, NQ, and market internals updating smoothly. A pre-set rule for “NYSE TICK > +900” fires; an in-app toast pops, a short chime plays, and a Slack DM appears with context. Moments later, ES tags a key level; a second alert routes to a Slack channel watched on mobile. After the morning move, the trader opens the Alerts tab, filters by instrument, and exports the log to review which signals led to actionable entries. Latency stayed below a second and no alerts were missed. With confidence in data→alert→review, the trader tweaks thresholds and prepares to layer in strategy detection next release.

---

## Success Metrics

### User-Centric Metrics

### Business Metrics

### Technical Metrics

### Tracking Plan

* Events: app_start, api_connect_success/fail, tick_ingested, rule_created, rule_fired, alert_sent\_{app|sound|slack}, alert_acknowledged, ingestion_gap_detected, recovery_complete, export_performed.

---

## Technical Considerations

### Technical Needs

* Components: Data ingestion; alert evaluation engine; time-series and alert log store; web UI; notification layers; credentials vault.

* Data model: Instruments, rules, events, alerts, deliveries.

### Integration Points

* Schwab brokerage API.

* Slack OAuth and Web API.

* Local sound subsystem.

* Google Cloud Secret Manager (GCSM) for credential storage and rotation.

### Data Storage & Privacy

* Credentials Handling: Store Schwab API keys and Slack OAuth tokens exclusively in Google Cloud Secret Manager (GCSM). LAB hosts authenticate to GCSM using a dedicated service account key stored locally once at install, scoped by least privilege. Secrets are encrypted at rest by Google-managed keys and transmitted over TLS; the app retrieves secrets at boot and caches them in memory only. No credentials are persisted in app databases or logs.

  * **Rotation:** Optional. Provide an enable/disable toggle. When enabled, allow user-configured interval (e.g., 30/60/90 days) and a manual “Rotate now” action; default is disabled.

  * Offline fallback: OS keyring or an encrypted .env file (temporary) with a migration prompt back to GCSM when connectivity returns.

* Encrypt API keys at rest, limit to localhost access. Store alert logs and metadata. No PII collection.

* For Release 1, automatic rotation remains disabled by default; only manual “Rotate now” is exposed.

### Scalability & Performance

* Single-user, now; services stateless and message-queue-ready for future horizontal scaling. Target sub‑second evaluation for typical watchlist sizes.


---

## Milestones & Sequencing


**Release Scope:** MVP R1, single-user

### Suggested Phases

**Phase 1: Core Data and Alert MVP**

* Schwab data ingestion (real-time/historical)

* Alert engine with sub-second latency

* In-app/slack/sound notification delivery

* Rule creation/edit/delete UI

* Basic health/status indicators

* Logging and alert review UI

**Phase 2: Controls and Security**

* API/Slack key rotation flows

* Secrets wallet integration (GCSM) with optional auto-rotation (default OFF), manual rotate, and UI status.

* Data retention/cleanup controls

* Accessibility and resilience (buffering, reconnect, throttle)

* *Implement manual rotate and status; leave auto-rotation toggle hidden or default OFF for R1.*

---

## Roadmap Context

* **R1.5:** Attach outcomes to alerts (strategy detection).

* **R2:** Add SPX options alerts/data.

* **R3:** Add equity options, SaaS multi-user path.

---

## Assumptions & Dependencies

* Schwab Open API availability and terms

* Slack API/OAuth & app registration

* Stable outbound internet from LAB device

* Google Cloud project with Secret Manager enabled and service account provisioned with Secret Manager Secret Accessor role.

* LAB environment permits outbound HTTPS to Google Cloud APIs (confirmed).