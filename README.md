# Automate DevSecOps

A command-line tool for automated analysis of software repositories to assess DevSecOps readiness. This tool analyzes code repositories to detect programming languages, dependencies, build processes, runtime configurations, databases, health endpoints, and security vulnerabilities.

## Features

- **Language Detection**: Automatically identifies the primary programming language used in the repository.
- **Dependency Analysis**: Checks for dependency declarations (e.g., `requirements.txt`, `package.json`).
- **Build Detection**: Identifies if the project requires a build step.
- **Runtime Configuration**: Determines start commands and application ports.
- **Database Detection**: Scans for database usage patterns.
- **Health Endpoint Detection**: Looks for health check endpoints in the code.
- **Security Analysis**: Collects security facts, including detection of potential hardcoded secrets.
- **Confidence Scoring**: Provides a confidence score based on the completeness of the analysis.
- **Docker Support**: Checks for the presence of a Dockerfile.

## Installation

### Prerequisites

- Python 3.7 or higher
- Git (for cloning repositories)

### Install from Source

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd automate_devsecops
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

After installation, you can analyze a repository using the command-line interface:

```bash
python cli.py repo <repository-path-or-url>
```

### Examples

- Analyze a local repository:
  ```bash
  python cli.py repo /path/to/your/project
  ```

- Analyze a remote repository (if supported):
  ```bash
  python cli.py repo https://github.com/user/repo.git
  ```

The tool will output a JSON-like structure containing:
- Analysis results (language, dependencies, etc.)
- Confidence score (0-100)
- Warnings for potential issues
- Security facts
- Dockerfile presence

## Project Structure

- `cli.py`: Command-line interface entry point.
- `analyzer/`: Core analysis modules.
  - `analyzer.py`: Main analysis logic.
  - `repo_loader.py`: Handles repository loading.
  - `language.py`: Language detection.
  - `dependencies.py`: Dependency analysis.
  - `build.py`: Build step detection.
  - `runtime.py`: Runtime configuration.
  - `database.py`: Database detection.
  - `health.py`: Health endpoint detection.
  - `security/`: Security analysis modules.
- `utils/`: Utility functions.
- `workspace/`: Temporary workspace for analysis.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.