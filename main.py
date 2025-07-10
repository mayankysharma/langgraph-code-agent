#!/usr/bin/env python

import os
import json
import re
import argparse
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from typing import TypedDict, Sequence, Dict, Any, Optional, List, Union
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq

# --- Load environment variables ---
load_dotenv()

chat_model = ChatGroq(
    model="llama-3.3-70b-versatile",
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

def filenaming_function(text: str, max_length: int = 50) -> str:
    """Sanitizes a string to be used as a filename."""
    # Replace non-alphanumeric characters with underscores
    s = re.sub(r'[^\w\s-]', '', text).strip().lower()
    # Replace spaces with hyphens
    s = re.sub(r'[-\s]+', '-', s)
    # Truncate to max_length
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
    print("--- Node: Code Generation ---")
    requirements = state["requirements"]

    code_prompt = (
        f"Based on these requirements: {requirements.get('task', 'a programming task')}. "
        f"Generate a {requirements.get('language', 'python')} script. "
        "Provide only the code block, no extra text or explanations outside the code block. " 
        "Write good quality code.  with proper indentation and use the best practices." 
        "Provide docstrings documentation for the code and keep comments to minimum and only if necessary."
        "Ensure the code is executable and simple."
    )
    
    response_content = chat_model.invoke([HumanMessage(content=code_prompt)]).content

    start_token = "```python"
    end_token = "```"
    if start_token in response_content and end_token in response_content:
        code_block = response_content.split(start_token)[1].split(end_token)[0]
    else:
        code_block = response_content.strip()
    
    print(f"Generated Code:\n{code_block}")
    state["chat_history"].append({"role": "user", "content": code_prompt})
    state["chat_history"].append({"role": "assistant", "content": response_content})
    return {"generated_code": code_block, "chat_history": state["chat_history"]}


def save_code(state: AgentState) -> Dict:
    print("--- Node: Save Code ---")
    final_code = state["generated_code"]
    requirements = state["requirements"]
    
    output_dir = "generated_code"
    os.makedirs(output_dir, exist_ok=True) # Create the directory if it doesn't exist

    # Use the 'task' from requirements to name the file
    task_name = requirements.get("task", "unknown_task")
    filename = f"{filenaming_function(task_name)}.py"
    output_file_path = os.path.join(output_dir, filename)
    
    try:
        with open(output_file_path, "w") as f:
            f.write(final_code)
        print(f"Final code saved to: {output_file_path}")
        state["output_file_path"] = output_file_path
    except Exception as e:
        print(f"Error saving file: {e}")
        state["output_file_path"] = None # Indicate failure to save
        
    return {"output_file_path": state["output_file_path"]}


workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("initialize_state", initialize_state)
workflow.add_node("generate_code", generate_code)
workflow.add_node("save_code", save_code)

# Add edges
workflow.add_edge("initialize_state", "generate_code")
workflow.add_edge("generate_code", "save_code")
workflow.add_edge("save_code", END)

workflow.set_entry_point("initialize_state")

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
        output_file_path=None
    )
    graph.invoke(state)
    return state


if __name__ == "__main__":
    print(f"Hi, I am your personal code generation agent. I will generate pythoncode for you based on your request!")
    user_request = input("Enter your request: ")    
    state = code_generation_agent(user_request)
    print(f"Code generated and saved to: {state['output_file_path']}")
    print("Thank you for using my service. Goodbye!")
