"""
Unit tests for Text-to-SQL Converter
"""

import pytest
from unittest.mock import Mock, patch
from src.utils.text_to_sql import TextToSQLConverter, SQLQuery


class TestTextToSQLConverter:
    """Test cases for TextToSQLConverter class"""
    
    @pytest.fixture
    def mock_llm_manager(self):
        """Create a mock LLM manager"""
        mock = Mock()
        mock.generate.return_value = "SELECT * FROM users WHERE active = true"
        return mock
    
    @pytest.fixture
    def mock_db_connection(self):
        """Create a mock database connection"""
        mock = Mock()
        mock.get_schema.return_value = {
            'users': [
                {
                    'column_name': 'id',
                    'data_type': 'integer',
                    'is_nullable': False,
                    'column_default': None
                },
                {
                    'column_name': 'name',
                    'data_type': 'varchar',
                    'is_nullable': True,
                    'column_default': None
                },
                {
                    'column_name': 'active',
                    'data_type': 'boolean',
                    'is_nullable': True,
                    'column_default': 'true'
                }
            ]
        }
        return mock
    
    @pytest.fixture
    def converter(self, mock_llm_manager, mock_db_connection):
        """Create a TextToSQLConverter instance for testing"""
        return TextToSQLConverter(mock_llm_manager, mock_db_connection)
    
    def test_converter_initialization(self, converter, mock_db_connection):
        """Test TextToSQLConverter initialization"""
        assert converter.llm_manager is not None
        assert converter.db_connection is not None
        assert 'users' in converter.schema_cache
    
    def test_convert_basic_query(self, converter):
        """Test basic text to SQL conversion"""
        text = "Show me all active users"
        
        with patch.object(converter, '_generate_sql') as mock_generate:
            mock_generate.return_value = "SELECT * FROM users WHERE active = true"
            
            result = converter.convert(text)
            
            assert isinstance(result, SQLQuery)
            assert result.query == "SELECT * FROM users WHERE active = true"
            assert result.query_type == "SELECT"
            assert "users" in result.tables
    
    def test_format_schema_context(self, converter):
        """Test schema context formatting"""
        context = converter._format_schema_context()
        
        assert "Table: users" in context
        assert "id: integer NOT NULL" in context
        assert "name: varchar NULL" in context
        assert "active: boolean NULL DEFAULT true" in context
    
    def test_extract_sql_from_response(self, converter):
        """Test SQL extraction from LLM response"""
        # Test with markdown code blocks
        response = "```sql\nSELECT * FROM users\n```"
        sql = converter._extract_sql_from_response(response)
        assert sql == "SELECT * FROM users"
        
        # Test with SQL prefix
        response = "SQL: SELECT * FROM users"
        sql = converter._extract_sql_from_response(response)
        assert sql == "SELECT * FROM users"
        
        # Test with Query prefix
        response = "Query: SELECT * FROM users"
        sql = converter._extract_sql_from_response(response)
        assert sql == "SELECT * FROM users"
        
        # Test clean SQL
        response = "SELECT * FROM users"
        sql = converter._extract_sql_from_response(response)
        assert sql == "SELECT * FROM users"
    
    def test_parse_sql_select(self, converter):
        """Test parsing SELECT query"""
        sql = "SELECT id, name FROM users WHERE active = true"
        result = converter._parse_sql(sql)
        
        assert result.query_type == "SELECT"
        assert "users" in result.tables
        assert "id" in result.columns
        assert "name" in result.columns
        assert "active = true" in result.conditions
        assert result.confidence > 0.0
    
    def test_parse_sql_insert(self, converter):
        """Test parsing INSERT query"""
        sql = "INSERT INTO users (name, active) VALUES ('John', true)"
        result = converter._parse_sql(sql)
        
        assert result.query_type == "INSERT"
        assert "users" in result.tables
        assert result.confidence > 0.0
    
    def test_parse_sql_update(self, converter):
        """Test parsing UPDATE query"""
        sql = "UPDATE users SET active = false WHERE id = 1"
        result = converter._parse_sql(sql)
        
        assert result.query_type == "UPDATE"
        assert "users" in result.tables
        assert "id = 1" in result.conditions
        assert result.confidence > 0.0
    
    def test_parse_sql_delete(self, converter):
        """Test parsing DELETE query"""
        sql = "DELETE FROM users WHERE id = 1"
        result = converter._parse_sql(sql)
        
        assert result.query_type == "DELETE"
        assert "users" in result.tables
        assert "id = 1" in result.conditions
        assert result.confidence > 0.0
    
    def test_detect_query_type(self, converter):
        """Test query type detection"""
        assert converter._detect_query_type("SELECT * FROM users") == "SELECT"
        assert converter._detect_query_type("INSERT INTO users") == "INSERT"
        assert converter._detect_query_type("UPDATE users SET") == "UPDATE"
        assert converter._detect_query_type("DELETE FROM users") == "DELETE"
        assert converter._detect_query_type("CREATE TABLE users") == "CREATE"
        assert converter._detect_query_type("ALTER TABLE users") == "ALTER"
        assert converter._detect_query_type("DROP TABLE users") == "DROP"
        assert converter._detect_query_type("INVALID QUERY") == "UNKNOWN"
    
    def test_extract_tables(self, converter):
        """Test table extraction from SQL"""
        # SELECT with JOIN
        sql = "SELECT * FROM users JOIN orders ON users.id = orders.user_id"
        tables = converter._extract_tables(sql)
        assert "users" in tables
        assert "orders" in tables
        
        # INSERT
        sql = "INSERT INTO users (name) VALUES ('John')"
        tables = converter._extract_tables(sql)
        assert "users" in tables
        
        # UPDATE
        sql = "UPDATE users SET name = 'John'"
        tables = converter._extract_tables(sql)
        assert "users" in tables
    
    def test_extract_columns(self, converter):
        """Test column extraction from SQL"""
        sql = "SELECT id, name, email FROM users"
        columns = converter._extract_columns(sql)
        assert "id" in columns
        assert "name" in columns
        assert "email" in columns
        
        # Test with aliases
        sql = "SELECT id AS user_id, name AS user_name FROM users"
        columns = converter._extract_columns(sql)
        assert "id" in columns
        assert "name" in columns
        
        # Test with functions
        sql = "SELECT COUNT(*), MAX(id) FROM users"
        columns = converter._extract_columns(sql)
        assert len(columns) == 0  # Functions are filtered out
    
    def test_extract_conditions(self, converter):
        """Test condition extraction from SQL"""
        sql = "SELECT * FROM users WHERE active = true AND age > 18"
        conditions = converter._extract_conditions(sql)
        assert "active = true" in conditions
        assert "age > 18" in conditions
        
        # Test with OR
        sql = "SELECT * FROM users WHERE active = true OR verified = true"
        conditions = converter._extract_conditions(sql)
        assert "active = true" in conditions
        assert "verified = true" in conditions
    
    def test_generate_explanation(self, converter):
        """Test explanation generation"""
        sql = "SELECT id, name FROM users WHERE active = true"
        query_type = "SELECT"
        tables = ["users"]
        columns = ["id", "name"]
        
        explanation = converter._generate_explanation(sql, query_type, tables, columns)
        
        assert "retrieves data from users" in explanation
        assert "selecting columns: id, name" in explanation
    
    def test_calculate_confidence(self, converter):
        """Test confidence calculation"""
        # Valid query with existing table
        sql = "SELECT * FROM users"
        tables = ["users"]
        confidence = converter._calculate_confidence(sql, tables)
        assert confidence > 0.5
        
        # Query with non-existent table
        sql = "SELECT * FROM non_existent_table"
        tables = ["non_existent_table"]
        confidence = converter._calculate_confidence(sql, tables)
        assert confidence < 1.0
        
        # Invalid SQL
        sql = "INVALID SQL QUERY"
        tables = []
        confidence = converter._calculate_confidence(sql, tables)
        assert confidence < 1.0
    
    def test_validate_sql_success(self, converter):
        """Test SQL validation success"""
        sql = "SELECT * FROM users"
        
        with patch.object(converter.db_connection, 'execute_query') as mock_execute:
            mock_execute.return_value = [{"id": 1, "name": "John"}]
            
            is_valid, message = converter.validate_sql(sql)
            
            assert is_valid is True
            assert "valid" in message.lower()
    
    def test_validate_sql_failure(self, converter):
        """Test SQL validation failure"""
        sql = "SELECT * FROM non_existent_table"
        
        with patch.object(converter.db_connection, 'execute_query') as mock_execute:
            mock_execute.side_effect = Exception("Table does not exist")
            
            is_valid, message = converter.validate_sql(sql)
            
            assert is_valid is False
            assert "failed" in message.lower()
    
    def test_optimize_sql(self, converter):
        """Test SQL optimization"""
        sql = "SELECT * FROM users WHERE active = true"
        
        with patch.object(converter.llm_manager, 'generate') as mock_generate:
            mock_generate.return_value = "SELECT id, name FROM users WHERE active = true LIMIT 100"
            
            optimized = converter.optimize_sql(sql)
            
            assert "LIMIT" in optimized
            assert optimized != sql
    
    def test_explain_sql(self, converter):
        """Test SQL explanation"""
        sql = "SELECT * FROM users WHERE active = true"
        
        with patch.object(converter.llm_manager, 'generate') as mock_generate:
            mock_generate.return_value = "This query retrieves all active users from the users table."
            
            explanation = converter.explain_sql(sql)
            
            assert "retrieves" in explanation
            assert "users" in explanation


class TestSQLQuery:
    """Test cases for SQLQuery dataclass"""
    
    def test_sql_query_creation(self):
        """Test SQLQuery creation"""
        query = SQLQuery(
            query="SELECT * FROM users",
            query_type="SELECT",
            tables=["users"],
            columns=["*"],
            conditions=[],
            explanation="Retrieves all users",
            confidence=0.9
        )
        
        assert query.query == "SELECT * FROM users"
        assert query.query_type == "SELECT"
        assert query.tables == ["users"]
        assert query.columns == ["*"]
        assert query.conditions == []
        assert query.explanation == "Retrieves all users"
        assert query.confidence == 0.9 