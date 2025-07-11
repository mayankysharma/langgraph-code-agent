# LangGraph Code Agent

A streamlined code generation agent built with LangGraph and Groq. This agent analyzes user requests, generates Python code, performs quality assurance checks, and automatically saves the results to a file.

## Features

- **Requirement Analysis**: Automatically analyzes user requests and extracts key requirements
- **Code Generation**: Generates Python code based on specified requirements with proper documentation
- **Quality Assurance**: Performs static analysis using Black, Pylint, MyPy, and LLM-based code review
- **Retry Logic**: Automatically retries code generation up to 3 times if QA issues are detected
- **Automatic File Saving**: Saves the generated code to a `generated_code/` directory with sanitized filenames
- **Interactive Interface**: Simple command-line interface for user input

## Architecture

The agent uses a LangGraph workflow with four main nodes:

1. **Initialize State** → Analyzes user request and extracts requirements
2. **Generate Code** → Creates Python code based on requirements (with retry capability)
3. **Perform QA** → Runs static analysis and LLM-based code review
4. **Save Code** → Saves the generated code to disk

## Installation

1. Clone the repository:
```bash
git clone https://github.com/mayankysharma/langgraph-code-agent.git
cd langgraph-code-agent
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the project root:
```
GROQ_API_KEY=your_groq_api_key_here
```

## Usage

Run the agent interactively:

```bash
python main.py
```

The agent will prompt you to enter your request, then generate and save the code.

### Example Usage

```
Hi, I am your personal code generation agent. I will generate python code for you based on your request!
Enter your request: Create a function to calculate the factorial of a number
```

## Configuration

### Model Settings

The agent uses Groq's `llama-3.1-8b-instant` model with:
- Temperature: 0 (deterministic output)
- Automatic code block extraction from responses

### Quality Assurance Tools

The agent uses several tools for code quality checking:
- **Black**: Code formatting
- **Pylint**: Static analysis and linting
- **MyPy**: Type checking
- **LLM Review**: AI-powered code review for critical issues

All QA tools are optional - the agent works even if they're not installed.

## Output

- **Console Output**: Progress through each workflow node
- **Generated Files**: Code is saved to `generated_code/` directory
- **File Naming**: Files are automatically named based on the task description


## Example Output

For a request like "Create a function to calculate the factorial of a number", the agent will:
1. Analyze the request and extract requirements
2. Generate a Python function with proper documentation
3. Perform quality assurance checks (formatting, linting, type checking, LLM review)
4. Save it to `generated_code/create-a-function-to-calculate-the-factorial-of-a-number.py`

### Sample Workflow Output

```
--- Node: Requirement Analysis ---
--- Node: Code Generation ---
--- Node: Quality Assurance (Linting, Formatting, Review) ---
Running Black formatter...
Running Pylint linter...
Running MyPy type checker...
Running LLM-based code review...
--- Code passed QA. Proceeding to save. ---
--- Node: Save Code ---
Final code saved to: generated_code/factorial-function.py
✅ Code generation successful! Final code saved to: generated_code/factorial-function.py
```

## Dependencies

### Prerequisites
- Python 3.8+
- Groq API key

### Python Packages
- `langgraph`: Graph-based workflow orchestration
- `langchain-groq`: Groq LLM integration
- `langchain-core`: Core LangChain functionality
- `python-dotenv`: Environment variable management


- `black`: Code formatting
- `pylint`: Static analysis and linting
- `mypy`: Type checking


