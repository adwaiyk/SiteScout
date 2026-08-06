# SiteScout — Solar & Wind Deployment Intelligence Platform
## Finalized Project Plan (v2 — Final Lock)

**Program:** Infosys Springboard Internship 2026 — AI Domain
**Duration:** 8 weeks, 4 milestones (2 weeks each)
**Repository:** github.com/adwaiyk/SiteScout
**Status:** LOCKED — do not re-derive core decisions. Update only the progress/status sections as work completes.

---

## 1. Objective

Build an AI-powered platform that recommends optimal locations for solar and wind energy deployment by analyzing environmental, geographic, climatic, infrastructure, and socio-economic factors. The platform goes beyond a standard scoring tool by helping the user genuinely *decide* between competing good options — using multi-objective optimization and explainable AI — rather than just producing a single ranked list.

**Geographic scope:** Global-capable engine, with India as the primary demo/validation region (pre-loaded dataset of 15–20 real Indian sites). Any coordinates worldwide can be analyzed; India is the flagship use case.

**Target audience:** Renewable energy companies, government agencies, utility providers, environmental organizations, infrastructure planners, sustainability consultants.

---

## 2. Core Differentiator (Centerpiece)

Standard site-scoring tools reduce site suitability to a single weighted number. This hides real trade-offs and gives no way to trust or interrogate the result.

**SiteScout's centerpiece: Multi-Objective Optimization + Explainability**

- **Multi-objective optimization (Pareto frontier)** — using NSGA-II (via `pymoo`), sites are evaluated simultaneously across competing objectives: energy output, environmental impact, and cost/infrastructure accessibility. Instead of one "best" site, the user sees the frontier of non-dominated options and the actual trade-offs between them.
- **Explainability (SHAP)** — for any site, the user can see exactly which factors drove its score up or down, turning the system from a black box into a transparent decision-support tool.

This is the primary decision-making tool of the platform. The weighted scoring model (Section 7) is a secondary, fast triage layer only — explicitly not treated as the "real" answer.

---

## 3. Full Feature List

### 3.1 Mandatory Core Modules (all included)

1. User Authentication & Role-Based Access (custom-built — see Section 6)
2. Project & Site Management — creation, registration, region management, comparison, history
3. Environmental Data Collection Engine — weather, satellite imagery, terrain, climate ingestion
4. Geographic Intelligence Engine — GIS processing, terrain mapping, infrastructure proximity
5. Solar Potential Prediction Engine
6. Wind Potential Prediction Engine
7. Site Suitability Intelligence Engine
8. Energy Forecasting Engine
9. Deployment Optimization Engine
10. Site Scoring Engine — user-adjustable weighted baseline (see Section 7)
11. Role-Based Dashboards — Planner, GIS Analyst, Project Manager, Admin
12. Notification & Alert System
13. Reports & Export System — PDF/Excel
14. Final Integration, Testing & Deployment

### 3.2 Signature Innovations

1. **Multi-Objective Optimization (Pareto Frontier)** [CENTERPIECE]
2. **SHAP-Based Explainability** [CENTERPIECE]
3. **Uncertainty-Aware Forecasting** — confidence bands, not point estimates
4. **LLM-Generated Investment Narratives** — plain-English feasibility summaries
5. **Interactive What-If Simulator** — live-recomputing sliders (panel tilt, turbine hub height, capacity, and factor weights)
6. **Land-Use Conflict Detector** — WDPA overlay, hard-flags protected/agricultural/water zones
7. **Grid Hosting Capacity Heuristic** — estimates spare capacity, not just distance
8. **Pre-Loaded India Demo Dataset** — 15–20 real, pre-scored sites for instant demo

**Explicitly deprioritized:** MLOps retraining pipelines, mobile app, OAuth2 social login, Kubernetes/advanced orchestration.

---

## 4. System Architecture

```
                        USER INTERFACES
   Web App (React/Next.js) | Dashboards | Reports | GIS Map Viewer
                                |
                    FASTAPI BACKEND (API Gateway)
   Custom JWT Auth | Routing | Validation | Rate Limiting | Logging
                                |
        ------------------------------------------------
        |         |          |            |            |
   Site/Project  Environmental  Solar/Wind   Optimization  Scoring &
   Service       Data Service   Prediction   Engine (NSGA- Explainability
                                Service      II / pymoo)   Service (SHAP)
        |         |          |            |            |
        ------------------------------------------------
                                |
                    DATA & ML LAYER
   PostgreSQL + PostGIS (Supabase, DB-only) | ML Models
   (XGBoost/LightGBM) | GeoPandas/Rasterio processing
                                |
                    EXTERNAL DATA SOURCES
   NASA POWER | Global Wind Atlas | SRTM (OpenTopography) |
   Copernicus Sentinel Hub | OSM Overpass | WDPA | OpenWeather
```

