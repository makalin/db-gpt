"""
Agent Manager for coordinating multiple AI agents
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from ..llm.llm_manager import LLMManager
from ..database.connection import DatabaseConnection
from ..utils.config import Config

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Enumeration of available agent roles"""
    ANALYST = "analyst"
    ENGINEER = "engineer"
    RESEARCHER = "researcher"


@dataclass
class Agent:
    """Represents an AI agent with specific capabilities"""
    name: str
    role: AgentRole
    description: str
    capabilities: List[str]
    is_active: bool = True


class AgentManager:
    """Manages multiple AI agents for collaborative database tasks"""
    
    def __init__(self, config: Dict[str, Any], llm_manager: LLMManager, 
                 db_connection: DatabaseConnection):
        self.config = config
        self.llm_manager = llm_manager
        self.db_connection = db_connection
        self.agents: Dict[str, Agent] = {}
        self.current_objective: Optional[str] = None
        self.task_history: List[Dict[str, Any]] = []
        
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize agents based on configuration"""
        for role_config in self.config.get('roles', []):
            role = AgentRole(role_config['name'])
            agent = Agent(
                name=role_config['name'],
                role=role,
                description=role_config['description'],
                capabilities=role_config['capabilities']
            )
            self.agents[agent.name] = agent
            logger.info(f"Initialized agent: {agent.name} - {agent.description}")
    
    def run(self, objective: str):
        """Main execution loop for the agent system"""
        self.current_objective = objective
        logger.info(f"Starting agent system with objective: {objective}")
        
        # Create initial task
        initial_task = self._create_initial_task(objective)
        self.task_history.append(initial_task)
        
        iteration = 0
        max_iterations = self.config.get('max_iterations', 10)
        
        while iteration < max_iterations:
            logger.info(f"Starting iteration {iteration + 1}/{max_iterations}")
            
            # Get next task
            current_task = self._get_next_task()
            if not current_task:
                logger.info("No more tasks to execute")
                break
            
            # Execute task with appropriate agent
            result = self._execute_task(current_task)
            
            # Create new tasks based on result
            new_tasks = self._create_new_tasks(result)
            self.task_history.extend(new_tasks)
            
            iteration += 1
            
            # Check for completion
            if self._is_objective_complete(result):
                logger.info("Objective completed successfully")
                break
        
        # Generate final summary
        self._generate_summary()
    
    def _create_initial_task(self, objective: str) -> Dict[str, Any]:
        """Create the initial task from the objective"""
        prompt = f"""
        Given the objective: "{objective}"
        
        Break this down into the first task that needs to be completed.
        Consider what database queries, analysis, or setup might be needed.
        
        Return a JSON object with:
        - task_id: unique identifier
        - task_name: descriptive name
        - task_description: detailed description
        - priority: HIGH, MEDIUM, or LOW
        - agent_role: which agent should handle this (analyst, engineer, researcher)
        - expected_output: what should be produced
        """
        
        response = self.llm_manager.generate(prompt)
        # Parse response and create task
        # This is a simplified version - in practice, you'd parse the JSON response
        
        return {
            'task_id': f"task_{len(self.task_history) + 1}",
            'task_name': f"Initial analysis of: {objective}",
            'task_description': f"Begin analysis of the objective: {objective}",
            'priority': 'HIGH',
            'agent_role': 'analyst',
            'expected_output': 'Initial data exploration and query generation',
            'status': 'pending'
        }
    
    def _get_next_task(self) -> Optional[Dict[str, Any]]:
        """Get the next highest priority task"""
        pending_tasks = [task for task in self.task_history if task['status'] == 'pending']
        if not pending_tasks:
            return None
        
        # Sort by priority
        priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        pending_tasks.sort(key=lambda x: priority_order.get(x['priority'], 4))
        
        return pending_tasks[0]
    
    def _execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task using the appropriate agent"""
        logger.info(f"Executing task: {task['task_name']}")
        
        agent_role = task['agent_role']
        agent = self.agents.get(agent_role)
        
        if not agent:
            logger.error(f"No agent found for role: {agent_role}")
            return {'status': 'error', 'message': f'No agent for role {agent_role}'}
        
        # Execute based on agent capabilities
        if 'sql_generation' in agent.capabilities:
            result = self._execute_sql_task(task)
        elif 'data_analysis' in agent.capabilities:
            result = self._execute_analysis_task(task)
        elif 'schema_design' in agent.capabilities:
            result = self._execute_schema_task(task)
        else:
            result = self._execute_general_task(task)
        
        # Update task status
        task['status'] = 'completed'
        task['result'] = result
        
        return result
    
    def _execute_sql_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SQL generation task"""
        prompt = f"""
        Task: {task['task_description']}
        
        Generate SQL queries to accomplish this task. Consider:
        1. What tables might be involved
        2. What data needs to be retrieved or analyzed
        3. Any joins, aggregations, or filtering needed
        
        Return the SQL query and explain what it does.
        """
        
        response = self.llm_manager.generate(prompt)
        
        # In a real implementation, you'd parse the SQL and execute it
        # For now, return the response
        return {
            'type': 'sql_generation',
            'sql_query': response,
            'status': 'success'
        }
    
    def _execute_analysis_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data analysis task"""
        prompt = f"""
        Task: {task['task_description']}
        
        Analyze the data and provide insights. Consider:
        1. Key patterns or trends
        2. Anomalies or outliers
        3. Business implications
        4. Recommendations
        
        Provide a comprehensive analysis.
        """
        
        response = self.llm_manager.generate(prompt)
        
        return {
            'type': 'data_analysis',
            'analysis': response,
            'status': 'success'
        }
    
    def _execute_schema_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute schema design task"""
        prompt = f"""
        Task: {task['task_description']}
        
        Design or optimize database schema. Consider:
        1. Table structure and relationships
        2. Indexing strategies
        3. Data types and constraints
        4. Performance optimization
        
        Provide schema recommendations.
        """
        
        response = self.llm_manager.generate(prompt)
        
        return {
            'type': 'schema_design',
            'schema_recommendations': response,
            'status': 'success'
        }
    
    def _execute_general_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute general task"""
        prompt = f"""
        Task: {task['task_description']}
        
        Provide a comprehensive response to accomplish this task.
        """
        
        response = self.llm_manager.generate(prompt)
        
        return {
            'type': 'general',
            'response': response,
            'status': 'success'
        }
    
    def _create_new_tasks(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create new tasks based on the result of the previous task"""
        prompt = f"""
        Based on the completed task result:
        {result}
        
        And the original objective: {self.current_objective}
        
        What are the next logical tasks that should be created?
        Consider what follow-up actions, deeper analysis, or new directions are needed.
        
        Return a list of new tasks in JSON format.
        """
        
        response = self.llm_manager.generate(prompt)
        
        # In practice, you'd parse the JSON response
        # For now, return an empty list
        return []
    
    def _is_objective_complete(self, result: Dict[str, Any]) -> bool:
        """Check if the objective has been completed"""
        prompt = f"""
        Original objective: {self.current_objective}
        Latest result: {result}
        
        Has the objective been fully completed? Consider:
        1. All required analysis done
        2. All necessary insights generated
        3. All actionable recommendations provided
        
        Answer with just 'YES' or 'NO'.
        """
        
        response = self.llm_manager.generate(prompt)
        return 'YES' in response.upper()
    
    def _generate_summary(self):
        """Generate a final summary of all completed work"""
        logger.info("Generating final summary...")
        
        completed_tasks = [task for task in self.task_history if task['status'] == 'completed']
        
        summary_prompt = f"""
        Original objective: {self.current_objective}
        
        Completed tasks:
        {completed_tasks}
        
        Generate a comprehensive summary of:
        1. What was accomplished
        2. Key findings and insights
        3. Recommendations and next steps
        4. Any limitations or areas for improvement
        """
        
        summary = self.llm_manager.generate(summary_prompt)
        
        logger.info("Final Summary:")
        logger.info(summary)
        
        # Save summary to file
        with open('result_summary.txt', 'w') as f:
            f.write(f"DB-GPT Execution Summary\n")
            f.write(f"Objective: {self.current_objective}\n")
            f.write(f"Tasks completed: {len(completed_tasks)}\n")
            f.write(f"\nSummary:\n{summary}\n") 