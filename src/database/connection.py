"""
Database Connection Manager
Handles connections to different database types
"""

import logging
import os
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseProvider(ABC):
    """Abstract base class for database providers"""
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to the database"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Close the database connection"""
        pass
    
    @abstractmethod
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a query and return results"""
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Get database schema information"""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test the database connection"""
        pass


class PostgreSQLProvider(DatabaseProvider):
    """PostgreSQL database provider"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = None
        self.engine = None
        
        # Connection parameters
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 5432)
        self.database = config.get('database', 'db_gpt')
        self.username = config.get('username') or os.getenv('DB_USERNAME')
        self.password = config.get('password') or os.getenv('DB_PASSWORD')
        self.url = config.get('url') or os.getenv('DATABASE_URL')
        
        # Pool settings
        self.pool_size = config.get('pool_size', 10)
        self.max_overflow = config.get('max_overflow', 20)
        self.pool_timeout = config.get('pool_timeout', 30)
    
    def connect(self) -> bool:
        """Establish connection to PostgreSQL"""
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            
            if self.url:
                # Use connection URL if provided
                self.engine = create_engine(
                    self.url,
                    pool_size=self.pool_size,
                    max_overflow=self.max_overflow,
                    pool_timeout=self.pool_timeout
                )
            else:
                # Build connection URL from components
                if not all([self.username, self.password, self.database]):
                    raise ValueError("Database credentials not provided")
                
                connection_url = f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
                self.engine = create_engine(
                    connection_url,
                    pool_size=self.pool_size,
                    max_overflow=self.max_overflow,
                    pool_timeout=self.pool_timeout
                )
            
            # Test the connection
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            
            logger.info("PostgreSQL connection established successfully")
            return True
            
        except ImportError:
            raise ImportError("SQLAlchemy not installed. Run: pip install sqlalchemy psycopg2-binary")
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close PostgreSQL connection"""
        if self.engine:
            self.engine.dispose()
            logger.info("PostgreSQL connection closed")
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a query on PostgreSQL"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(query)
                if result.returns_rows:
                    columns = result.keys()
                    return [dict(zip(columns, row)) for row in result.fetchall()]
                else:
                    return [{"affected_rows": result.rowcount}]
        except Exception as e:
            logger.error(f"PostgreSQL query execution failed: {e}")
            raise
    
    def get_schema(self) -> Dict[str, Any]:
        """Get PostgreSQL schema information"""
        try:
            schema_query = """
            SELECT 
                t.table_name,
                c.column_name,
                c.data_type,
                c.is_nullable,
                c.column_default
            FROM information_schema.tables t
            JOIN information_schema.columns c ON t.table_name = c.table_name
            WHERE t.table_schema = 'public'
            ORDER BY t.table_name, c.ordinal_position
            """
            
            with self.engine.connect() as conn:
                result = conn.execute(schema_query)
                columns = result.keys()
                rows = [dict(zip(columns, row)) for row in result.fetchall()]
            
            # Organize by table
            schema = {}
            for row in rows:
                table_name = row['table_name']
                if table_name not in schema:
                    schema[table_name] = []
                schema[table_name].append({
                    'column_name': row['column_name'],
                    'data_type': row['data_type'],
                    'is_nullable': row['is_nullable'],
                    'column_default': row['column_default']
                })
            
            return schema
            
        except Exception as e:
            logger.error(f"Failed to get PostgreSQL schema: {e}")
            return {}
    
    def test_connection(self) -> bool:
        """Test PostgreSQL connection"""
        try:
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"PostgreSQL connection test failed: {e}")
            return False


class SQLiteProvider(DatabaseProvider):
    """SQLite database provider"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = None
        self.database_path = config.get('database_path', 'db_gpt.db')
    
    def connect(self) -> bool:
        """Establish connection to SQLite"""
        try:
            import sqlite3
            self.connection = sqlite3.connect(self.database_path)
            self.connection.row_factory = sqlite3.Row  # Enable dict-like access
            logger.info(f"SQLite connection established: {self.database_path}")
            return True
        except Exception as e:
            logger.error(f"SQLite connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close SQLite connection"""
        if self.connection:
            self.connection.close()
            logger.info("SQLite connection closed")
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a query on SQLite"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            else:
                self.connection.commit()
                return [{"affected_rows": cursor.rowcount}]
        except Exception as e:
            logger.error(f"SQLite query execution failed: {e}")
            raise
    
    def get_schema(self) -> Dict[str, Any]:
        """Get SQLite schema information"""
        try:
            schema_query = """
            SELECT 
                name as table_name,
                sql as table_sql
            FROM sqlite_master 
            WHERE type='table'
            """
            
            cursor = self.connection.cursor()
            cursor.execute(schema_query)
            tables = cursor.fetchall()
            
            schema = {}
            for table in tables:
                table_name = table['table_name']
                schema[table_name] = []
                
                # Get columns for this table
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                for col in columns:
                    schema[table_name].append({
                        'column_name': col[1],
                        'data_type': col[2],
                        'is_nullable': not col[3],
                        'column_default': col[4]
                    })
            
            return schema
            
        except Exception as e:
            logger.error(f"Failed to get SQLite schema: {e}")
            return {}
    
    def test_connection(self) -> bool:
        """Test SQLite connection"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"SQLite connection test failed: {e}")
            return False


class DatabaseConnection:
    """Main database connection manager"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_type = config.get('type', 'postgresql')
        self.provider = self._initialize_provider()
        
        logger.info(f"Initialized database connection for: {self.db_type}")
    
    def _initialize_provider(self) -> DatabaseProvider:
        """Initialize the appropriate database provider"""
        if self.db_type == 'postgresql':
            return PostgreSQLProvider(self.config)
        elif self.db_type == 'sqlite':
            return SQLiteProvider(self.config)
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")
    
    def connect(self) -> bool:
        """Establish database connection"""
        return self.provider.connect()
    
    def disconnect(self):
        """Close database connection"""
        self.provider.disconnect()
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a database query"""
        return self.provider.execute_query(query)
    
    def get_schema(self) -> Dict[str, Any]:
        """Get database schema"""
        return self.provider.get_schema()
    
    def test_connection(self) -> bool:
        """Test database connection"""
        return self.provider.test_connection()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        try:
            if not self.test_connection():
                self.connect()
            yield self
        finally:
            pass  # Connection is managed by the provider
    
    def execute_sql_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Execute SQL commands from a file"""
        try:
            with open(file_path, 'r') as f:
                sql_content = f.read()
            
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            results = []
            
            for statement in statements:
                if statement:
                    result = self.execute_query(statement)
                    results.extend(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to execute SQL file {file_path}: {e}")
            raise
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific table"""
        schema = self.get_schema()
        return schema.get(table_name, {})
    
    def list_tables(self) -> List[str]:
        """List all tables in the database"""
        schema = self.get_schema()
        return list(schema.keys())
    
    def get_table_count(self, table_name: str) -> int:
        """Get the number of rows in a table"""
        try:
            result = self.execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
            return result[0]['count'] if result else 0
        except Exception as e:
            logger.error(f"Failed to get count for table {table_name}: {e}")
            return 0 