---

## 5. Tech Stack (Finalized)

| Layer | Technology | Notes |
|---|---|---|
| Backend | Python, FastAPI | |
| Frontend | React.js, Next.js, Tailwind CSS | |
| Mapping | Leaflet.js + OpenStreetMap tiles | No API key/usage risk |
| Database | PostgreSQL + PostGIS via **Supabase** | Database + Storage only |
| Auth | **Custom-built JWT auth** | Hand-rolled register/login/refresh endpoints via `passlib` (hashing) + `python-jose` (JWT). Supabase Auth explicitly NOT used — clean separation of concerns. Password reset/email verification deferred as documented future work. |
| Storage | Supabase Storage | Reports, imagery, exports |
| ML — Prediction | Scikit-learn, XGBoost, LightGBM | |
| ML — Explainability | **SHAP** | Centerpiece |
| ML — Optimization | **pymoo** (NSGA-II) | Centerpiece |
| GIS Processing | GeoPandas, Rasterio, Shapely, GDAL | |
| Visualization | Plotly, Chart.js | |
| Containerization | Docker, Docker Compose | |
| Deployment | **Render** (free tier, Dockerfile-based) | AWS excluded entirely — cost-risk |
| CI/CD | GitHub Actions | |

**Cost target: $0**, no credit card risk anywhere in the stack.

---

## 6. Authentication — Custom Implementation

Decision: build auth from scratch rather than using Supabase Auth, for full control and stronger learning value. Supabase is used purely as a Postgres+PostGIS+Storage provider.

**Endpoints:**
- `POST /auth/register` — validate input, hash password (bcrypt via passlib), insert into `users` table
- `POST /auth/login` — verify password hash, issue JWT (role claim + expiry) via python-jose
- `POST /auth/refresh` — refresh token rotation
- Middleware — verifies JWT signature/expiry on protected routes, extracts `role` claim for RBAC checks

**Deferred (documented as future work, not built in this internship cycle):** password reset flow, email verification, rate-limiting on login attempts.

### User Schema

```
users
├── id (UUID)
├── email (unique)
├── password_hash
├── full_name
├── role (enum: planner | gis_analyst | project_manager | admin)
├── organization (nullable)
├── phone (nullable)
├── created_at
├── last_login
└── is_active (boolean)
```

---

## 7. Site Suitability Scoring Model (Baseline — User-Adjustable)

This is explicitly a **fast triage tool**, not the platform's real decision mechanism (that's the Pareto/SHAP system in Section 2). Rather than fixed percentages — which are arbitrary regardless of how many factors are added — weights are **user-adjustable via sliders**, defaulting to roughly balanced starting proportions. This is honest about the fact that "suitability" depends on whose priorities are being optimized (an investor weighs cost differently than a government agency weighs environmental impact), and it pairs directly with the What-If Simulator feature.

**Factors (default starting weights, all user-adjustable):**
- Renewable Resource Availability — default 30%
- Geographic Suitability — default 20%
- Infrastructure Accessibility — default 15%
- Environmental Impact — default 15%
- Socio-Economic Viability — default 15%
  - Sub-factors: land acquisition complexity (ownership type), demand proximity, local economic impact estimate, land cost proxy (via land-use type), social acceptance risk proxy (population density near site)
- Economic/Cost Feasibility — default 5%

**Categories:** Excellent, Highly Suitable, Moderately Suitable, Low Suitability, Unsuitable

UI/docs framing: "A fast, transparent triage score — adjust weights to match your priorities. For a full trade-off view across all options, see the Optimization tab."

---

## 8. Data Sources (Production-Grade, Non-Kaggle)

