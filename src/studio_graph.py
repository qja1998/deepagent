"""LangGraph Studio entrypoint for Cursor Clone Agent - Agent Mode Only."""
import os
from dotenv import load_dotenv

from src.orchestrator import CursorAgentOrchestrator
from src.state.graph_state import AgentState

# Load environment variables
load_dotenv()

# Build the orchestrator graph (Agent Mode only)
orchestrator = CursorAgentOrchestrator(project_root=".")
graph = orchestrator.graph


# Helper function for creating test inputs
def create_test_input(
    user_input: str = "Explain this code",
    current_file: str = None,
    selection: dict = None
):
    """Helper function to create test inputs for the graph.
    
    Args:
        user_input: User's input/question
        current_file: Current file path
        selection: Selection range dict with start_line, end_line
        
    Returns:
        Initial AgentState for CursorAgent
    """
    state: AgentState = {
        "user_input": user_input,
        "context": {},
        "messages": [],
        "plan": None,
        "selected_tool": None,
        "tool_input": None,
        "tool_output": None,
        "reflection": None,
        "iteration_count": 0,
        "max_iterations": 5,
        "best_result": None,
        "best_quality": 0.0,
        "current_quality": 0.0,
        "improved": False,
        "history": [],
        "next_action": "continue",
        "should_continue": True,
        "final_output": None,
        "errors": []
    }
    
    # Set current file if provided
    if current_file:
        orchestrator.context_manager.set_current_file(current_file)
    
    # Set selection if provided
    if selection:
        orchestrator.context_manager.set_selection(
            start_line=selection.get("start_line", 1),
            end_line=selection.get("end_line", 1)
        )
    
    return state


# Example inputs for testing in Studio
EXAMPLE_INPUTS = {
    "simple_task": create_test_input(
        user_input="What does this function do?",
        current_file="src/agents/react_agent.py",
        selection={"start_line": 86, "end_line": 100}
    ),
    
    "code_explanation": create_test_input(
        user_input="Explain the ReActAgent class and how it works",
        current_file="src/agents/react_agent.py"
    ),
    
    "complex_task": create_test_input(
        user_input="Implement error handling for all file operations in the project"
    ),
    
    "multi_step": create_test_input(
        user_input="Analyze the project structure, identify issues, and suggest improvements"
    ),
}

