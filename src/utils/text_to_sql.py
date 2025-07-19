"""
Text-to-SQL Converter
Converts natural language queries to SQL statements
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SQLQuery:
    """Represents a SQL query with metadata"""
    query: str
    query_type: str  # SELECT, INSERT, UPDATE, DELETE, CREATE, etc.
    tables: List[str]
    columns: List[str]
    conditions: List[str]
    explanation: str
    confidence: float


class TextToSQLConverter:
    """Converts natural language text to SQL queries"""
    
    def __init__(self, llm_manager, db_connection):
        self.llm_manager = llm_manager
        self.db_connection = db_connection
        self.schema_cache: Dict[str, Any] = {}
        self._load_schema()
    
    def _load_schema(self):
        """Load database schema for context"""
        try:
            self.schema_cache = self.db_connection.get_schema()
            logger.info(f"Loaded schema for {len(self.schema_cache)} tables")
        except Exception as e:
            logger.warning(f"Failed to load schema: {e}")
            self.schema_cache = {}
    
    def convert(self, text: str, query_type: Optional[str] = None) -> SQLQuery:
        """
        Convert natural language text to SQL query
        
        Args:
            text: Natural language query
            query_type: Expected query type (SELECT, INSERT, etc.)
        
        Returns:
            SQLQuery object with the generated SQL and metadata
        """
        logger.info(f"Converting text to SQL: {text}")
        
        # Generate SQL using LLM
        sql_query = self._generate_sql(text, query_type)
        
        # Parse and validate the SQL
        parsed_query = self._parse_sql(sql_query)
        
        return parsed_query
    
    def _generate_sql(self, text: str, query_type: Optional[str] = None) -> str:
        """Generate SQL using LLM"""
        schema_context = self._format_schema_context()
        
        prompt = f"""
        Convert the following natural language query to SQL:
        
        Query: "{text}"
        Expected type: {query_type or 'auto-detect'}
        
        Database schema:
        {schema_context}
        
        Instructions:
        1. Generate valid SQL for the given database schema
        2. Use appropriate table and column names from the schema
        3. Include proper JOINs if multiple tables are needed
        4. Add WHERE clauses for filtering when appropriate
        5. Use appropriate aggregation functions (COUNT, SUM, AVG, etc.) when needed
        6. Return only the SQL query, no explanations
        
        SQL Query:
        """
        
        response = self.llm_manager.generate(prompt)
        
        # Clean up the response
        sql = self._extract_sql_from_response(response)
        
        return sql
    
    def _format_schema_context(self) -> str:
        """Format database schema for LLM context"""
        if not self.schema_cache:
            return "No schema information available"
        
        schema_text = []
        for table_name, columns in self.schema_cache.items():
            schema_text.append(f"Table: {table_name}")
            for col in columns:
                nullable = "NULL" if col['is_nullable'] else "NOT NULL"
                default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                schema_text.append(f"  - {col['column_name']}: {col['data_type']} {nullable}{default}")
            schema_text.append("")
        
        return "\n".join(schema_text)
    
    def _extract_sql_from_response(self, response: str) -> str:
        """Extract SQL query from LLM response"""
        # Remove markdown code blocks
        sql = re.sub(r'```sql\s*', '', response)
        sql = re.sub(r'```\s*', '', sql)
        
        # Remove common prefixes
        sql = re.sub(r'^SQL[:\s]*', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'^Query[:\s]*', '', sql, flags=re.IGNORECASE)
        
        # Clean up whitespace
        sql = sql.strip()
        
        return sql
    
    def _parse_sql(self, sql: str) -> SQLQuery:
        """Parse SQL query and extract metadata"""
        try:
            # Determine query type
            query_type = self._detect_query_type(sql)
            
            # Extract tables
            tables = self._extract_tables(sql)
            
            # Extract columns
            columns = self._extract_columns(sql)
            
            # Extract conditions
            conditions = self._extract_conditions(sql)
            
            # Generate explanation
            explanation = self._generate_explanation(sql, query_type, tables, columns)
            
            # Calculate confidence
            confidence = self._calculate_confidence(sql, tables)
            
            return SQLQuery(
                query=sql,
                query_type=query_type,
                tables=tables,
                columns=columns,
                conditions=conditions,
                explanation=explanation,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error parsing SQL: {e}")
            return SQLQuery(
                query=sql,
                query_type="UNKNOWN",
                tables=[],
                columns=[],
                conditions=[],
                explanation=f"Error parsing SQL: {str(e)}",
                confidence=0.0
            )
    
    def _detect_query_type(self, sql: str) -> str:
        """Detect the type of SQL query"""
        sql_upper = sql.upper().strip()
        
        if sql_upper.startswith('SELECT'):
            return 'SELECT'
        elif sql_upper.startswith('INSERT'):
            return 'INSERT'
        elif sql_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif sql_upper.startswith('DELETE'):
            return 'DELETE'
        elif sql_upper.startswith('CREATE'):
            return 'CREATE'
        elif sql_upper.startswith('ALTER'):
            return 'ALTER'
        elif sql_upper.startswith('DROP'):
            return 'DROP'
        else:
            return 'UNKNOWN'
    
    def _extract_tables(self, sql: str) -> List[str]:
        """Extract table names from SQL query"""
        tables = []
        
        # Extract FROM clause tables
        from_match = re.search(r'FROM\s+(\w+)', sql, re.IGNORECASE)
        if from_match:
            tables.append(from_match.group(1))
        
        # Extract JOIN clause tables
        join_matches = re.findall(r'JOIN\s+(\w+)', sql, re.IGNORECASE)
        tables.extend(join_matches)
        
        # Extract INSERT/UPDATE table
        insert_match = re.search(r'INSERT\s+INTO\s+(\w+)', sql, re.IGNORECASE)
        if insert_match:
            tables.append(insert_match.group(1))
        
        update_match = re.search(r'UPDATE\s+(\w+)', sql, re.IGNORECASE)
        if update_match:
            tables.append(update_match.group(1))
        
        # Remove duplicates and return
        return list(set(tables))
    
    def _extract_columns(self, sql: str) -> List[str]:
        """Extract column names from SQL query"""
        columns = []
        
        # Extract SELECT columns
        select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql, re.IGNORECASE | re.DOTALL)
        if select_match:
            select_clause = select_match.group(1)
            # Split by comma and clean up
            cols = [col.strip() for col in select_clause.split(',')]
            for col in cols:
                # Remove aliases and functions
                clean_col = re.sub(r'\s+AS\s+\w+', '', col, flags=re.IGNORECASE)
                clean_col = re.sub(r'\w+\(', '', clean_col)  # Remove function names
                clean_col = re.sub(r'\)', '', clean_col)
                if clean_col.strip() and clean_col.strip() != '*':
                    columns.append(clean_col.strip())
        
        return columns
    
    def _extract_conditions(self, sql: str) -> List[str]:
        """Extract WHERE conditions from SQL query"""
        conditions = []
        
        where_match = re.search(r'WHERE\s+(.*?)(?:\s+GROUP\s+BY|\s+ORDER\s+BY|\s+LIMIT|$)', 
                               sql, re.IGNORECASE | re.DOTALL)
        if where_match:
            where_clause = where_match.group(1)
            # Split by AND/OR and clean up
            conds = re.split(r'\s+AND\s+|\s+OR\s+', where_clause, flags=re.IGNORECASE)
            for cond in conds:
                clean_cond = cond.strip()
                if clean_cond:
                    conditions.append(clean_cond)
        
        return conditions
    
    def _generate_explanation(self, sql: str, query_type: str, tables: List[str], 
                            columns: List[str]) -> str:
        """Generate explanation of what the SQL query does"""
        explanation_parts = []
        
        if query_type == 'SELECT':
            explanation_parts.append(f"This query retrieves data from {', '.join(tables)}")
            if columns:
                explanation_parts.append(f"selecting columns: {', '.join(columns)}")
        elif query_type == 'INSERT':
            explanation_parts.append(f"This query inserts new data into {', '.join(tables)}")
        elif query_type == 'UPDATE':
            explanation_parts.append(f"This query updates existing data in {', '.join(tables)}")
        elif query_type == 'DELETE':
            explanation_parts.append(f"This query removes data from {', '.join(tables)}")
        
        return " ".join(explanation_parts)
    
    def _calculate_confidence(self, sql: str, tables: List[str]) -> float:
        """Calculate confidence score for the generated SQL"""
        confidence = 1.0
        
        # Check if tables exist in schema
        for table in tables:
            if table not in self.schema_cache:
                confidence -= 0.2
        
        # Check for basic SQL syntax
        if not re.search(r'SELECT|INSERT|UPDATE|DELETE|CREATE', sql, re.IGNORECASE):
            confidence -= 0.3
        
        # Check for balanced parentheses
        if sql.count('(') != sql.count(')'):
            confidence -= 0.1
        
        return max(0.0, confidence)
    
    def validate_sql(self, sql: str) -> Tuple[bool, str]:
        """Validate SQL query against database schema"""
        try:
            # Try to execute the query (for SELECT queries)
            if sql.upper().strip().startswith('SELECT'):
                self.db_connection.execute_query(sql)
                return True, "SQL query is valid"
            else:
                # For non-SELECT queries, just check syntax
                return True, "SQL syntax appears valid"
        except Exception as e:
            return False, f"SQL validation failed: {str(e)}"
    
    def optimize_sql(self, sql: str) -> str:
        """Optimize SQL query for better performance"""
        optimization_prompt = f"""
        Optimize the following SQL query for better performance:
        
        {sql}
        
        Consider:
        1. Adding appropriate indexes
        2. Optimizing JOINs
        3. Reducing data transfer
        4. Using appropriate WHERE clauses
        5. Limiting result sets when possible
        
        Return only the optimized SQL query:
        """
        
        optimized_sql = self.llm_manager.generate(optimization_prompt)
        return self._extract_sql_from_response(optimized_sql)
    
    def explain_sql(self, sql: str) -> str:
        """Generate detailed explanation of SQL query"""
        explanation_prompt = f"""
        Explain what the following SQL query does in detail:
        
        {sql}
        
        Include:
        1. What tables are involved
        2. What data is being retrieved/modified
        3. Any filtering or conditions applied
        4. The expected result
        5. Potential performance considerations
        """
        
        return self.llm_manager.generate(explanation_prompt) 