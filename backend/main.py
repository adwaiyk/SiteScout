from fastapi import FastAPI
import auth, models, projects
from database import engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="SiteScout API")

app.include_router(auth.router)

@app.get("/")
def root():
    return {"message": "SiteScout API is live."}

app.include_router(auth.router)
app.include_router(projects.router)