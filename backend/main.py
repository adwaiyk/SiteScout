from fastapi import FastAPI
import auth, models, projects
from database import engine
from fastapi.middleware.cors import CORSMiddleware
import analysis
import projects

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="SiteScout API")

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "SiteScout API is live."}

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(analysis.router)