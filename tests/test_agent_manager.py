"""
Unit tests for Agent Manager
"""

import pytest
from unittest.mock import Mock, patch
from src.core.agent_manager import AgentManager, Agent, AgentRole


class TestAgentManager:
    """Test cases for AgentManager class"""
    
    @pytest.fixture
    def mock_llm_manager(self):
        """Create a mock LLM manager"""
        mock = Mock()
        mock.generate.return_value = "Mock response"
        return mock
    
    @pytest.fixture
    def mock_db_connection(self):
        """Create a mock database connection"""
        mock = Mock()
        mock.get_schema.return_value = {}
        return mock
    
    @pytest.fixture
    def agent_config(self):
        """Sample agent configuration"""
        return {
            'max_iterations': 5,
            'roles': [
                {
                    'name': 'analyst',
                    'description': 'Data analyst for business intelligence',
                    'capabilities': ['sql_generation', 'data_analysis']
                },
                {
                    'name': 'engineer',
                    'description': 'Database engineer',
                    'capabilities': ['schema_design', 'query_optimization']
                }
            ]
        }
    
    @pytest.fixture
    def agent_manager(self, mock_llm_manager, mock_db_connection, agent_config):
        """Create an AgentManager instance for testing"""
        return AgentManager(agent_config, mock_llm_manager, mock_db_connection)
    
    def test_agent_manager_initialization(self, agent_manager, agent_config):
        """Test AgentManager initialization"""
        assert agent_manager.config == agent_config
        assert len(agent_manager.agents) == 2
        assert 'analyst' in agent_manager.agents
        assert 'engineer' in agent_manager.agents
    
    def test_agent_creation(self, agent_manager):
        """Test agent creation with correct attributes"""
        analyst_agent = agent_manager.agents['analyst']
        assert analyst_agent.name == 'analyst'
        assert analyst_agent.role == AgentRole.ANALYST
        assert 'sql_generation' in analyst_agent.capabilities
        assert analyst_agent.is_active is True
    
    def test_run_method_creates_initial_task(self, agent_manager):
        """Test that run method creates initial task"""
        objective = "Analyze sales data"
        
        with patch.object(agent_manager, '_create_initial_task') as mock_create:
            mock_create.return_value = {
                'task_id': 'task_1',
                'task_name': 'Initial analysis',
                'task_description': 'Begin analysis',
                'priority': 'HIGH',
                'agent_role': 'analyst',
                'expected_output': 'Initial results',
                'status': 'pending'
            }
            
            agent_manager.run(objective)
            
            assert agent_manager.current_objective == objective
            mock_create.assert_called_once_with(objective)
    
    def test_get_next_task_returns_highest_priority(self, agent_manager):
        """Test that get_next_task returns highest priority task"""
        # Add tasks with different priorities
        agent_manager.task_history = [
            {
                'task_id': 'task_1',
                'priority': 'LOW',
                'status': 'pending'
            },
            {
                'task_id': 'task_2',
                'priority': 'HIGH',
                'status': 'pending'
            },
            {
                'task_id': 'task_3',
                'priority': 'MEDIUM',
                'status': 'pending'
            }
        ]
        
        next_task = agent_manager._get_next_task()
        assert next_task['task_id'] == 'task_2'  # HIGH priority
    
    def test_execute_task_with_analyst(self, agent_manager):
        """Test task execution with analyst agent"""
        task = {
            'task_name': 'Analyze data',
            'task_description': 'Perform data analysis',
            'agent_role': 'analyst'
        }
        
        with patch.object(agent_manager, '_execute_analysis_task') as mock_execute:
            mock_execute.return_value = {'type': 'analysis', 'status': 'success'}
            
            result = agent_manager._execute_task(task)
            
            assert result['type'] == 'analysis'
            assert result['status'] == 'success'
            mock_execute.assert_called_once_with(task)
    
    def test_execute_task_with_engineer(self, agent_manager):
        """Test task execution with engineer agent"""
        task = {
            'task_name': 'Design schema',
            'task_description': 'Design database schema',
            'agent_role': 'engineer'
        }
        
        with patch.object(agent_manager, '_execute_schema_task') as mock_execute:
            mock_execute.return_value = {'type': 'schema_design', 'status': 'success'}
            
            result = agent_manager._execute_task(task)
            
            assert result['type'] == 'schema_design'
            assert result['status'] == 'success'
            mock_execute.assert_called_once_with(task)
    
    def test_execute_task_with_unknown_agent(self, agent_manager):
        """Test task execution with unknown agent role"""
        task = {
            'task_name': 'Unknown task',
            'task_description': 'Task with unknown agent',
            'agent_role': 'unknown_agent'
        }
        
        result = agent_manager._execute_task(task)
        
        assert result['status'] == 'error'
        assert 'No agent for role unknown_agent' in result['message']
    
    def test_create_initial_task(self, agent_manager):
        """Test initial task creation"""
        objective = "Analyze customer data"
        
        with patch.object(agent_manager.llm_manager, 'generate') as mock_generate:
            mock_generate.return_value = "Mock SQL query"
            
            task = agent_manager._create_initial_task(objective)
            
            assert task['task_name'] == f'Initial analysis of: {objective}'
            assert task['priority'] == 'HIGH'
            assert task['agent_role'] == 'analyst'
            assert task['status'] == 'pending'
    
    def test_is_objective_complete_returns_true(self, agent_manager):
        """Test objective completion check returns True"""
        agent_manager.current_objective = "Analyze data"
        result = {'type': 'analysis', 'status': 'success'}
        
        with patch.object(agent_manager.llm_manager, 'generate') as mock_generate:
            mock_generate.return_value = "YES"
            
            is_complete = agent_manager._is_objective_complete(result)
            
            assert is_complete is True
    
    def test_is_objective_complete_returns_false(self, agent_manager):
        """Test objective completion check returns False"""
        agent_manager.current_objective = "Analyze data"
        result = {'type': 'analysis', 'status': 'success'}
        
        with patch.object(agent_manager.llm_manager, 'generate') as mock_generate:
            mock_generate.return_value = "NO"
            
            is_complete = agent_manager._is_objective_complete(result)
            
            assert is_complete is False


class TestAgent:
    """Test cases for Agent class"""
    
    def test_agent_creation(self):
        """Test Agent creation with all attributes"""
        agent = Agent(
            name="test_agent",
            role=AgentRole.ANALYST,
            description="Test agent description",
            capabilities=["sql_generation", "data_analysis"],
            is_active=True
        )
        
        assert agent.name == "test_agent"
        assert agent.role == AgentRole.ANALYST
        assert agent.description == "Test agent description"
        assert agent.capabilities == ["sql_generation", "data_analysis"]
        assert agent.is_active is True
    
    def test_agent_default_values(self):
        """Test Agent creation with default values"""
        agent = Agent(
            name="test_agent",
            role=AgentRole.ENGINEER,
            description="Test agent",
            capabilities=["schema_design"]
        )
        
        assert agent.is_active is True  # Default value


class TestAgentRole:
    """Test cases for AgentRole enum"""
    
    def test_agent_role_values(self):
        """Test AgentRole enum values"""
        assert AgentRole.ANALYST.value == "analyst"
        assert AgentRole.ENGINEER.value == "engineer"
        assert AgentRole.RESEARCHER.value == "researcher"
    
    def test_agent_role_from_string(self):
        """Test creating AgentRole from string"""
        assert AgentRole("analyst") == AgentRole.ANALYST
        assert AgentRole("engineer") == AgentRole.ENGINEER
        assert AgentRole("researcher") == AgentRole.RESEARCHER 