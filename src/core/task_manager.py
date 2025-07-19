"""
Task Manager for handling task lifecycle
"""

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class TaskStatus(Enum):
    """Task status states"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Represents a task in the system"""
    task_id: str
    task_name: str
    task_description: str
    priority: TaskPriority
    agent_role: str
    expected_output: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class TaskManager:
    """Manages task creation, prioritization, and execution tracking"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.tasks: List[Task] = []
        self.task_counter = 0
        self.task_list_file = config.get('task_list_file', 'task_list.json')
        self.result_summary_file = config.get('result_summary_file', 'result_summary.json')
        
        self._load_tasks()
    
    def _load_tasks(self):
        """Load tasks from file if it exists"""
        try:
            with open(self.task_list_file, 'r') as f:
                task_data = json.load(f)
                for task_dict in task_data:
                    task = self._dict_to_task(task_dict)
                    self.tasks.append(task)
                    self.task_counter = max(self.task_counter, int(task.task_id.split('_')[1]))
        except FileNotFoundError:
            logger.info("No existing task file found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading tasks: {e}")
    
    def _save_tasks(self):
        """Save tasks to file"""
        try:
            task_data = [asdict(task) for task in self.tasks]
            # Convert datetime objects to strings for JSON serialization
            for task_dict in task_data:
                if task_dict['created_at']:
                    task_dict['created_at'] = task_dict['created_at'].isoformat()
                if task_dict['started_at']:
                    task_dict['started_at'] = task_dict['started_at'].isoformat()
                if task_dict['completed_at']:
                    task_dict['completed_at'] = task_dict['completed_at'].isoformat()
            
            with open(self.task_list_file, 'w') as f:
                json.dump(task_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving tasks: {e}")
    
    def _dict_to_task(self, task_dict: Dict[str, Any]) -> Task:
        """Convert dictionary to Task object"""
        # Convert string dates back to datetime objects
        if task_dict.get('created_at'):
            task_dict['created_at'] = datetime.fromisoformat(task_dict['created_at'])
        if task_dict.get('started_at'):
            task_dict['started_at'] = datetime.fromisoformat(task_dict['started_at'])
        if task_dict.get('completed_at'):
            task_dict['completed_at'] = datetime.fromisoformat(task_dict['completed_at'])
        
        # Convert string enums back to enum objects
        task_dict['priority'] = TaskPriority(task_dict['priority'])
        task_dict['status'] = TaskStatus(task_dict['status'])
        
        return Task(**task_dict)
    
    def create_task(self, task_name: str, task_description: str, 
                   priority: TaskPriority, agent_role: str, 
                   expected_output: str) -> Task:
        """Create a new task"""
        self.task_counter += 1
        task_id = f"task_{self.task_counter}"
        
        task = Task(
            task_id=task_id,
            task_name=task_name,
            task_description=task_description,
            priority=priority,
            agent_role=agent_role,
            expected_output=expected_output
        )
        
        self.tasks.append(task)
        self._save_tasks()
        
        logger.info(f"Created task: {task_id} - {task_name}")
        return task
    
    def get_next_task(self) -> Optional[Task]:
        """Get the next highest priority pending task"""
        pending_tasks = [task for task in self.tasks if task.status == TaskStatus.PENDING]
        
        if not pending_tasks:
            return None
        
        # Sort by priority
        priority_order = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3
        }
        
        pending_tasks.sort(key=lambda x: priority_order.get(x.priority, 4))
        return pending_tasks[0]
    
    def start_task(self, task_id: str) -> bool:
        """Mark a task as in progress"""
        task = self._get_task_by_id(task_id)
        if not task:
            logger.error(f"Task not found: {task_id}")
            return False
        
        if task.status != TaskStatus.PENDING:
            logger.warning(f"Task {task_id} is not in pending status: {task.status}")
            return False
        
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now()
        self._save_tasks()
        
        logger.info(f"Started task: {task_id}")
        return True
    
    def complete_task(self, task_id: str, result: Dict[str, Any]) -> bool:
        """Mark a task as completed with results"""
        task = self._get_task_by_id(task_id)
        if not task:
            logger.error(f"Task not found: {task_id}")
            return False
        
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        task.result = result
        self._save_tasks()
        
        logger.info(f"Completed task: {task_id}")
        return True
    
    def fail_task(self, task_id: str, error_message: str) -> bool:
        """Mark a task as failed"""
        task = self._get_task_by_id(task_id)
        if not task:
            logger.error(f"Task not found: {task_id}")
            return False
        
        task.status = TaskStatus.FAILED
        task.completed_at = datetime.now()
        task.error_message = error_message
        self._save_tasks()
        
        logger.error(f"Failed task: {task_id} - {error_message}")
        return True
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        task = self._get_task_by_id(task_id)
        if not task:
            logger.error(f"Task not found: {task_id}")
            return False
        
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now()
        self._save_tasks()
        
        logger.info(f"Cancelled task: {task_id}")
        return True
    
    def _get_task_by_id(self, task_id: str) -> Optional[Task]:
        """Get a task by its ID"""
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        return None
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get the status of a task"""
        task = self._get_task_by_id(task_id)
        return task.status if task else None
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Get all tasks with a specific status"""
        return [task for task in self.tasks if task.status == status]
    
    def get_tasks_by_priority(self, priority: TaskPriority) -> List[Task]:
        """Get all tasks with a specific priority"""
        return [task for task in self.tasks if task.priority == priority]
    
    def get_tasks_by_agent(self, agent_role: str) -> List[Task]:
        """Get all tasks assigned to a specific agent"""
        return [task for task in self.tasks if task.agent_role == agent_role]
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """Get statistics about tasks"""
        total_tasks = len(self.tasks)
        completed_tasks = len(self.get_tasks_by_status(TaskStatus.COMPLETED))
        failed_tasks = len(self.get_tasks_by_status(TaskStatus.FAILED))
        pending_tasks = len(self.get_tasks_by_status(TaskStatus.PENDING))
        in_progress_tasks = len(self.get_tasks_by_status(TaskStatus.IN_PROGRESS))
        
        priority_stats = {}
        for priority in TaskPriority:
            priority_stats[priority.value] = len(self.get_tasks_by_priority(priority))
        
        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'failed_tasks': failed_tasks,
            'pending_tasks': pending_tasks,
            'in_progress_tasks': in_progress_tasks,
            'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            'priority_distribution': priority_stats
        }
    
    def save_result_summary(self, objective: str, summary: str):
        """Save the final result summary"""
        summary_data = {
            'objective': objective,
            'summary': summary,
            'statistics': self.get_task_statistics(),
            'completed_at': datetime.now().isoformat()
        }
        
        try:
            with open(self.result_summary_file, 'w') as f:
                json.dump(summary_data, f, indent=2)
            logger.info("Result summary saved")
        except Exception as e:
            logger.error(f"Error saving result summary: {e}")
    
    def clear_completed_tasks(self):
        """Clear completed tasks from memory (keep in file)"""
        self.tasks = [task for task in self.tasks if task.status != TaskStatus.COMPLETED]
        logger.info("Cleared completed tasks from memory")
    
    def reset_all_tasks(self):
        """Reset all tasks to pending status"""
        for task in self.tasks:
            task.status = TaskStatus.PENDING
            task.started_at = None
            task.completed_at = None
            task.result = None
            task.error_message = None
        
        self._save_tasks()
        logger.info("Reset all tasks to pending status") 