# SiteScout

**Solar & Wind Deployment Intelligence Platform**

> Status: In Development (Infosys Springboard Internship Project)

## Overview

SiteScout is an AI-powered platform that recommends optimal locations for solar and wind energy deployment by analyzing environmental, geographic, climatic, infrastructure, and socio-economic factors. The platform combines geospatial analytics, satellite imagery, weather forecasting, terrain analysis, machine learning, multi-objective optimization, and explainable AI to estimate renewable energy generation potential, evaluate project feasibility, and support investment decision-making.

This project is being built as part of the Infosys Springboard Internship program and is currently under active development. Features, APIs, and documentation are subject to change as milestones are completed.

## Objective

To identify high-potential locations for solar and wind energy projects using data-driven site suitability scoring, resource prediction models, and deployment optimization — helping users genuinely *decide* between competing good options rather than relying on a single ranked list. Built for renewable energy companies, government agencies, utility providers, environmental organizations, infrastructure planners, and sustainability consultants.

## Current Development Status

This project is being implemented in four milestones over an eight-week timeline. Refer to the table below for progress.

| Milestone | Focus Area | Status |
|---|---|---|
| Milestone 1 (Week 1–2) | Project setup, authentication, site management, dataset integration | Completed |
| Milestone 2 (Week 3–4) | Environmental intelligence engine, solar and wind prediction models | Completed |
| Milestone 3 (Week 5–6) | Site suitability engine, deployment optimization, forecasting, dashboards | Completed |
| Milestone 4 (Week 7–8) | Analytics, testing, containerization, deployment | Not Started |

Note: This README will be updated as each milestone is completed.

### Milestone 1 — Completed

- Finalized system architecture and PostGIS database schema (users, projects, sites)
- Set up FastAPI backend and Next.js frontend environments
- Implemented custom JWT-based authentication (register, login, refresh) with role-based access control
- Built project and site management CRUD workflows
- Set up Docker and Docker Compose for local development
- Began integration of environmental datasets (NASA POWER, OSM Overpass)

### Milestone 2 — Completed

- Extended database schema with PostGIS-backed site geometry (`POINT`, SRID 4326) and scan log persistence
- Built concurrent environmental data ingestion pipelines: NASA POWER (solar irradiance, temperature, wind speed) and OSM Overpass (power line, substation, and road proximity)
- Implemented land-use conflict detection against protected zones, forests, and restricted areas
- Trained and integrated XGBoost regression models for solar and wind yield prediction (MWh/yr) and capacity factor estimation
- Added project and site analysis API routes, including full-payload scan logging
- Built the interactive GIS map scanner (Leaflet) and workspace dashboard (collapsible sidebar, project history, site persistence modal)

### Milestone 3 — Completed (Centerpiece)

- Restructured the backend into a layered architecture (`app/api/routes`, `app/services`, `app/schemas`) for maintainability going into the final milestones
- Built the **user-adjustable weighted scoring engine** — a fast triage layer where the user sets factor weights via sliders rather than fixed percentages, defaulting to a balanced starting point across all six factors (see Scoring Model below)
- Implemented the platform's centerpiece: **NSGA-II multi-objective optimization** (via `pymoo`) producing a Pareto frontier across energy output, environmental impact, and infrastructure cost — surfacing the full set of non-dominated trade-offs instead of a single "best" site
- Implemented **SHAP-based explainability**, decomposing each site's suitability score into per-factor contributions so users can see exactly why a site scored the way it did
- Built **uncertainty-aware energy forecasting** — P10/P50/P90 confidence bands instead of single-point yield estimates
- Built the **grid hosting capacity heuristic** — estimates a site's likely spare grid capacity (thermal limit, existing generation, distance derating) rather than reporting distance-to-substation alone
- Delivered the **Planner** and **GIS Analyst** role dashboards, including a live what-if weight adjuster, grid capacity inspector, and land-use conflict indicators

### Milestone 4 — Not Started

