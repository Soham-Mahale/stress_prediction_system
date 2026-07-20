from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.database import connect, disconnect, ensure_indexes
from backend.app.routers import assessments, profiles, users

origins = [
    "http://localhost:5173",  # Vite React frontend
    "http://192.168.29.244:5173",  # LAN access
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    connect()
    await ensure_indexes()
    yield
    disconnect()


app = FastAPI(title="Stress Management & Personalized Wellness Platform", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(profiles.router)
app.include_router(assessments.router)
