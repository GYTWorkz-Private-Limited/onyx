# Pulse Contribution Guidelines

Welcome! To contribute to the Pulse project, please follow these guidelines:

- **Feature Organization:**  
  Each feature from the development board should be placed in its own subfolder under the `pulse` directory.  
  For example: `pulse/session_management`

- **Project Structure:**  
  Every `pulse` subfolder should follow the structure provided in `pulse/skeleton`.

- **Dependency Management:**  
  Use [Poetry](https://python-poetry.org/) to manage dependencies for each submodule.  
  Ensure that each submodule has its own `pyproject.toml` file.
  Each feature must expose its functionality through at least one of:
  - REST API endpoints (using FastAPI)
  - GraphQL endpoints (using Strawberry)
  - WebSocket connections (using FastAPI)
  Include appropriate API documentation and examples in the feature's README.


- **General Tips:**  
  - Write clear, maintainable code.
  - Update documentation as needed.

Thank you for helping make Pulse better!
