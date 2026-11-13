from fastapi import FastAPI
from api.routes import blog
from src.config import setup_logging

setup_logging()

app = FastAPI(title="AI Blog Generator")

app.include_router(
    blog.router,
    prefix="/api/blog"
)