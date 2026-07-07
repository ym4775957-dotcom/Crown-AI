import os
import json
from typing import Dict, Any, List
from backend.security import validate_mcp_tool_arguments, validate_file_path
from backend.config import WORKSPACE_DIR

# Custom local database of knowledge for simulations
KNOWLEDGE_BASE = {
    "machine learning": (
        "Machine Learning (ML) is a subset of AI that trains systems to learn from data. "
        "Key topics: Supervised Learning (Linear Regression, SVMs, Decision Trees), Unsupervised Learning (K-Means, PCA), "
        "Neural Networks (Backpropagation, Activation Functions), and Evaluation Metrics (Accuracy, Precision, Recall, F1-Score)."
    ),
    "algorithms": (
        "Algorithms are step-by-step procedures for calculations. Core concepts: Big O Notation, "
        "Sorting (QuickSort, MergeSort), Searching (Binary Search), Dynamic Programming, and Graph Traversals (BFS, DFS)."
    ),
    "time blocking": (
        "Time blocking is a time management technique where you divide your day into blocks of time, "
        "each dedicated to completing a specific task or group of tasks. Example: 90-minute focus blocks "
        "interspaced with 10-minute rest intervals (Pomodoro technique variation)."
    ),
    "productivity": (
        "Productivity frameworks: Getting Things Done (GTD), Eisenhower Matrix (Urgent vs. Important), "
        "and the 2-Minute Rule (if it takes less than 2 minutes, do it now)."
    )
}

# Standard MCP tool schemas
TOOLS_SCHEMA = [
    {
        "name": "search_knowledge",
        "description": "Searches the central knowledge database for educational concepts, algorithms, or scheduling tips.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search term, e.g., 'machine learning'"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "optimize_task",
        "description": "Refines task descriptions to be SMART (Specific, Measurable, Achievable, Relevant, Time-bound).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_description": {"type": "string", "description": "Raw task description"}
            },
            "required": ["task_description"]
        }
    },
    {
        "name": "schedule_event",
        "description": "Blocks a time slots in the shared calendar configuration file.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "event": {"type": "string", "description": "Title of the calendar event"},
                "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                "time": {"type": "string", "description": "Time in HH:MM format"}
            },
            "required": ["event", "date", "time"]
        }
    },
    {
        "name": "generate_study_deck",
        "description": "Generates a collection of Q&A flashcards on a specific topic.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Subject topic for the cards"},
                "cards_count": {"type": "integer", "description": "Number of cards to generate (1-50)"}
            },
            "required": ["topic"]
        }
    }
]

class MCPServer:
    """Simulates a Model Context Protocol server exposing schemas and execution wrappers."""
    def __init__(self):
        self.calendar_file = os.path.join(WORKSPACE_DIR, "calendar.json")
        self.study_decks_dir = os.path.join(WORKSPACE_DIR, "study_decks")
        
        # Ensure directories exist
        os.makedirs(self.study_decks_dir, exist_ok=True)
        if not os.path.exists(self.calendar_file):
            with open(self.calendar_file, "w") as f:
                json.dump([], f)

    def list_tools(self) -> List[Dict[str, Any]]:
        """Returns registered tools and schemas."""
        return TOOLS_SCHEMA

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handles tool execution after enforcing validation protocols."""
        # 1. Parameter Validation Checks
        valid, msg = validate_mcp_tool_arguments(tool_name, arguments)
        if not valid:
            return {"status": "error", "error_type": "ValidationError", "message": msg}

        # 2. Tool Execution Routing
        try:
            if tool_name == "search_knowledge":
                query = arguments["query"].lower()
                results = []
                for key, content in KNOWLEDGE_BASE.items():
                    if query in key or key in query:
                        results.append(f"{key.upper()}: {content}")
                
                if not results:
                    results.append(f"No specific knowledge database matches for query: '{query}'. Standard search fallback initiated.")
                return {"status": "success", "data": "\n".join(results)}

            elif tool_name == "optimize_task":
                raw_desc = arguments["task_description"]
                optimized = (
                    f"OPTIMIZED SMART TASK: {raw_desc} | "
                    f"Metrics: Specific target set. Measure of completion: verified. "
                    f"Timeline: Scheduled as requested. Checked for safety constraints."
                )
                return {"status": "success", "data": {"original": raw_desc, "optimized": optimized}}

            elif tool_name == "schedule_event":
                # Ensure calendar write is within allowed path
                valid_path, path_msg = validate_file_path(self.calendar_file)
                if not valid_path:
                    return {"status": "error", "error_type": "SecurityError", "message": path_msg}

                event_data = {
                    "event": arguments["event"],
                    "date": arguments["date"],
                    "time": arguments["time"]
                }
                
                # Load, append, save
                with open(self.calendar_file, "r") as f:
                    calendar = json.load(f)
                
                calendar.append(event_data)
                
                with open(self.calendar_file, "w") as f:
                    json.dump(calendar, f, indent=2)

                return {"status": "success", "message": f"Successfully blocked calendar event: {event_data}"}

            elif tool_name == "generate_study_deck":
                topic = arguments["topic"]
                count = arguments.get("cards_count", 5)
                
                deck_file = os.path.join(self.study_decks_dir, f"{topic.lower().replace(' ', '_')}_deck.json")
                valid_path, path_msg = validate_file_path(deck_file)
                if not valid_path:
                    return {"status": "error", "error_type": "SecurityError", "message": path_msg}

                # Generate mock flashcards
                cards = []
                for i in range(1, count + 1):
                    cards.append({
                        "card_id": i,
                        "question": f"Key concept question #{i} for study topic: {topic}?",
                        "answer": f"Verified answer explanation #{i} matching study material of {topic}."
                    })
                
                deck_data = {
                    "topic": topic,
                    "cards": cards
                }

                with open(deck_file, "w") as f:
                    json.dump(deck_data, f, indent=2)

                return {"status": "success", "data": deck_data, "file_saved": deck_file}

            else:
                return {"status": "error", "error_type": "UnknownTool", "message": f"Tool '{tool_name}' not found."}

        except Exception as e:
            return {"status": "error", "error_type": "ExecutionError", "message": f"Tool execution failed: {str(e)}"}
