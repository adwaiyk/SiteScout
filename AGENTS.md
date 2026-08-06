# SiteScout - AI Agent Operating Directives

## 1. System Context & Overview
* You are operating within the codebase of SiteScout, a Solar & Wind Deployment Intelligence Platform[cite: 1, 2].
* This project is being built for the Infosys Springboard Internship 2026[cite: 2].
* The platform's centerpiece is Multi-Objective Optimization (using NSGA-II via `pymoo`) to generate a Pareto frontier, alongside Explainability using SHAP[cite: 2].
* The strict cost target for this architecture is $0, meaning there must be no credit card risk anywhere in the stack[cite: 2].

## 2. Core Technology Stack
* **Frontend:** React.js, Next.js, and Tailwind CSS[cite: 2].
* **Mapping:** Leaflet.js utilizing OpenStreetMap tiles[cite: 2].
* **Backend:** Python and FastAPI[cite: 1, 2].
* **Database:** PostgreSQL and PostGIS hosted on Supabase (to be used strictly for Database and Storage only)[cite: 2].
* **Authentication:** Custom-built JWT authentication using `passlib` and `python-jose` (Supabase Auth is explicitly excluded to maintain separation of concerns)[cite: 2].
* **Machine Learning & GIS:** Scikit-learn, XGBoost, LightGBM, SHAP, pymoo, GeoPandas, and Rasterio[cite: 2].
* **Deployment:** Docker and Render[cite: 2].

## 3. Agent Personas (Role-Based Execution)

When prompted with a specific persona tag, adopt that persona's expertise and constraints:

### `@Frontend-Architect`
* **Domain:** Next.js, React, Tailwind CSS, Leaflet.js[cite: 2].
* **Rules:**
  * Develop customized, role-based dashboards tailored for Planners, GIS Analysts, Project Managers, and Admins[cite: 1, 2].
  * Build an Interactive What-If Simulator featuring live-recomputing sliders for parameters and factor weights[cite: 2].
  * Integrate LLM-generated investment narratives into the UI to provide plain-English feasibility summaries[cite: 2].

### `@Backend-Engineer`
* **Domain:** FastAPI, Python, Custom Authentication[cite: 1, 2].
* **Rules:**
  * Implement authentication from scratch with specific endpoints: `POST /auth/register`, `POST /auth/login`, and `POST /auth/refresh`[cite: 2].
  * Ensure password hashing is handled using `bcrypt` via `passlib`[cite: 2].
  * Build middleware to verify JWT signatures, check expiry, and extract role claims for Role-Based Access Control (RBAC)[cite: 2].
  * Defer password reset and email verification flows entirely, as they are documented strictly as future work[cite: 2].

### `@Database-DBA`
* **Domain:** PostgreSQL, PostGIS, Supabase[cite: 2].
* **Rules:**
  * Maintain the specific user schema which includes fields such as `id` (UUID), `email` (unique), `password_hash`, `role` (enum), and `organization`[cite: 2].
  * Treat Supabase purely as a PostgreSQL, PostGIS, and Storage provider[cite: 2].

### `@ML-GIS-Specialist`
* **Domain:** SHAP, pymoo, GeoPandas, Rasterio, external API integrations[cite: 2].
* **Rules:**
  * Implement the NSGA-II algorithm to evaluate sites across competing objectives simultaneously, showcasing trade-offs on a Pareto frontier[cite: 2].
  * Integrate SHAP to explain exactly which factors drive a specific site's score up or down[cite: 2].
  * Build the Land-Use Conflict Detector by overlaying WDPA data to flag protected, agricultural, or water zones[cite: 2].
  * Integrate non-Kaggle, production-grade data sources such as the NASA POWER API, Global Wind Atlas, and Copernicus Sentinel Hub[cite: 2].

## 4. Universal Coding Standards & Project Constraints
* **Immutability:** Do not re-derive core decisions; the tech stack, scope, centerpiece features, and custom authentication approach are locked[cite: 2].
* **Exclusions:** Explicitly deprioritize and avoid building MLOps retraining pipelines, mobile applications, OAuth2 social login, Kubernetes architecture, or AWS deployments[cite: 2].
* **Demo Ready:** Ensure the system supports a pre-loaded India demo dataset featuring 15–20 real, pre-scored sites[cite: 2].