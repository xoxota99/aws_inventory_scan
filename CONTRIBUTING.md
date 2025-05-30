# Contributing to AWS Inventory Scanner

Thank you for your interest in contributing to AWS Inventory Scanner! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

Please be respectful and considerate of others when contributing to this project. We aim to foster an inclusive and welcoming community.

## Getting Started

1. **Fork the repository** on GitHub.

2. **Clone your fork** to your local machine:
   ```bash
   git clone https://github.com/yourusername/aws_inventory_scan.git
   cd aws_inventory_scan
   ```

3. **Set up the development environment**:
   ```bash
   # Create a virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install development dependencies
   pip install -e ".[dev]"
   ```

4. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Guidelines

### Code Style

We follow PEP 8 style guidelines for Python code. Please ensure your code adheres to these standards.

Use the following tools to check and format your code:

```bash
# Check code style
flake8 aws_inventory_scan tests

# Format code
black aws_inventory_scan tests

# Sort imports
isort aws_inventory_scan tests
```

### Type Hints

Use type hints for function parameters and return values:

```python
def example_function(param1: str, param2: int) -> bool:
    """Example function with type hints."""
    return True
```

### Documentation

Document your code using docstrings. We follow the Google style for docstrings:

```python
def example_function(param1, param2):
    """Example function with Google style docstring.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ExceptionType: When and why this exception is raised
    """
    return True
```

### Testing

Write tests for your code using pytest:

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=aws_inventory_scan
```

Ensure that your code passes all tests and maintains or improves code coverage.

## Adding Support for a New AWS Service

To add support for a new AWS service:

1. **Add service mapping** to `service_mappings.py`:
   ```python
   'new-service': {
       'method': 'list_resources',
       'key': 'Resources',
       'arn_attr': 'ResourceArn'
   }
   ```

2. **Create a service collector** in the `services` directory:
   ```python
   # services/new_service.py
   def collect_resources(client, region, account_id, resource_arns, verbose=False):
       """Collect resources for the new service."""
       # Implementation here
   ```

3. **Add tests** for your service collector.

## Pull Request Process

1. **Update documentation** to reflect any changes.

2. **Add tests** for new functionality.

3. **Ensure all tests pass** and code style checks pass.

4. **Update the CHANGELOG.md** with details of your changes.

5. **Submit a pull request** to the main repository.

6. **Respond to feedback** from maintainers.

## Release Process

Releases are managed by the project maintainers. The process typically involves:

1. Updating the version number in `__init__.py`
2. Updating the CHANGELOG.md
3. Creating a new release on GitHub
4. Publishing to PyPI

## Questions?

If you have questions or need help, please open an issue on GitHub.
