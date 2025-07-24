from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router
from app.core.database import Base, engine

# Create database tables
try:
    Base.metadata.create_all(bind=engine)
    print("DEBUG: main.py - Database tables created successfully (or already exist).")
except Exception as e:
    print(f"ERROR: main.py - Failed to create database tables: {e}")
    raise e # <--- ADD THIS LINE

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {"message": "HCP CRM Module Backend API"}