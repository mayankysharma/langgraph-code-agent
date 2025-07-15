# LangGraph Code Agent

A streamlined code generation agent built with LangGraph and Groq. This LangGraph agent is a synchronous graph. The agent analyzes user requests, generates Python code, performs quality assurance checks, and automatically saves the results to a file and traces all workflow steps to the Judgeval dashboard for monitoring and evaluation.

## Features

- **Requirement Analysis**: Automatically analyzes user requests and extracts key requirements
- **Code Generation**: Generates Python code based on specified requirements with proper documentation
- **Quality Assurance**: Performs static analysis using Black, Pylint, MyPy, and LLM-based code review
- **Retry Logic**: Automatically retries code generation up to 3 times if QA issues are detected
- **Automatic File Saving**: Saves the generated code to a `generated_code/` directory with sanitized filenames
- **Interactive Interface**: Simple command-line interface for user input
- **Judgeval Tracing**: All workflow steps, tool calls, and LLM generations are automatically traced and sent to the Judgeval dashboard via JudgevalCallbackHandler.
- **Automated Output Evaluation**: After code is generated, the agent uses Judgeval's AnswerRelevancyScorer to automatically assess the relevance and quality of the output with respect to the user request. Results are logged to the Judgeval dashboard.

## Architecture

The agent uses a LangGraph workflow with four main nodes:

1. **Initialize State** → Analyzes user request and extracts requirements (with full tracing of this step)
2. **Generate Code** → Creates Python code based on requirements (with retry capability and tracing of LLM/tool calls)
3. **Perform QA** → Runs static analysis and LLM-based code review (all QA steps are traced)
4. **Save Code** → Saves the generated code to disk (traced), then triggers automated output evaluation using Judgeval's AnswerRelevancyScorer (evaluation results are logged and traced)


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
JUDGMENT_API_KEY=your_judgeval_api_key_here
```

## Usage

Run the agent interactively:

```bash
python main.py
```

The agent will prompt you to enter your request, then generate and save the code.

After each code generation, the agent automatically evaluates the output using AnswerRelevancyScorer and sends the results to your Judgeval dashboard.

If you have set up your Judgeval API key and project, traces and metrics will appear in your Judgeval dashboard automatically.

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

### Evaluation Configuration

- After each code generation, evaluation is performed automatically using Judgeval's AnswerRelevancyScorer.
- You can adjust the threshold for AnswerRelevancyScorer or add your own custom scorers in `main.py` to tailor evaluation to your needs.
- To avoid evaluation run name errors, set a unique `eval_run_name` (e.g., using a timestamp) or use `override=True`/`append=True` in your evaluation call.
- Always set the `project_name` argument in your evaluation call to ensure results are logged to the correct project and to avoid project limit errors.

## Output

- **Console Output**: Progress through each workflow node
- **Generated Files**: Code is saved to `generated_code/` directory
- **File Naming**: Files are automatically named based on the task description

## Evaluation

After code generation, the agent automatically evaluates the generated code using Judgeval's `AnswerRelevancyScorer`. This scorer checks the relevance and quality of the output code with respect to the user request. The evaluation results are sent to the Judgeval dashboard for review and monitoring.

**How it works:**
After the agent finishes, it runs:
```python
from judgeval.scorers import AnswerRelevancyScorer
from judgeval import JudgmentClient
from judgeval.data import Example

client = JudgmentClient()
example = Example(
    input={"user_request": "Create a function to calculate the factorial of a number"},
    actual_output=generated_code
)
client.run_evaluation(
    examples=[example],
    scorers=[AnswerRelevancyScorer(threshold=0.5)],
    project_name="your-project-name",
    eval_run_name="code_agent_eval_...",
    override=True
)
```
You can customize or add additional scorers in `main.py` as needed. See [Judgeval documentation](https://docs.judgmentlabs.ai/documentation/evaluation/scorers/custom-scorers) for more details.

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

Evaluation results are sent to your Judgeval dashboard for each code generation.

## Dependencies

### Prerequisites
- Python 3.8+
- Groq API key
- JUDGMENT API Key

### Python Packages
- `langgraph`: Graph-based workflow orchestration
- `langchain-groq`: Groq LLM integration
- `langchain-core`: Core LangChain functionality
- `python-dotenv`: Environment variable management


- `black`: Code formatting
- `pylint`: Static analysis and linting
- `mypy`: Type checking
- `judgeval`: Post-building library for AI agents that comes with everything you need to trace and test your agents with evals.

## Tracing & Evaluation (Judgeval Integration)

- **Judgeval Tracing**: All agent workflow steps, tool calls, and LLM generations are automatically traced and sent to the [Judgeval](https://dashboard.judgmentlabs.ai/) dashboard for monitoring and evaluation. This is handled by the JudgevalCallbackHandler integrated into the workflow.
- **Automated Evaluation**: After each code generation, the output is automatically evaluated for relevance and quality using Judgeval's AnswerRelevancyScorer. The evaluation results are also sent to the Judgeval dashboard for review and monitoring.
- **Project Name**: The project name in your code must match your Judgeval dashboard project.
- **API Key**: Requires a valid `JUDGMENT_API_KEY` environment variable for Judgeval integration.

**Note:** The `project_name` in your code (see `main.py`) must match the project name in your Judgeval dashboard for traces and evaluation results to appear.

## Troubleshooting

- **No traces in Judgeval dashboard?**
  - Ensure your `JUDGMENT_API_KEY` is set and valid.
  - The `project_name` in your code must match your Judgeval dashboard project.
  - Update Judgeval to the latest version: `pip install --upgrade judgeval`
  - Check for errors in the console output related to Judgeval initialization or API key authorization.

- **Judgeval errors like "Unauthorized request" or "Invalid request format"?**
  - Double-check your API key and project name.
  - Make sure your environment variables are loaded before running the script.

- **Evaluation run name errors (e.g., 'already exists for this project')?**
  - Use a unique `eval_run_name` for each run, or set `override=True` or `append=True` in your evaluation call.
- **Error 422: Project limit exceeded**
  - When using `run_evaluation()` without passing in the project_name argument, the project_name defaulted to default_project which counted as trying to create a second project. So, this will add one more project in the dashboard. So, if project limit is set pass same project_name which is picked by user




