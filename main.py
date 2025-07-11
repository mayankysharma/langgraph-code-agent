#!/usr/bin/env python

import os
import json
import re
import tempfile
import subprocess
import sys
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from typing import TypedDict, Sequence, Dict, Any, Optional, List, Union
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq

# --- Load environment variables ---
load_dotenv()

chat_model = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.environ.get("GROQ_API_KEY"),
    temperature=0
)

# --- Define your Graph State ---
class AgentState(TypedDict):
    user_request: str
    requirements: Dict[str, Any]
    generated_code: str
    chat_history: List[Dict[str, str]]
    output_file_path: Optional[str]
    qa_report: Optional[str]
    error_message: Optional[str]
    retry_count: int

def filenaming_function(text: str, max_length: int = 50) -> str:
    """Sanitizes a string to be used as a filename."""
    s = re.sub(r'[^\w\s-]', '', text).strip().lower()
    s = re.sub(r'[-\s]+', '-', s)
    return s[:max_length]

# Node functions
def initialize_state(state: AgentState) -> Dict:
    print("--- Node: Requirement Analysis ---")
    user_request = state["user_request"]
    
    analysis_prompt = (
        f"Analyze the following user request and extract key requirements:\nRequest: '{user_request}'\n\n"
        "Provide the output as a JSON object with keys like 'language', 'task', 'output_format', 'constraints'. "
        "Be concise. Do not include any additional text or explanations, just the JSON."
    )
    
    response_content = chat_model.invoke([HumanMessage(content=analysis_prompt)]).content
    
    try:
        requirements = json.loads(response_content)
        if not isinstance(requirements, dict):
            raise ValueError("LLM response was not a dictionary after JSON parsing.")
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        print(f"Warning: Failed to parse requirements as JSON: {e}. LLM response: {response_content}")
        requirements = {"language": "python", "task": user_request, "output_format": "standard"}
    
    state["chat_history"].append({"role": "user", "content": analysis_prompt})
    state["chat_history"].append({"role": "assistant", "content": response_content})
    
    return {"requirements": requirements, "chat_history": state["chat_history"]}

def generate_code(state: AgentState) -> Dict:
    """
    Generates new code or revises existing code based on requirements and QA feedback.
    """
    print("\n--- Node: Code Generation/Revision ---")
    requirements = state["requirements"]
    existing_code = state.get("generated_code", "")
    error_message = state.get("error_message", "")
    qa_report = state.get("qa_report", "")

    if error_message or (qa_report and "issues detected" in qa_report.lower()):
        current_retries = state.get("retry_count", 0)
        state["retry_count"] = current_retries + 1

    if error_message or (qa_report and "issues detected" in qa_report.lower()):
        print("--- Revising code based on previous QA issues. ---")
        revision_prompt = (
            f"The previous attempt to generate code for the task: '{requirements.get('task', 'a programming task')}' "
            f"encountered quality assurance issues. Here is the feedback:\n\n"
            f"**Static Analysis/QA Report:**\n```\n{qa_report}\n```\n\n"
            f"Please revise the {requirements.get('language', 'python')} script to address these problems. "
            f"Here is the previous code that needs fixing:\n```python\n{existing_code}\n```\n"
            "Provide only the corrected code block, no extra text or explanations outside the code block. "
            "Ensure the code adheres to best practices, resolves the identified issues, and is executable. "
            "Provide docstrings documentation for the code and keep comments to minimum and only if necessary."
        )
        final_prompt = revision_prompt
    else:
        print("--- Generating initial code. ---")
        initial_gen_prompt = (
            f"Based on these requirements: {requirements.get('task', 'a programming task')}. "
            f"Generate a {requirements.get('language', 'python')} script. "
            "Provide only the code block, no extra text or explanations outside the code block. "
            "Write good quality code with proper indentation and use the best practices. "
            "Provide docstrings documentation for the code and keep comments to minimum and only if necessary."
            "Ensure the code is executable and simple."
        )
        final_prompt = initial_gen_prompt

    response_content = chat_model.invoke([HumanMessage(content=final_prompt)]).content

    start_token = "```python"
    end_token = "```"
    if start_token in response_content and end_token in response_content:
        code_block = response_content.split(start_token)[1].split(end_token)[0]
    else:
        code_block = response_content.strip()

    print(f"Generated/Revised Code:\n{code_block}")
    state["chat_history"].append({"role": "user", "content": final_prompt})
    state["chat_history"].append({"role": "assistant", "content": response_content})
    
    return {
        "generated_code": code_block,
        "chat_history": state["chat_history"],
        "retry_count": state.get("retry_count", 0),
    }

