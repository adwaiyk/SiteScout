# SiteScout ⚡

AI-powered platform for recommending optimal solar & wind deployment locations 
using geospatial analytics, climate data, and machine learning.

![badges: Python | FastAPI | React | PostgreSQL | Docker]

## Overview

SiteScout analyzes environmental, geographic, climatic, and infrastructure data 
to recommend high-potential locations for renewable energy projects. Built for 
renewable energy planners, GIS analysts, and infrastructure decision-makers.

## Features

- 🌞 Solar potential prediction (irradiance, capacity factor, energy output)
- 💨 Wind potential prediction (wind speed, power density, turbine suitability)
- 🗺️ GIS-based site suitability scoring (weighted multi-factor model)
- 📊 Deployment optimization engine (solar/wind/hybrid recommendations)
- 📈 Energy generation & revenue forecasting
- 🔐 Role-based dashboards (Planner, GIS Analyst, Project Manager, Admin)
- 📄 PDF/Excel report export

## Tech Stack

**Backend:** Python, FastAPI  
**Frontend:** React.js, Next.js, Tailwind CSS  
**Database:** PostgreSQL + PostGIS, MongoDB  
**ML/AI:** XGBoost, Random Forest, TensorFlow, Scikit-learn  
**GIS:** GeoPandas, Rasterio, GDAL, Shapely  
**Data Sources:** NASA POWER, Global Wind Atlas, NASA SRTM, OpenStreetMap, Copernicus Sentinel  
**Deployment:** Docker, AWS/Azure

## Architecture

[link or embed architecture diagram image here]

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ with PostGIS extension
- Docker (optional, for containerized setup)

### Installation
\`\`\`bash
git clone https://github.com/yourusername/sitescout.git
cd sitescout

# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
\`\`\`

### Environment Variables
\`\`\`
DATABASE_URL=
NASA_POWER_API_KEY=
OPENWEATHER_API_KEY=
JWT_SECRET=
\`\`\`

## Project Structure
\`\`\`
sitescout/
├── backend/
│   ├── services/
│   ├── models/
│   └── api/
├── frontend/
│   └── src/
├── ml/
│   └── notebooks/
└── docker-compose.yml
\`\`\`

## Scoring Model

Deployment Suitability Score:
- Renewable Resource Availability — 35%
- Geographic Suitability — 25%
- Infrastructure Accessibility — 15%
- Environmental Impact — 15%
- Economic Feasibility — 10%

## Roadmap
- [ ] Week 1-2: Auth, site management, dataset integration
- [ ] Week 3-4: Solar/wind prediction engines
- [ ] Week 5-6: Suitability engine, optimization, dashboards
- [ ] Week 7-8: Testing, Docker deployment, docs

## License
MIT

## Acknowledgments
Built as part of the Infosys Springboard internship program.