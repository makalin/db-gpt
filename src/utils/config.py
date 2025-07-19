"""
Configuration Manager for DB-GPT
Handles loading and validation of configuration settings
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager for DB-GPT"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config_data: Dict[str, Any] = {}
        self._load_config()
        self._validate_config()
    
    def _load_config(self):
        """Load configuration from YAML file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config_data = yaml.safe_load(f) or {}
                logger.info(f"Loaded configuration from {self.config_path}")
            else:
                logger.warning(f"Configuration file {self.config_path} not found, using defaults")
                self.config_data = self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self.config_data = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'llm': {
                'provider': 'openai',
                'model': 'gpt-4',
                'api_key': '${OPENAI_API_KEY}',
                'max_tokens': 2048,
                'temperature': 0.7,
                'timeout': 30
            },
            'database': {
                'type': 'sqlite',
                'database_path': 'db_gpt.db'
            },
            'vector_store': {
                'provider': 'chroma',
                'index_name': 'db-gpt-tasks',
                'dimension': 1536
            },
            'agent': {
                'max_iterations': 10,
                'max_consecutive_auto_reply': 3,
                'human_input_mode': 'NEVER'
            },
            'task': {
                'max_tasks': 100,
                'task_list_file': 'task_list.json',
                'result_summary_file': 'result_summary.json'
            },
            'logging': {
                'level': 'INFO',
                'file': 'db_gpt.log',
                'max_size': '10MB',
                'backup_count': 5
            }
        }
    
    def _validate_config(self):
        """Validate configuration settings"""
        required_sections = ['llm', 'database', 'agent', 'task']
        
        for section in required_sections:
            if section not in self.config_data:
                logger.warning(f"Missing configuration section: {section}")
                self.config_data[section] = {}
        
        # Validate LLM configuration
        llm_config = self.config_data.get('llm', {})
        if llm_config.get('provider') == 'openai':
            if not llm_config.get('api_key') and not os.getenv('OPENAI_API_KEY'):
                logger.warning("OpenAI API key not found in configuration or environment")
        
        # Validate database configuration
        db_config = self.config_data.get('database', {})
        if db_config.get('type') == 'postgresql':
            required_db_vars = ['username', 'password', 'database']
            for var in required_db_vars:
                if not db_config.get(var) and not os.getenv(f'DB_{var.upper()}'):
                    logger.warning(f"Database {var} not found in configuration or environment")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation)"""
        keys = key.split('.')
        value = self.config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value by key (supports dot notation)"""
        keys = key.split('.')
        config = self.config_data
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self, config_path: Optional[str] = None):
        """Save configuration to file"""
        save_path = config_path or self.config_path
        
        try:
            with open(save_path, 'w') as f:
                yaml.dump(self.config_data, f, default_flow_style=False, indent=2)
            logger.info(f"Configuration saved to {save_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def reload(self):
        """Reload configuration from file"""
        self._load_config()
        self._validate_config()
    
    @property
    def llm(self) -> Dict[str, Any]:
        """Get LLM configuration"""
        return self.config_data.get('llm', {})
    
    @property
    def database(self) -> Dict[str, Any]:
        """Get database configuration"""
        return self.config_data.get('database', {})
    
    @property
    def vector_store(self) -> Dict[str, Any]:
        """Get vector store configuration"""
        return self.config_data.get('vector_store', {})
    
    @property
    def agent(self) -> Dict[str, Any]:
        """Get agent configuration"""
        return self.config_data.get('agent', {})
    
    @property
    def task(self) -> Dict[str, Any]:
        """Get task configuration"""
        return self.config_data.get('task', {})
    
    @property
    def logging(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return self.config_data.get('logging', {})
    
    @property
    def security(self) -> Dict[str, Any]:
        """Get security configuration"""
        return self.config_data.get('security', {})
    
    @property
    def performance(self) -> Dict[str, Any]:
        """Get performance configuration"""
        return self.config_data.get('performance', {})
    
    def resolve_environment_variables(self, value: str) -> str:
        """Resolve environment variables in configuration values"""
        if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
            env_var = value[2:-1]
            return os.getenv(env_var, value)
        return value
    
    def get_resolved_config(self) -> Dict[str, Any]:
        """Get configuration with environment variables resolved"""
        def resolve_dict(d: Dict[str, Any]) -> Dict[str, Any]:
            resolved = {}
            for key, value in d.items():
                if isinstance(value, dict):
                    resolved[key] = resolve_dict(value)
                elif isinstance(value, str):
                    resolved[key] = self.resolve_environment_variables(value)
                else:
                    resolved[key] = value
            return resolved
        
        return resolve_dict(self.config_data)
    
    def validate_required_settings(self) -> bool:
        """Validate that all required settings are present"""
        resolved_config = self.get_resolved_config()
        
        # Check LLM settings
        llm_config = resolved_config.get('llm', {})
        if llm_config.get('provider') == 'openai':
            if not llm_config.get('api_key'):
                logger.error("OpenAI API key is required")
                return False
        
        # Check database settings
        db_config = resolved_config.get('database', {})
        if db_config.get('type') == 'postgresql':
            required_db_settings = ['username', 'password', 'database']
            for setting in required_db_settings:
                if not db_config.get(setting):
                    logger.error(f"Database {setting} is required for PostgreSQL")
                    return False
        
        return True
    
    def get_database_url(self) -> Optional[str]:
        """Get the database connection URL"""
        db_config = self.database
        db_type = db_config.get('type', 'sqlite')
        
        if db_type == 'postgresql':
            username = self.resolve_environment_variables(db_config.get('username', ''))
            password = self.resolve_environment_variables(db_config.get('password', ''))
            host = db_config.get('host', 'localhost')
            port = db_config.get('port', 5432)
            database = self.resolve_environment_variables(db_config.get('database', ''))
            
            if all([username, password, database]):
                return f"postgresql://{username}:{password}@{host}:{port}/{database}"
        
        elif db_type == 'sqlite':
            database_path = db_config.get('database_path', 'db_gpt.db')
            return f"sqlite:///{database_path}"
        
        return None 