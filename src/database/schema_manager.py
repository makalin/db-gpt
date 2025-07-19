"""
Schema Manager for database schema operations
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SchemaManager:
    """Manages database schema operations and metadata"""
    
    def __init__(self, db_connection):
        self.db_connection = db_connection
        self.schema_cache: Dict[str, Any] = {}
        self._load_schema()
    
    def _load_schema(self):
        """Load database schema"""
        try:
            self.schema_cache = self.db_connection.get_schema()
            logger.info(f"Loaded schema for {len(self.schema_cache)} tables")
        except Exception as e:
            logger.warning(f"Failed to load schema: {e}")
            self.schema_cache = {}
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the current schema"""
        return self.schema_cache
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get schema for a specific table"""
        return self.schema_cache.get(table_name, [])
    
    def list_tables(self) -> List[str]:
        """List all tables in the database"""
        return list(self.schema_cache.keys())
    
    def get_table_columns(self, table_name: str) -> List[str]:
        """Get column names for a table"""
        columns = self.get_table_schema(table_name)
        return [col['column_name'] for col in columns]
    
    def get_column_info(self, table_name: str, column_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific column"""
        columns = self.get_table_schema(table_name)
        for col in columns:
            if col['column_name'] == column_name:
                return col
        return None
    
    def get_primary_keys(self, table_name: str) -> List[str]:
        """Get primary key columns for a table"""
        # This would need to be implemented based on the database type
        # For now, return empty list
        return []
    
    def get_foreign_keys(self, table_name: str) -> List[Dict[str, Any]]:
        """Get foreign key relationships for a table"""
        # This would need to be implemented based on the database type
        # For now, return empty list
        return []
    
    def get_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Get indexes for a table"""
        # This would need to be implemented based on the database type
        # For now, return empty list
        return []
    
    def create_table(self, table_name: str, columns: List[Dict[str, Any]]) -> bool:
        """Create a new table"""
        try:
            # Build CREATE TABLE statement
            column_definitions = []
            for col in columns:
                col_def = f"{col['name']} {col['type']}"
                if not col.get('nullable', True):
                    col_def += " NOT NULL"
                if col.get('default'):
                    col_def += f" DEFAULT {col['default']}"
                column_definitions.append(col_def)
            
            create_sql = f"""
            CREATE TABLE {table_name} (
                {', '.join(column_definitions)}
            )
            """
            
            self.db_connection.execute_query(create_sql)
            
            # Refresh schema cache
            self._load_schema()
            
            logger.info(f"Created table: {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {e}")
            return False
    
    def drop_table(self, table_name: str) -> bool:
        """Drop a table"""
        try:
            drop_sql = f"DROP TABLE {table_name}"
            self.db_connection.execute_query(drop_sql)
            
            # Refresh schema cache
            self._load_schema()
            
            logger.info(f"Dropped table: {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to drop table {table_name}: {e}")
            return False
    
    def add_column(self, table_name: str, column_name: str, column_type: str, 
                  nullable: bool = True, default: Optional[str] = None) -> bool:
        """Add a column to an existing table"""
        try:
            alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            
            if not nullable:
                alter_sql += " NOT NULL"
            
            if default:
                alter_sql += f" DEFAULT {default}"
            
            self.db_connection.execute_query(alter_sql)
            
            # Refresh schema cache
            self._load_schema()
            
            logger.info(f"Added column {column_name} to table {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add column {column_name} to table {table_name}: {e}")
            return False
    
    def drop_column(self, table_name: str, column_name: str) -> bool:
        """Drop a column from a table"""
        try:
            alter_sql = f"ALTER TABLE {table_name} DROP COLUMN {column_name}"
            self.db_connection.execute_query(alter_sql)
            
            # Refresh schema cache
            self._load_schema()
            
            logger.info(f"Dropped column {column_name} from table {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to drop column {column_name} from table {table_name}: {e}")
            return False
    
    def create_index(self, table_name: str, index_name: str, columns: List[str], 
                    unique: bool = False) -> bool:
        """Create an index on a table"""
        try:
            unique_clause = "UNIQUE" if unique else ""
            index_sql = f"CREATE {unique_clause} INDEX {index_name} ON {table_name} ({', '.join(columns)})"
            
            self.db_connection.execute_query(index_sql)
            
            logger.info(f"Created index {index_name} on table {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create index {index_name} on table {table_name}: {e}")
            return False
    
    def drop_index(self, index_name: str) -> bool:
        """Drop an index"""
        try:
            drop_sql = f"DROP INDEX {index_name}"
            self.db_connection.execute_query(drop_sql)
            
            logger.info(f"Dropped index: {index_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to drop index {index_name}: {e}")
            return False
    
    def get_table_size(self, table_name: str) -> Dict[str, Any]:
        """Get size information for a table"""
        try:
            # This would need to be implemented based on the database type
            # For now, return basic information
            columns = self.get_table_schema(table_name)
            
            return {
                'table_name': table_name,
                'column_count': len(columns),
                'estimated_size': 'Unknown',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get table size for {table_name}: {e}")
            return {
                'table_name': table_name,
                'error': str(e)
            }
    
    def validate_schema(self) -> Dict[str, Any]:
        """Validate the database schema"""
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'tables_checked': len(self.schema_cache)
        }
        
        for table_name, columns in self.schema_cache.items():
            # Check for empty tables
            if not columns:
                validation_results['warnings'].append(f"Table {table_name} has no columns")
            
            # Check for duplicate column names
            column_names = [col['column_name'] for col in columns]
            if len(column_names) != len(set(column_names)):
                validation_results['errors'].append(f"Table {table_name} has duplicate column names")
                validation_results['valid'] = False
        
        return validation_results
    
    def export_schema(self, format: str = 'json') -> str:
        """Export schema in various formats"""
        if format.lower() == 'json':
            import json
            return json.dumps(self.schema_cache, indent=2)
        elif format.lower() == 'sql':
            return self._generate_create_statements()
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _generate_create_statements(self) -> str:
        """Generate CREATE TABLE statements for all tables"""
        statements = []
        
        for table_name, columns in self.schema_cache.items():
            column_definitions = []
            for col in columns:
                col_def = f"{col['column_name']} {col['data_type']}"
                if not col['is_nullable']:
                    col_def += " NOT NULL"
                if col['column_default']:
                    col_def += f" DEFAULT {col['column_default']}"
                column_definitions.append(col_def)
            
            create_stmt = f"CREATE TABLE {table_name} (\n"
            create_stmt += ",\n".join(f"  {col_def}" for col_def in column_definitions)
            create_stmt += "\n);"
            
            statements.append(create_stmt)
        
        return "\n\n".join(statements)
    
    def refresh_schema(self):
        """Refresh the schema cache"""
        self._load_schema()
        logger.info("Schema cache refreshed") 