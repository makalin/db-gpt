"""
Query Executor for handling SQL query execution
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class QueryExecutor:
    """Handles SQL query execution and result processing"""
    
    def __init__(self, db_connection):
        self.db_connection = db_connection
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a SQL query and return results
        
        Args:
            query: SQL query to execute
            params: Optional parameters for prepared statements
        
        Returns:
            Dictionary containing query results and metadata
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Executing query: {query[:100]}...")
            
            # Execute the query
            if params:
                # For parameterized queries, we'd need to implement this
                # based on the specific database provider
                results = self.db_connection.execute_query(query)
            else:
                results = self.db_connection.execute_query(query)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Process results
            processed_results = self._process_results(results)
            
            return {
                'success': True,
                'results': processed_results,
                'row_count': len(results),
                'execution_time': execution_time,
                'query': query,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Query execution failed: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'execution_time': execution_time,
                'query': query,
                'timestamp': datetime.now().isoformat()
            }
    
    def _process_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process and clean up query results"""
        processed = []
        
        for row in results:
            processed_row = {}
            for key, value in row.items():
                # Convert datetime objects to strings
                if isinstance(value, datetime):
                    processed_row[key] = value.isoformat()
                else:
                    processed_row[key] = value
            processed.append(processed_row)
        
        return processed
    
    def execute_batch(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Execute multiple queries in batch"""
        results = []
        
        for query in queries:
            result = self.execute_query(query)
            results.append(result)
            
            # Stop on first failure
            if not result['success']:
                break
        
        return results
    
    def execute_transaction(self, queries: List[str]) -> Dict[str, Any]:
        """Execute queries in a transaction"""
        start_time = datetime.now()
        
        try:
            # This would need to be implemented based on the database provider
            # For now, we'll execute them sequentially
            results = []
            
            for query in queries:
                result = self.execute_query(query)
                results.append(result)
                
                if not result['success']:
                    # Rollback would happen here
                    raise Exception(f"Query failed: {result['error']}")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'success': True,
                'results': results,
                'execution_time': execution_time,
                'queries_executed': len(queries),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Transaction failed: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'execution_time': execution_time,
                'queries_executed': len(results),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_query_plan(self, query: str) -> Dict[str, Any]:
        """Get query execution plan"""
        try:
            # This would need to be implemented based on the database type
            # For PostgreSQL: EXPLAIN (FORMAT JSON) query
            # For SQLite: EXPLAIN QUERY PLAN query
            
            explain_query = f"EXPLAIN {query}"
            plan_results = self.db_connection.execute_query(explain_query)
            
            return {
                'success': True,
                'plan': plan_results,
                'query': query
            }
            
        except Exception as e:
            logger.error(f"Failed to get query plan: {e}")
            return {
                'success': False,
                'error': str(e),
                'query': query
            }
    
    def validate_query(self, query: str) -> Dict[str, Any]:
        """Validate a query without executing it"""
        try:
            # Basic syntax validation
            query_upper = query.upper().strip()
            
            # Check for basic SQL keywords
            if not any(keyword in query_upper for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP']):
                return {
                    'valid': False,
                    'error': 'Query must contain a valid SQL command'
                }
            
            # Check for balanced parentheses
            if query.count('(') != query.count(')'):
                return {
                    'valid': False,
                    'error': 'Unbalanced parentheses in query'
                }
            
            # Check for basic structure
            if query_upper.startswith('SELECT') and 'FROM' not in query_upper:
                return {
                    'valid': False,
                    'error': 'SELECT query must contain FROM clause'
                }
            
            return {
                'valid': True,
                'message': 'Query appears to be syntactically valid'
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Validation error: {str(e)}'
            }
    
    def get_table_stats(self, table_name: str) -> Dict[str, Any]:
        """Get statistics about a table"""
        try:
            # Get row count
            count_query = f"SELECT COUNT(*) as row_count FROM {table_name}"
            count_result = self.execute_query(count_query)
            
            if not count_result['success']:
                return count_result
            
            row_count = count_result['results'][0]['row_count']
            
            # Get column information
            schema = self.db_connection.get_schema()
            table_schema = schema.get(table_name, [])
            
            return {
                'success': True,
                'table_name': table_name,
                'row_count': row_count,
                'column_count': len(table_schema),
                'columns': table_schema,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get table stats for {table_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'table_name': table_name
            } 