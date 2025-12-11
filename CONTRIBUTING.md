# Contributing to Cosmetics Records

Thank you for your interest in contributing to Cosmetics Records! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)

## Code of Conduct

This project adheres to a Code of Conduct. By participating, you are expected to uphold this code. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## How to Contribute

### Types of Contributions

- **Bug fixes**: Fix issues reported in the issue tracker
- **Features**: Implement new features (please discuss first)
- **Documentation**: Improve or add documentation
- **Tests**: Add missing tests or improve existing ones
- **Translations**: Help translate the application to new languages

## Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/cosmetics-records.git
   cd cosmetics-records
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or: venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Run the application**
   ```bash
   python src/cosmetics_records/app.py
   ```

5. **Run tests**
   ```bash
   pytest
   ```

## Code Style

We use several tools to maintain code quality:

### Formatting with Black

```bash
black src/ tests/
```

- Line length: 88 characters
- Run before committing

### Linting with Flake8

```bash
flake8 src/ tests/
```

### Type Checking with MyPy

```bash
mypy src/
```

- We use strict type checking
- All public functions must have type hints

### Naming Conventions

- **Classes**: PascalCase (e.g., `ClientController`)
- **Functions/Methods**: snake_case (e.g., `get_client`)
- **Constants**: UPPER_CASE (e.g., `PRIMARY_BLUE`)
- **Private members**: Leading underscore (e.g., `_settings`)

### Documentation

- All public classes and methods must have docstrings
- Use Google-style docstrings with Args, Returns, Raises sections
- Include inline comments explaining "why" for non-obvious code

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/cosmetics_records

# Run specific test file
pytest tests/unit/test_models.py

# Run tests matching a pattern
pytest -k "test_client"
```

### Writing Tests

- Place unit tests in `tests/unit/`
- Place integration tests in `tests/integration/`
- Use fixtures from `tests/conftest.py`
- Test both success and error cases
- Use descriptive test names

### Test Requirements

- All new features must include tests
- Bug fixes should include a regression test
- Maintain or improve code coverage

## Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the code style guidelines
   - Add tests for new functionality
   - Update documentation if needed

3. **Run quality checks**
   ```bash
   black src/ tests/
   flake8 src/ tests/
   mypy src/
   pytest
   ```

4. **Commit your changes**
   - Use conventional commit messages:
     - `feat:` for new features
     - `fix:` for bug fixes
     - `docs:` for documentation changes
     - `refactor:` for code refactoring
     - `test:` for test additions/changes
   - Example: `feat: Add export to PDF functionality`

5. **Push and create a Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```
   - Fill out the PR template
   - Link related issues
   - Request review from maintainers

6. **Address review feedback**
   - Make requested changes
   - Push additional commits
   - Re-request review when ready

### PR Requirements

- All CI checks must pass
- At least one maintainer approval required
- No merge conflicts with main branch
- Documentation updated if needed

## Reporting Bugs

### Before Reporting

1. Check existing issues to avoid duplicates
2. Try to reproduce on the latest version
3. Collect relevant information

### Bug Report Contents

- **Description**: Clear description of the bug
- **Steps to Reproduce**: Detailed steps to reproduce
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Environment**: OS, Python version, app version
- **Screenshots**: If applicable
- **Logs**: Relevant log output (check `~/.cosmetics-records/logs/`)

## Suggesting Features

### Before Suggesting

1. Check existing issues and discussions
2. Consider if it fits the project scope
3. Think about implementation approach

### Feature Request Contents

- **Description**: Clear description of the feature
- **Use Case**: Why is this feature needed?
- **Proposed Solution**: How might it work?
- **Alternatives**: Other approaches considered
- **Additional Context**: Mockups, examples, etc.

## Questions?

If you have questions about contributing, feel free to:
- Open a discussion on GitHub
- Check existing documentation
- Review similar PRs for examples

Thank you for contributing!
