from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.core.config import settings
from api.core.database import Base, engine
from api.routers import (
    auth, users, transactions, budget,
    analytics, settings as settings_router,
    webhooks, categories,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PREFIX = "/v1"
app.include_router(auth.router,              prefix=PREFIX)
app.include_router(users.router,             prefix=PREFIX)
app.include_router(transactions.router,      prefix=PREFIX)
app.include_router(budget.router,            prefix=PREFIX)
app.include_router(analytics.router,         prefix=PREFIX)
app.include_router(settings_router.router,   prefix=PREFIX)
app.include_router(webhooks.router,          prefix=PREFIX)
app.include_router(categories.router,        prefix=PREFIX)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "version": settings.APP_VERSION}