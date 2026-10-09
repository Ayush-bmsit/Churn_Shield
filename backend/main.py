"""FastAPI entrypoint: wires routes, CORS, and a health check."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import analytics, auth, chatbot, customers, prediction

app = FastAPI(
    title="ChurnShield API",
    description=(
        "ChurnShield demo: JWT auth, a saved sklearn pipeline, MySQL analytics, "
        "and a SELECT-only SQL assistant. Policy RAG is not implemented."
    ),
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(prediction.router)
app.include_router(customers.router)
app.include_router(analytics.router)
app.include_router(chatbot.router)


@app.get("/health")
def health():
    return {"status": "ok"}
