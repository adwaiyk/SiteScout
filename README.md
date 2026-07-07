# SiteScout

**Solar & Wind Deployment Intelligence Platform**

> Status: In Development (Infosys Springboard Internship Project)

## Overview

SiteScout is an AI-powered platform that recommends optimal locations for solar and wind energy deployment by analyzing environmental, geographic, climatic, and infrastructure-related factors. The platform combines geospatial analytics, satellite imagery, weather forecasting, terrain analysis, and machine learning to estimate renewable energy generation potential, evaluate project feasibility, and support investment decision-making.

This project is being built as part of the Infosys Springboard Internship program and is currently under active development. Features, APIs, and documentation are subject to change as milestones are completed.

## Objective

To identify high-potential locations for solar and wind energy projects using data-driven site suitability scoring, resource prediction models, and deployment optimization, supporting renewable energy companies, government agencies, utility providers, environmental organizations, infrastructure planners, and sustainability consultants.

## Current Development Status

This project is being implemented in four milestones over an eight-week timeline. Refer to the table below for progress.

| Milestone | Focus Area | Status |
|---|---|---|
| Milestone 1 (Week 1–2) | Project setup, authentication, site management, dataset integration | In Progress |
| Milestone 2 (Week 3–4) | Environmental intelligence engine, solar and wind prediction models | Not Started |
| Milestone 3 (Week 5–6) | Site suitability engine, deployment optimization, forecasting, dashboards | Not Started |
| Milestone 4 (Week 7–8) | Analytics, testing, containerization, deployment | Not Started |

Note: This README will be updated as each milestone is completed.

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
- Site scoring engine (weighted multi-factor suitability model)
- Role-based dashboards (Planner, GIS Analyst, Project Manager, Administrator)
- Notification and alert system
- Reports and export system (PDF, Excel)

## Site Suitability Scoring Model

Deployment suitability is calculated using a weighted scoring model:

| Factor | Weight |
|---|---|
| Renewable Resource Availability | 35% |
| Geographic Suitability | 25% |
| Infrastructure Accessibility | 15% |
| Environmental Impact | 15% |
| Economic Feasibility | 10% |

Sites are classified into one of five categories: Excellent, Highly Suitable, Moderately Suitable, Low Suitability, Unsuitable.

## Tech Stack

**Backend:** Python, FastAPI
**Frontend:** JavaScript, React.js, Next.js, Tailwind CSS
**Database:** PostgreSQL with PostGIS (primary), MongoDB (secondary)
**Machine Learning:** XGBoost, Random Forest, LightGBM, TensorFlow, PyTorch, Scikit-learn
**GIS and Remote Sensing:** QGIS, GDAL, Rasterio, GeoPandas, Shapely
**Data Sources:** NASA POWER API, Global Wind Atlas, NASA SRTM Elevation Dataset, OpenStreetMap, Copernicus Sentinel Hub, OpenWeather API
**Visualization:** Plotly, Leaflet.js, Mapbox, Chart.js
**DevOps:** Docker, Docker Compose, GitHub Actions, AWS/Azure

## Project Structure

```
SiteScout/
├── backend/          FastAPI application, ML models, services
├── frontend/          React/Next.js application
├── data/                 Sample and reference datasets (large raw data excluded)
├── docs/               Documentation and architecture notes
├── .gitignore
└── README.md
```

Note: This structure will evolve as modules are implemented.

## Getting Started

Setup instructions will be added once the initial backend and frontend environments are configured (Milestone 1).

## Disclaimer

This is an academic and learning-oriented project developed under the Infosys Springboard Internship program. It is not intended for production use in its current state, and prediction outputs should not be relied upon for real-world investment or deployment decisions without independent validation.

## License

To be determined.