Interactive what-if simulator polish, LLM-generated investment narratives, reports and export (PDF/Excel), notification system, pre-loaded India demo dataset, full testing pass, and deployment to Render.

## Planned Core Modules

- User authentication and role-based access control
- Project and site management
- Environmental data collection engine
- Geographic intelligence engine (GIS processing, terrain mapping, infrastructure proximity)
- Solar potential prediction engine
- Wind potential prediction engine
- Site suitability intelligence engine
- Energy generation forecasting engine
- Deployment optimization engine
- Site scoring engine (user-adjustable weighted suitability model)
- Role-based dashboards (Planner, GIS Analyst, Project Manager, Administrator)
- Notification and alert system
- Reports and export system (PDF, Excel)

## Signature Innovations

- **Multi-Objective Optimization (Pareto Frontier)** — NSGA-II via `pymoo`, trading off energy output, environmental impact, and infrastructure cost
- **SHAP-Based Explainability** — per-factor score attribution for every site
- **Uncertainty-Aware Forecasting** — P10/P50/P90 confidence bands
- **Grid Hosting Capacity Heuristic** — estimated spare capacity, not just distance
- Land-use conflict detection, LLM-generated investment narratives, and a pre-loaded India demo dataset are planned for later milestones

## Site Suitability Scoring Model

This is a fast, transparent triage score — not the platform's primary decision mechanism (that's the Pareto frontier and SHAP explainability engine above). Weights are **user-adjustable** rather than fixed, since suitability priorities differ by stakeholder (an investor weighs cost differently than a government agency weighs environmental impact).

**Factors (default starting weights, all adjustable):**

| Factor | Default Weight |
|---|---|
| Renewable Resource Availability | 30% |
| Geographic Suitability | 20% |
| Infrastructure Accessibility | 15% |
| Environmental Impact | 15% |
| Socio-Economic Viability | 15% |
| Economic/Cost Feasibility | 5% |

Socio-Economic Viability incorporates land acquisition complexity, demand proximity, local economic impact, land cost proxy, and social acceptance risk (population density near site).

Sites are classified into one of five categories: Excellent, Highly Suitable, Moderately Suitable, Low Suitability, Unsuitable.

## Tech Stack

**Backend:** Python, FastAPI
**Frontend:** JavaScript, TypeScript, React.js, Next.js, Tailwind CSS
**Database:** PostgreSQL with PostGIS (Supabase)
**Machine Learning:** XGBoost, Scikit-learn, SHAP, pymoo (NSGA-II)
**GIS and Remote Sensing:** GeoPandas, Rasterio, Shapely, GDAL
**Data Sources:** NASA POWER API, Global Wind Atlas, NASA SRTM Elevation Dataset, OpenStreetMap Overpass, Copernicus Sentinel Hub, WDPA, OpenWeather API
**Visualization:** Leaflet.js, Recharts
**DevOps:** Docker, Docker Compose, GitHub Actions, Render (deployment)

## Project Structure

```
SiteScout/
├── backend/
│   ├── app/
│   │   ├── api/routes/       FastAPI route handlers
│   │   ├── models/           SQLAlchemy ORM models
│   │   ├── schemas/          Pydantic request/response schemas
│   │   ├── services/         Business logic (ML, GIS, forecasting, optimization)
│   │   ├── config.py
│   │   ├── database.py
│   │   └── main.py
│   ├── models/                Trained ML model artifacts (.joblib)
│   ├── scripts/                Model training scripts
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/                 Next.js App Router pages
│       ├── components/    Reusable UI and dashboard components
│       ├── context/          Auth and theme context providers
│       └── lib/                  API client and utilities
├── docs/                       Documentation and architecture notes
├── .gitignore
└── README.md
```

Note: This structure will evolve as modules are implemented.

## Getting Started

Setup instructions will be added ahead of final deployment (Milestone 4).

## Disclaimer

This is an academic and learning-oriented project developed under the Infosys Springboard Internship program. It is not intended for production use in its current state, and prediction outputs should not be relied upon for real-world investment or deployment decisions without independent validation.

## License

To be determined.