def perform_qa(state: AgentState) -> Dict:
    """
    Performs static analysis (Black, Pylint, MyPy) and an LLM-based code review.
    """
    print("\n--- Node: Quality Assurance (Linting, Formatting, Review) ---")
    code = state["generated_code"]
    qa_report = ""
    linting_errors_found = False
    formatted_code = code

    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.py', encoding='utf-8') as temp_file:
        temp_file.write(code)
        temp_file_path = temp_file.name
    
    print("Running Black formatter...")
    try:
        black_cmd = [sys.executable, "-m", "black", temp_file_path]
        check_cmd = [sys.executable, "-m", "black", "--check", temp_file_path]
        check_result = subprocess.run(check_cmd, capture_output=True, text=True, check=False)

        if check_result.returncode != 0:
            format_result = subprocess.run(black_cmd, capture_output=True, text=True, check=False)
            if format_result.returncode == 0:
                qa_report += "Black: Code was reformatted.\n"
                with open(temp_file_path, 'r', encoding='utf-8') as f:
                    formatted_code = f.read()
                state["generated_code"] = formatted_code
                print("Code reformatted by Black.")
            else:
                qa_report += f"Black: Formatting failed with errors: {format_result.stderr}\n"
                linting_errors_found = True
        else:
            qa_report += "Black: Code already formatted correctly.\n"

    except FileNotFoundError:
        qa_report += "Black not found. Install with: pip install black\n"
    except Exception as e:
        qa_report += f"Error running Black: {e}\n"
        linting_errors_found = True

    print("Running Pylint linter...")
    try:
        pylint_cmd = [
            sys.executable, "-m", "pylint",
            "--disable=C0114,C0115,C0116,R0903,W0613,C0103,E0401,W0621",
            "--output-format=json",
            temp_file_path
        ]
        pylint_result = subprocess.run(pylint_cmd, capture_output=True, text=True, check=False)

        if pylint_result.stdout:
            try:
                pylint_output = json.loads(pylint_result.stdout)
                if pylint_output:
                    qa_report += "\nPylint Report (Warnings/Errors):\n"
                    for msg in pylint_output:
                        qa_report += (
                            f"  {msg['type'].upper()} ({msg['symbol']}): "
                            f"{msg['message']} at {msg['path']}:{msg['line']}:{msg['column']}\n"
                        )
                        if msg['type'] in ['error', 'fatal', 'warning']:
                            linting_errors_found = True
                else:
                    qa_report += "\nPylint: No issues found.\n"
            except json.JSONDecodeError:
                qa_report += f"\nPylint: Failed to parse JSON output. Raw output:\n{pylint_result.stdout}\n"
                linting_errors_found = True
        if pylint_result.stderr:
            qa_report += f"\nPylint Errors (stderr):\n{pylint_result.stderr}\n"
            linting_errors_found = True

    except FileNotFoundError:
        qa_report += "Pylint not found. Install with: pip install pylint\n"
    except Exception as e:
        qa_report += f"Error running Pylint: {e}\n"
        linting_errors_found = True

    print("Running MyPy type checker...")
    try:
        mypy_cmd = [sys.executable, "-m", "mypy", "--ignore-missing-imports", temp_file_path]
        mypy_result = subprocess.run(mypy_cmd, capture_output=True, text=True, check=False)

        if mypy_result.stdout and "Success: no issues found" not in mypy_result.stdout:
            qa_report += "\nMyPy Type Check Report:\n" + mypy_result.stdout
            if "error:" in mypy_result.stdout or "warning:" in mypy_result.stdout:
                 linting_errors_found = True
        elif mypy_result.stderr:
            qa_report += f"\nMyPy Errors (stderr):\n{mypy_result.stderr}\n"
            linting_errors_found = True
        else:
            qa_report += "\nMyPy: No type errors found.\n"

    except FileNotFoundError:
        qa_report += "MyPy not found. Install with: pip install mypy\n"
    except Exception as e:
        qa_report += f"Error running MyPy: {e}\n"
        linting_errors_found = True
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    print("Running LLM-based code review...")
    review_prompt = (
        f"Review the following code and static analysis report. "
        "Be LENIENT in your assessment. "
        "If the code is functionally correct and follows basic Python syntax, respond with ONLY: 'Code quality is acceptable for execution.' "
        "Only flag issues if there are CRITICAL problems that would prevent the code from running (syntax errors, logical errors, security issues). "
        "Ignore minor style issues, missing docstrings, or import warnings for optional libraries.\n\n"
        f"Code:\n```python\n{formatted_code}\n```\n\n"
        f"Static Analysis Report:\n{qa_report}"
    )
    llm_review_response = chat_model.invoke([HumanMessage(content=review_prompt)]).content
    qa_report += f"\nLLM Code Review & Suggestions:\n{llm_review_response}\n"

    print(f"Full QA Report:\n{qa_report}")
    state["chat_history"].append({"role": "user", "content": "Performed QA on generated code."})
    state["chat_history"].append({"role": "assistant", "content": f"QA Report: {qa_report}"})

    state["generated_code"] = formatted_code
    state["qa_report"] = qa_report
    
    llm_review_lower = llm_review_response.lower()
    
    is_acceptable = any(phrase in llm_review_lower for phrase in [
        "acceptable for execution", "excellent", "good", "fine", "works", "functional"
    ])
    
    critical_issues = any(phrase in llm_review_lower for phrase in [
        "critical", "error", "won't run", "cannot run", "broken", "fatal", 
        "security issue", "logical error", "syntax error", "missing import"
    ])
    
    if critical_issues and not is_acceptable:
        state["error_message"] = "Critical issues detected. See QA Report for details."
    else:
        state["error_message"] = None

    return {"generated_code": state["generated_code"], "qa_report": state["qa_report"], "chat_history": state["chat_history"], "error_message": state["error_message"]}

