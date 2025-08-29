import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .providers.fixtures import FixturesProvider
from .providers.searoutes import SearoutesProvider
from .routes.carriers import router as carriers_router
from .routes.ports import router as ports_router
from .routes.schedules import router as schedules_router

# Provider selection via environment variable
provider_name = os.environ.get("PROVIDER", "fixtures").lower()
if provider_name == "searoutes":
    schedule_provider = SearoutesProvider()
else:
    schedule_provider = FixturesProvider()

app = FastAPI(title="Searoutes Mock API", version="1.0.0")

# CORS for local dev / browser UI
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inject provider into routes
from .routes.schedules import set_provider

set_provider(schedule_provider)

# Register routers
app.include_router(schedules_router)
app.include_router(ports_router)
app.include_router(carriers_router)


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"ok": True}
