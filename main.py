#!/usr/bin/env python3
"""
DB-GPT: BabyAGI with Database Integration
Main entry point for the application
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

from src.core.agent_manager import AgentManager
from src.core.task_manager import TaskManager
from src.database.connection import DatabaseConnection
from src.llm.llm_manager import LLMManager
from src.utils.config import Config

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('db_gpt.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for DB-GPT application"""
    parser = argparse.ArgumentParser(description='DB-GPT: BabyAGI with Database Integration')
    parser.add_argument('--objective', type=str, required=True,
                       help='The main objective for the AI agent')
    parser.add_argument('--config', type=str, default='config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Load configuration
        config = Config(args.config)
        
        # Initialize components
        logger.info("Initializing DB-GPT components...")
        
        # Initialize LLM manager
        llm_manager = LLMManager(config.llm)
        
        # Initialize database connection
        db_connection = DatabaseConnection(config.database)
        
        # Initialize task manager
        task_manager = TaskManager(config.task)
        
        # Initialize agent manager
        agent_manager = AgentManager(config.agent, llm_manager, db_connection)
        
        logger.info(f"Starting DB-GPT with objective: {args.objective}")
        
        # Start the main execution loop
        agent_manager.run(args.objective)
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down gracefully...")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 