def save_code(state: AgentState) -> Dict:
    print("--- Node: Save Code ---")
    final_code = state["generated_code"]
    requirements = state["requirements"]
    
    output_dir = "generated_code"
    os.makedirs(output_dir, exist_ok=True)

    task_name = requirements.get("task", "unknown_task")
    filename = f"{filenaming_function(task_name)}.py"
    output_file_path = os.path.join(output_dir, filename)
    
    try:
        with open(output_file_path, "w", encoding='utf-8') as f:
            f.write(final_code)
        print(f"Final code saved to: {output_file_path}")
        state["output_file_path"] = output_file_path
    except Exception as e:
        print(f"Error saving file: {e}")
        state["output_file_path"] = None
        
    return {"output_file_path": state["output_file_path"], "error_message": state.get("error_message")}

def should_retry_qa(state: AgentState) -> str:
    """
    Decides whether to re-attempt code generation/QA or finish.
    Allows up to 3 retries for QA issues.
    """
    current_retries = state.get("retry_count", 0)
    max_retries = 3

    qa_has_issues = bool(state.get("error_message"))

    if qa_has_issues and current_retries < max_retries:
        print(f"--- QA failed. Retrying code generation. Retry count: {current_retries + 1}/{max_retries} ---")
        return "retry"
    elif qa_has_issues and current_retries >= max_retries:
        print(f"--- QA failed, and {max_retries} retries exhausted. Ending. ---")
        return "fail_and_end"
    else:
        print("--- Code passed QA. Proceeding to save. ---")
        return "end"

workflow = StateGraph(AgentState)

workflow.add_node("initialize_state", initialize_state)
workflow.add_node("generate_code", generate_code)
workflow.add_node("perform_qa", perform_qa)
workflow.add_node("save_code", save_code)

workflow.set_entry_point("initialize_state")

workflow.add_edge("initialize_state", "generate_code")
workflow.add_edge("generate_code", "perform_qa")

workflow.add_conditional_edges(
    "perform_qa",
    should_retry_qa,
    {   
        "end": "save_code",
        "retry": "generate_code",
        "fail_and_end": END
    }
)

workflow.add_edge("save_code", END)

graph = workflow.compile()


def code_generation_agent(user_request: str):
    """
    This function initializes the state, generates code, and saves the code.
    """
    
    state = AgentState(
        user_request=user_request,
        requirements={},
        generated_code="",
        chat_history=[],
        output_file_path=None,
        qa_report=None,
        error_message=None,
        retry_count=0
    )
    final_state = graph.invoke(state)
    return final_state


if __name__ == "__main__":
    print(f"Hi, I am your personal code generation agent. I will generate python code for you based on your request!")
    user_request = input("Enter your request: ")
    
    final_state = code_generation_agent(user_request)
    
    print("\n--- Agent Workflow Completed ---")
    print(f"Debug - output_file_path: {final_state.get('output_file_path')}")
    print(f"Debug - error_message: {final_state.get('error_message')}")
    
    if final_state.get('output_file_path'):
        print(f"\n Code generation successful! Final code saved to: {final_state['output_file_path']}")
    else:
        print("\n Code generation failed or was not saved successfully due to QA issues or retry limits.")
        if final_state.get('error_message'):
            print(f"Last error/QA summary:\n{final_state['error_message']}")
        if final_state.get('qa_report'):
            print(f"Full QA Report:\n{final_state['qa_report']}")
    print("\nThank you for using my service. Goodbye!")
