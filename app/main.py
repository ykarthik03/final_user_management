from builtins import Exception
from fastapi import FastAPI, Request, status
from starlette.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError, OperationalError
import logging

from app.database import Database
from app.dependencies import get_settings
from app.routers import user_routes
from app.utils.api_description import getDescription

# Set up logging
logger = logging.getLogger(__name__)
app = FastAPI(
    title="User Management",
    description=getDescription(),
    version="0.0.1",
    contact={
        "name": "API Support",
        "url": "http://www.example.com/support",
        "email": "support@example.com",
    },
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
)
# CORS middleware configuration
# This middleware will enable CORS and allow requests from any origin
# It can be configured to allow specific methods, headers, and origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # List of origins that are allowed to access the server, ["*"] allows all
    allow_credentials=True,  # Support credentials (cookies, authorization headers, etc.)
    allow_methods=["*"],  # Allowed HTTP methods
    allow_headers=["*"],  # Allowed HTTP headers
)

@app.on_event("startup")
async def startup_event():
    settings = get_settings()
    try:
        # Initialize database with retry logic
        Database.initialize(
            settings.database_url, 
            settings.debug,
            max_retries=5,  # Increase retries for startup
            retry_interval=3  # Shorter interval for startup
        )
        
        # Verify connection is working
        connection_ok = await Database.check_connection()
        if not connection_ok:
            logger.error("Database connection check failed during startup")
            # We continue anyway since the connection might recover later
        else:
            logger.info("Application started successfully with database connection")
    except OperationalError as e:
        logger.critical(f"Failed to initialize database: {str(e)}")
        # We don't exit here, but the app will return 503 errors for database operations

@app.exception_handler(Exception)
async def exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500, 
        content={"message": "An unexpected error occurred."}
    )

@app.exception_handler(OperationalError)
async def database_exception_handler(request, exc):
    logger.error(f"Database operational error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"message": "Database service unavailable. Please try again later."}
    )

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request, exc):
    logger.error(f"SQLAlchemy error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "A database error occurred."}
    )

@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except SQLAlchemyError as e:
        logger.error(f"Database error during request: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"message": "Database error occurred. Please try again later."}
        )

app.include_router(user_routes.router)


