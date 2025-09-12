from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

from database import engine, Base
from routers import auth, survey
from models import User, Survey, Response
import schemas
from middlewares import response_wrapper_middleware, logging_middleware

app = FastAPI(
    title="CultureLens API - Refactored",
    description="FastAPI and MySQL backend API for CultureLens, with new DB schema.",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add middleware
app.middleware('http')(logging_middleware)
app.middleware('http')(response_wrapper_middleware)

# CORS Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "https://culturelens.cloud", "http://culturelens-front.s3-website.ap-northeast-2.amazonaws.com"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.on_event("startup")
async def startup_event():
    """
    On application startup, create database tables.
    """
    async with engine.begin() as conn:
        # In development, you might want to drop and recreate tables.
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

# Register routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(survey.router, prefix="/api/surveys", tags=["Surveys"])

@app.get("/", tags=["Root"], response_class=HTMLResponse)
async def read_root():
    """Root endpoint to check server status and provide API documentation links."""
    return """
    <html>
        <head>
            <title>CultureLens API</title>
        </head>
        <body>
            <h1>CultureLens API (v2.0)</h1>
            <p>✅ Server is running correctly.</p>
            <p>API Documentation:</p>
            <ul>
                <li><a href="/api/docs">Swagger UI</a></li>
                <li><a href="/api/redoc">ReDoc</a></li>
            </ul>
        </body>
    </html>
    """

# To run the server directly with uvicorn, uncomment the following lines:
# if __name__ == "__main__":
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
