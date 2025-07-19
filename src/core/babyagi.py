"""
BabyAGI Core Implementation
Provides the foundational task execution framework
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from ..llm.llm_manager import LLMManager
from ..database.connection import DatabaseConnection
from .task_manager import TaskManager, Task, TaskPriority, TaskStatus

logger = logging.getLogger(__name__)


@dataclass
class BabyAGIConfig:
    """Configuration for BabyAGI"""
    max_iterations: int = 10
    max_consecutive_auto_reply: int = 3
    human_input_mode: str = "NEVER"  # NEVER, ALWAYS, TERMINATE
    task_list_file: str = "task_list.json"
    result_summary_file: str = "result_summary.json"


class BabyAGI:
    """
    BabyAGI: An AI agent that can generate and execute tasks based on an objective
    """
    
    def __init__(self, config: BabyAGIConfig, llm_manager: LLMManager, 
                 db_connection: DatabaseConnection):
        self.config = config
        self.llm_manager = llm_manager
        self.db_connection = db_connection
        self.task_manager = TaskManager({
            'task_list_file': config.task_list_file,
            'result_summary_file': config.result_summary_file
        })
        
        self.objective: Optional[str] = None
        self.task_list: List[Dict[str, Any]] = []
        self.result_summary: List[Dict[str, Any]] = []
        self.current_task_id = 1
    
    def run(self, objective: str):
        """
        Run the BabyAGI agent with a given objective
        
        Args:
            objective (str): The main objective to accomplish
        """
        self.objective = objective
        logger.info(f"Starting BabyAGI with objective: {objective}")
        
        # Create the first task
        first_task = self._create_first_task(objective)
        self.task_list.append(first_task)
        
        # Main execution loop
        iteration = 0
        consecutive_auto_reply = 0
        
        while iteration < self.config.max_iterations:
            logger.info(f"Starting iteration {iteration + 1}/{self.config.max_iterations}")
            
            # Get the next task
            if not self.task_list:
                logger.info("No more tasks to execute")
                break
            
            current_task = self.task_list[0]
            task_id = current_task['task_id']
            
            # Execute the task
            logger.info(f"Executing task {task_id}: {current_task['task_name']}")
            result = self._execute_task(current_task)
            
            # Add result to summary
            self.result_summary.append({
                'task_id': task_id,
                'task_name': current_task['task_name'],
                'result': result,
                'timestamp': datetime.now().isoformat()
            })
            
            # Remove the completed task
            self.task_list.pop(0)
            
            # Create new tasks based on the result
            new_tasks = self._create_new_tasks(result)
            self.task_list.extend(new_tasks)
            
            # Check if we should ask for human input
            if self.config.human_input_mode == "ALWAYS":
                user_input = input("Press Enter to continue or type 'stop' to end: ")
                if user_input.lower() == 'stop':
                    break
            elif self.config.human_input_mode == "TERMINATE":
                if consecutive_auto_reply >= self.config.max_consecutive_auto_reply:
                    user_input = input("Press Enter to continue or type 'stop' to end: ")
                    if user_input.lower() == 'stop':
                        break
                    consecutive_auto_reply = 0
                else:
                    consecutive_auto_reply += 1
            
            iteration += 1
            
            # Check if objective is complete
            if self._is_objective_complete(result):
                logger.info("Objective completed successfully")
                break
        
        # Generate final summary
        self._generate_final_summary()
    
    def _create_first_task(self, objective: str) -> Dict[str, Any]:
        """Create the first task based on the objective"""
        prompt = f"""
        Given the objective: "{objective}"
        
        Create the first task that needs to be completed to achieve this objective.
        Consider what initial analysis, data gathering, or setup might be needed.
        
        Return a JSON object with:
        - task_id: "task_1"
        - task_name: descriptive name
        - task_description: detailed description
        - priority: "HIGH"
        - agent_role: "analyst"
        - expected_output: what should be produced
        """
        
        response = self.llm_manager.generate(prompt)
        
        # In a real implementation, you'd parse the JSON response
        # For now, create a basic task structure
        return {
            'task_id': 'task_1',
            'task_name': f'Initial analysis of: {objective}',
            'task_description': f'Begin analysis of the objective: {objective}',
            'priority': 'HIGH',
            'agent_role': 'analyst',
            'expected_output': 'Initial data exploration and query generation'
        }
    
    def _execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single task"""
        task_description = task['task_description']
        
        # Generate SQL query if needed
        if 'database' in task_description.lower() or 'query' in task_description.lower():
            sql_prompt = f"""
            Task: {task_description}
            
            Generate SQL queries to accomplish this task. Consider:
            1. What tables might be involved
            2. What data needs to be retrieved or analyzed
            3. Any joins, aggregations, or filtering needed
            
            Return the SQL query and explain what it does.
            """
            
            sql_response = self.llm_manager.generate(sql_prompt)
            
            # In a real implementation, you'd execute the SQL
            # For now, return the generated query
            return {
                'type': 'sql_generation',
                'sql_query': sql_response,
                'status': 'success',
                'timestamp': datetime.now().isoformat()
            }
        
        # General task execution
        general_prompt = f"""
        Task: {task_description}
        
        Provide a comprehensive response to accomplish this task.
        Consider the objective: {self.objective}
        
        Include:
        1. Analysis of the task requirements
        2. Steps taken to complete the task
        3. Results and findings
        4. Any recommendations or next steps
        """
        
        response = self.llm_manager.generate(general_prompt)
        
        return {
            'type': 'general_task',
            'response': response,
            'status': 'success',
            'timestamp': datetime.now().isoformat()
        }
    
    def _create_new_tasks(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create new tasks based on the result of the previous task"""
        prompt = f"""
        Based on the completed task result:
        {result}
        
        And the original objective: {self.objective}
        
        What are the next logical tasks that should be created?
        Consider what follow-up actions, deeper analysis, or new directions are needed.
        
        Return a list of new tasks in JSON format. Each task should have:
        - task_id: "task_X" (increment from current task)
        - task_name: descriptive name
        - task_description: detailed description
        - priority: HIGH, MEDIUM, or LOW
        - agent_role: analyst, engineer, or researcher
        - expected_output: what should be produced
        """
        
        response = self.llm_manager.generate(prompt)
        
        # In practice, you'd parse the JSON response
        # For now, create a simple follow-up task
        self.current_task_id += 1
        
        return [{
            'task_id': f'task_{self.current_task_id}',
            'task_name': f'Follow-up analysis based on previous results',
            'task_description': f'Analyze the results from the previous task and provide deeper insights',
            'priority': 'MEDIUM',
            'agent_role': 'analyst',
            'expected_output': 'Detailed analysis and recommendations'
        }]
    
    def _is_objective_complete(self, result: Dict[str, Any]) -> bool:
        """Check if the objective has been completed"""
        prompt = f"""
        Original objective: {self.objective}
        Latest result: {result}
        
        Has the objective been fully completed? Consider:
        1. All required analysis done
        2. All necessary insights generated
        3. All actionable recommendations provided
        
        Answer with just 'YES' or 'NO'.
        """
        
        response = self.llm_manager.generate(prompt)
        return 'YES' in response.upper()
    
    def _generate_final_summary(self):
        """Generate a final summary of all completed work"""
        logger.info("Generating final summary...")
        
        summary_prompt = f"""
        Original objective: {self.objective}
        
        Completed tasks and results:
        {self.result_summary}
        
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
        with open(self.config.result_summary_file, 'w') as f:
            f.write(f"BabyAGI Execution Summary\n")
            f.write(f"Objective: {self.objective}\n")
            f.write(f"Tasks completed: {len(self.result_summary)}\n")
            f.write(f"\nSummary:\n{summary}\n")
        
        # Also save detailed results
        import json
        detailed_results = {
            'objective': self.objective,
            'tasks_completed': len(self.result_summary),
            'summary': summary,
            'detailed_results': self.result_summary,
            'completed_at': datetime.now().isoformat()
        }
        
        with open('detailed_results.json', 'w') as f:
            json.dump(detailed_results, f, indent=2)
    
    def get_task_list(self) -> List[Dict[str, Any]]:
        """Get the current task list"""
        return self.task_list
    
    def get_result_summary(self) -> List[Dict[str, Any]]:
        """Get the result summary"""
        return self.result_summary
    
    def add_task(self, task: Dict[str, Any]):
        """Add a new task to the list"""
        self.task_list.append(task)
        logger.info(f"Added task: {task['task_name']}")
    
    def clear_task_list(self):
        """Clear the task list"""
        self.task_list.clear()
        logger.info("Cleared task list")
    
    def reset(self):
        """Reset the BabyAGI instance"""
        self.objective = None
        self.task_list.clear()
        self.result_summary.clear()
        self.current_task_id = 1
        logger.info("Reset BabyAGI instance") 