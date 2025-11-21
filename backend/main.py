from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.core.database import create_db_and_tables
from app.routers import projects, websockets, settings
from app.services.watcher_service import watcher_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    watcher_service.start()
    yield
    watcher_service.stop()

app = FastAPI(title="TuTu's Code Ark Backend", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(websockets.router, tags=["websockets"])
app.include_router(settings.router, prefix="/settings", tags=["settings"])

@app.get("/health")
async def health_check():
    return {"status": "online", "message": "TuTu's Code Ark Backend is running"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
