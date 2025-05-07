from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import SQLAlchemyError, OperationalError
import logging
import time

logger = logging.getLogger(__name__)

Base = declarative_base()

class Database:
    """Handles database connections and sessions."""
    _engine = None
    _session_factory = None

    @classmethod
    def initialize(cls, database_url: str, echo: bool = False, max_retries: int = 3, retry_interval: int = 5):
        """Initialize the async engine and sessionmaker with retry logic.
        
        Args:
            database_url: The URL of the database to connect to
            echo: Whether to echo SQL statements
            max_retries: Maximum number of connection retry attempts
            retry_interval: Time in seconds between retry attempts
        
        Raises:
            OperationalError: If connection to the database fails after all retries
        """
        if cls._engine is None:  # Ensure engine is created once
            retry_count = 0
            last_error = None
            
            while retry_count < max_retries:
                try:
                    logger.info(f"Attempting to connect to database (attempt {retry_count + 1}/{max_retries})")
                    cls._engine = create_async_engine(
                        database_url, 
                        echo=echo, 
                        future=True,
                        pool_pre_ping=True,  # Check connection validity before using from pool
                        pool_recycle=3600    # Recycle connections after 1 hour
                        # Removed connect_timeout as it's not supported by asyncpg
                    )
                    
                    cls._session_factory = sessionmaker(
                        bind=cls._engine, 
                        class_=AsyncSession, 
                        expire_on_commit=False, 
                        future=True
                    )
                    
                    logger.info("Successfully connected to database")
                    return
                    
                except (SQLAlchemyError, OperationalError) as e:
                    last_error = e
                    retry_count += 1
                    if retry_count < max_retries:
                        logger.warning(f"Database connection failed: {str(e)}. Retrying in {retry_interval} seconds...")
                        time.sleep(retry_interval)
                    else:
                        logger.error(f"Failed to connect to database after {max_retries} attempts: {str(e)}")
            
            # If we've exhausted all retries, raise the last error
            if last_error:
                raise OperationalError(f"Database connection failed after {max_retries} attempts", None) from last_error

    @classmethod
    def get_session_factory(cls):
        """Returns the session factory, ensuring it's initialized.
        
        Returns:
            The session factory for creating database sessions
            
        Raises:
            ValueError: If the database has not been initialized
        """
        if cls._session_factory is None:
            logger.error("Attempted to get session factory before database initialization")
            raise ValueError("Database not initialized. Call `initialize()` first.")
        return cls._session_factory
        
    @classmethod
    async def check_connection(cls):
        """Check if the database connection is working.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        if cls._engine is None:
            logger.error("Cannot check connection - database not initialized")
            return False
            
        try:
            # Create a connection and execute a simple query
            async with cls._engine.connect() as conn:
                from sqlalchemy import text
                await conn.execute(text("SELECT 1"))
            logger.info("Database connection check successful")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database connection check failed: {str(e)}")
            return False
