# YUI Codebase Guidelines

## Commands
- Setup: `python3 -m venv env && source env/bin/activate && pip install -r requirements.txt`
- Run: `python main.py`
- Install dependency: `pip install <package> && pip freeze > requirements.txt`

## Code Style
- Type hints are required for all functions and classes
- Use snake_case for functions/variables, PascalCase for classes, UPPER_CASE for constants
- Imports organized: standard library → third-party → local packages
- Follow clean architecture pattern: model → repository → gateway → controller
- Use SQLModel for database models with proper type annotations
- Error handling via try/except blocks with specific exceptions
- Maintain separation of concerns between components
- Use direct passing for dependency injection for repositories and gateways
- Rich library used for terminal rendering and UI components

## Environment
- API keys stored in .env file (CLAUDE_API_KEY required)
- Python 3 with virtual environment