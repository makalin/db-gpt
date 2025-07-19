# Contributing to DB-GPT

Thank you for your interest in contributing to DB-GPT! This document provides guidelines and information for contributors.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a feature branch** for your changes
4. **Make your changes** following the guidelines below
5. **Test your changes** thoroughly
6. **Submit a pull request**

## Development Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # for development dependencies
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run tests**:
   ```bash
   pytest
   ```

## Code Style Guidelines

### Python Code
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines
- Use type hints for function parameters and return values
- Write docstrings for all public functions and classes
- Keep functions focused and under 50 lines when possible

### Example
```python
from typing import Dict, List, Optional

def process_data(data: List[Dict[str, Any]], 
                config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Process the input data according to the configuration.
    
    Args:
        data: List of data dictionaries to process
        config: Optional configuration dictionary
        
    Returns:
        Dictionary containing processed results
        
    Raises:
        ValueError: If data is empty or invalid
    """
    if not data:
        raise ValueError("Data cannot be empty")
    
    # Process data here
    return {"processed": True, "count": len(data)}
```

## Testing Guidelines

- Write unit tests for all new functionality
- Aim for at least 80% code coverage
- Use descriptive test names
- Test both success and failure cases

### Example Test
```python
import pytest
from src.utils.text_to_sql import TextToSQLConverter

def test_text_to_sql_conversion():
    """Test basic text to SQL conversion functionality."""
    converter = TextToSQLConverter(mock_llm_manager, mock_db_connection)
    
    result = converter.convert("Show me all users")
    
    assert result.query_type == "SELECT"
    assert "SELECT" in result.query.upper()
    assert result.confidence > 0.5
```

## Pull Request Guidelines

### Before Submitting
1. **Update documentation** if needed
2. **Add tests** for new functionality
3. **Run all tests** and ensure they pass
4. **Check code style** with flake8 and black
5. **Update CHANGELOG.md** with your changes

### Pull Request Template
```markdown
## Description
Brief description of the changes made.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] No breaking changes (or documented)
```

## Focus Areas for Contributions

### High Priority
- **Text-to-SQL accuracy improvements**
- **Database connector enhancements**
- **Performance optimizations**
- **Error handling improvements**

### Medium Priority
- **Additional LLM provider support**
- **Vector store integrations**
- **API endpoint development**
- **Web interface improvements**

### Low Priority
- **Documentation improvements**
- **Code refactoring**
- **Test coverage improvements**
- **Example notebooks**

## Reporting Issues

When reporting issues, please include:

1. **Environment information**:
   - Python version
   - Operating system
   - DB-GPT version
   - Database type and version

2. **Steps to reproduce**:
   - Clear, step-by-step instructions
   - Sample data if applicable
   - Configuration files (with sensitive data removed)

3. **Expected vs actual behavior**:
   - What you expected to happen
   - What actually happened
   - Any error messages or logs

## Getting Help

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Documentation**: Check the README and inline code documentation

## Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please be respectful and constructive in all interactions.

## License

By contributing to DB-GPT, you agree that your contributions will be licensed under the MIT License. 