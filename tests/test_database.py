"""
Tests for database connection and error handling.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from app.database import Database

def test_database_initialization():
    """Test that database initialization works correctly."""
    # Ensure Database is in a clean state for this specific test
    Database._engine = None
    Database._session_factory = None
    
    # Mock the create_async_engine function to avoid actual database connection
    with patch('app.database.create_async_engine') as mock_engine:
        # Set up the mock to return a mock engine
        mock_engine.return_value = MagicMock()
        
        # Initialize the database
        Database.initialize("sqlite:///test.db", echo=False)
        
        # Check that create_async_engine was called with the correct arguments
        mock_engine.assert_called_once()
        args, kwargs = mock_engine.call_args
        assert args[0] == "sqlite:///test.db"
        assert kwargs["echo"] is False
        assert kwargs["future"] is True
        
        # Reset the database class for other tests
        Database._engine = None
        Database._session_factory = None

def test_database_initialization_retry_logic():
    """Test that database initialization retry logic works correctly."""
    # Mock the create_async_engine function to simulate database connection failures
    
    # ENSURE Database is in a clean state for this specific test
    Database._engine = None
    Database._session_factory = None

    with patch('app.database.create_async_engine') as mock_engine:
        # Set up the mock to raise an OperationalError twice, then succeed
        mock_engine.side_effect = [
            OperationalError("connection failed", None, None),
            OperationalError("connection failed again", None, None),
            MagicMock()  # Success on third attempt
        ]
        
        # Mock time.sleep to avoid actual waiting
        with patch('app.database.time.sleep') as mock_sleep:
            # Initialize the database with retry logic
            Database.initialize(
                "sqlite:///test.db", 
                echo=False, 
                max_retries=3, 
                retry_interval=1
            )
            
            # Check that create_async_engine was called three times
            assert mock_engine.call_count == 3
            
            # Check that sleep was called twice (after first and second failures)
            assert mock_sleep.call_count == 2
            
            # Reset the database class for other tests
            Database._engine = None
            Database._session_factory = None

def test_database_initialization_max_retries_exceeded():
    """Test that database initialization raises an error after max retries."""
    # Ensure Database is in a clean state for this specific test
    Database._engine = None
    Database._session_factory = None
    
    # Mock the create_async_engine function to always fail
    with patch('app.database.create_async_engine') as mock_engine:
        # Set up the mock to raise SQLAlchemyError for each call
        # We need to use a list to ensure a new exception is raised each time
        mock_engine.side_effect = [
            SQLAlchemyError("Database connection failed"),
            SQLAlchemyError("Database connection failed again"),
            SQLAlchemyError("Database connection failed a third time")
        ]
        
        # Mock time.sleep to avoid actual waiting
        with patch('app.database.time.sleep'):
            # Initialize the database with retry logic, should raise an exception
            with pytest.raises(Exception):
                Database.initialize(
                    "sqlite:///test.db", 
                    echo=False, 
                    max_retries=3, 
                    retry_interval=1
                )
            
            # Check that create_async_engine was called three times
            assert mock_engine.call_count == 3
            
            # Reset the database class for other tests
            Database._engine = None
            Database._session_factory = None

@pytest.mark.asyncio
async def test_check_connection_success():
    """Test that check_connection returns True when connection is successful."""
    # Set up a mock engine with proper async support
    mock_engine = MagicMock()
    mock_conn = AsyncMock()
    
    # Make the connection context manager awaitable
    mock_connect_context = AsyncMock()
    mock_connect_context.__aenter__.return_value = mock_conn
    mock_engine.connect.return_value = mock_connect_context
    
    # Make execute awaitable and return a result with scalar_one method
    result_proxy = AsyncMock()
    result_proxy.scalar_one = AsyncMock(return_value=1)
    mock_conn.execute = AsyncMock(return_value=result_proxy)
    
    # Patch the database class
    with patch.object(Database, '_engine', mock_engine):
        # Call check_connection
        result = await Database.check_connection()
        
        # Check that the result is True
        assert result is True
        
        # Verify the connection was used correctly
        mock_engine.connect.assert_called_once()

@pytest.mark.asyncio
async def test_check_connection_failure():
    """Test that check_connection returns False when connection fails."""
    # Set up a mock engine that raises an exception
    mock_engine = MagicMock()
    mock_engine.connect.return_value.__aenter__.side_effect = SQLAlchemyError("connection failed")
    
    # Patch the database class
    with patch.object(Database, '_engine', mock_engine):
        # Call check_connection
        result = await Database.check_connection()
        
        # Check that the result is False
        assert result is False

@pytest.mark.asyncio
async def test_check_connection_not_initialized():
    """Test that check_connection returns False when database is not initialized."""
    # Patch the database class to have no engine
    with patch.object(Database, '_engine', None):
        # Call check_connection
        result = await Database.check_connection()
        
        # Check that the result is False
        assert result is False