| Purpose | Source | Access | License |
|---|---|---|---|
| Solar irradiance | NASA POWER API | Free, no key | Public domain |
| Solar PV screening | Global Solar Atlas | Free, API/GeoTIFF | CC BY 4.0 |
| Wind resource | Global Wind Atlas (DTU/World Bank) | Free, API/GeoTIFF | CC BY 4.0 |
| Elevation/terrain | NASA SRTM via OpenTopography | Free API | Public domain |
| Satellite imagery/NDVI | Copernicus Data Space (Sentinel Hub) | Free tier, OAuth | Copernicus license |
| Land cover baseline | ESA WorldCover | Free download | CC BY 4.0 |
| Roads/transmission/substations | OSM Overpass API | Free | ODbL |
| Power grid infrastructure | Global Energy Monitor | Free download | CC BY 4.0 |
| Protected areas | WDPA (Protected Planet/UNEP-WCMC) | Free API | Free, non-commercial |
| Near-term weather/alerts | OpenWeather API | Free tier | Commercial API terms |
| Administrative boundaries | geoBoundaries | Free download | Open |
| Population density (social acceptance proxy) | WorldPop or geoBoundaries-linked census data | Free download | Open |

---

## 9. Milestone Plan (8 Weeks, 4 Milestones)

### Milestone 1 — Weeks 1–2: Foundation & Core Setup
**Branch:** `milestone_1`
- Finalize architecture and PostGIS schema (users, projects, sites)
- Set up FastAPI + Next.js environments
- **Build custom JWT auth** (register/login/refresh/RBAC middleware)
- Project/site management CRUD workflows
- Docker + Docker Compose for local dev
- Begin ingestion: NASA POWER, OSM Overpass
- **Evaluation:** project initialized, custom auth working, site management operational, one external dataset integrated

### Milestone 2 — Weeks 3–4: Environmental Intelligence & Prediction
**Branch:** `milestone_2`
- Complete environmental data engine (SRTM, Global Wind Atlas, Sentinel Hub, WDPA, WorldPop)
- Solar + wind potential prediction models (XGBoost/LightGBM)
- GIS processing workflows (GeoPandas/Rasterio)
- Land-use conflict detector
- **Evaluation:** solar + wind engines operational, GIS analytics implemented, conflict detection functional

### Milestone 3 — Weeks 5–6: Site Intelligence & Optimization (Centerpiece)
**Branch:** `milestone_3`
- User-adjustable weighted scoring engine
- **Pareto frontier optimization (pymoo/NSGA-II)**
- **SHAP explainability integration**
- Uncertainty-aware forecasting (confidence bands)
- Grid hosting capacity heuristic
- Initial dashboards (Planner, GIS Analyst)
- **Evaluation:** optimization + SHAP functional, forecasting produces confidence ranges

### Milestone 4 — Weeks 7–8: Analytics, Polish & Deployment
**Branch:** `milestone_4`
- Complete all 4 dashboards
- Interactive what-if simulator (parameter + weight sliders, live recompute)
- LLM-generated investment narratives
- Reports & export (PDF/Excel)
- Notification/alert system
- Pre-load and validate 15–20 site India demo dataset
- Integration/security/performance testing
- Docker finalized, deploy to Render
- Final documentation and presentation prep
- **Evaluation:** fully deployed, all dashboards operational, full demo workflow demonstrable live

---

## 10. Git Workflow

- `main` — stable integration branch
- `milestone_1` through `milestone_4` — active development branches, merged into `main` at each milestone's end
- README progress table updated at each milestone close
- No submodules — flat repo structure; `.gitignore` covers Python/Node/Docker/env/GIS raw data

---

## 11. Performance & Evaluation Metrics

- **Solar:** irradiance prediction accuracy, energy generation estimation accuracy, capacity factor prediction error
- **Wind:** wind speed prediction accuracy, power estimation accuracy, seasonal forecast accuracy
- **Site selection:** suitability classification accuracy, recommendation precision, infrastructure assessment accuracy
- **Forecasting:** annual energy prediction accuracy, revenue estimation accuracy
- **System:** GIS processing latency, API response time, dashboard load speed

---

## 12. Disclaimer (for README/reports)

This is an academic, learning-oriented project built for the Infosys Springboard Internship. Prediction outputs are for screening and pre-feasibility purposes and should not be used for real-world investment or deployment decisions without independent validation.

---

*This document is the single source of truth for SiteScout. Update only the milestone status/progress sections as work completes. Core decisions (tech stack, centerpiece features, scope, auth approach) are locked — do not reopen without deliberate re-evaluation.*
