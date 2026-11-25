from fastapi import FastAPI
from api.routes import blog
from src.config import setup_logging
from src.auth import router as auth_router
from api.routes import chat 
from src.database import Base, engine
from src.database import (
    MarkdownFile,
    User,
    BlogThread,
    BlogJobEvent,
    ChatConversation,
    ChatJob,
)

Base.metadata.create_all(bind=engine)

setup_logging()

app = FastAPI(title="AI Blog Generator")

app.include_router(
    blog.router,
    prefix="/api/blog"
)

app.include_router(
    auth_router,
    prefix="/api"
)

app.include_router(
    chat.router,
    prefix="/api/blog"
)