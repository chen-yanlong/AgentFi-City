from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import health, demo, events

app = FastAPI(title="AgentFi City", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(demo.router)
app.include_router(events.router)
