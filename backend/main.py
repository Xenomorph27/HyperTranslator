from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Placeholder for future import:
# from backend.models.sign_recognizer import load_model

@asynccontextmanager
async def lifespan(app: FastAPI):
    # load_model()  # Will load Transformer weights once at startup
    yield

app = FastAPI(title="ISL Translator API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-app.vercel.app", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "model": "isl_transformer_v2", "classes": 263}
