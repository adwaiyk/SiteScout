from fastapi import FastAPI
import auth, models, projects
from database import engine
from fastapi.middleware.cors import CORSMiddleware

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="SiteScout API")

app.include_router(auth.router)

@app.get("/")
def root():
    return {"message": "SiteScout API is live."}

app.include_router(auth.router)
app.include_router(projects.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Allow Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)