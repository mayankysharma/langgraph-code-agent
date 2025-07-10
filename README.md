# LangGraph Code Agent

A streamlined code generation agent built with LangGraph and Groq's LLM. This agent analyzes user requests, generates Python code, and automatically saves the results to a file.

## Features

- **Requirement Analysis**: Automatically analyzes user requests and extracts key requirements
- **Code Generation**: Generates Python code based on specified requirements with proper documentation
- **Automatic File Saving**: Saves the generated code to a `generated_code/` directory with sanitized filenames
- **Interactive Interface**: Simple command-line interface for user input

## Architecture

The agent uses a simple LangGraph workflow with three nodes:

1. **Initialize State** → Analyzes user request and extracts requirements
2. **Generate Code** → Creates Python code based on requirements
3. **Save Code** → Saves the generated code to disk

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd langgraph-code-agent
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install langgraph langchain-groq langchain-core python-dotenv
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

The agent uses Groq's `llama-3.3-70b-versatile` model with:
- Temperature: 0 (deterministic output)
- Automatic code block extraction from responses

## Output

- **Console Output**: Progress through each workflow node
- **Generated Files**: Code is saved to `generated_code/` directory
- **File Naming**: Files are automatically named based on the task description


## Example Output

For a request like "Create a function to calculate the factorial of a number", the agent will:
1. Analyze the request and extract requirements
2. Generate a Python function with proper documentation
3. Save it to `generated_code/create-a-function-to-calculate-the-factorial-of-a-number.py`

## Dependencies

### Prerequisites
- Python 3.8+
- Groq API key

### Python Packages
- `langgraph`: Graph-based workflow orchestration
- `langchain-groq`: Groq LLM integration
- `langchain-core`: Core LangChain functionality
- `python-dotenv`: Environment variable management


## TO DO

- Add checks for checking generated code against linting, unit test cases, security and others.
- Add ability to do code completion and debugging for user
- Add requirements.txt file