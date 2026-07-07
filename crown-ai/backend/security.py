import os
import re
from typing import Dict, Any, Tuple
from backend.config import ALLOWED_PATHS, ALLOWED_EXTENSIONS

# Dangerous command injection patterns
BLACKLISTED_PATTERNS = [
    r"rm\s+-rf",          # Linux delete command
    r"format\s+[a-zA-Z]:",# Disk format
    r"mkfs",              # Make filesystem
    r"dd\s+if=",          # DD copy disk
    r"shutdown\s+",       # System shutdown
    r"del\s+/s",          # Windows delete commands
    r"format\s+/q",
    r"cmd\.exe",          # Shell execution
    r"powershell",        # Powershell execution
    r"/bin/bash",         # Bash shell
    r"/bin/sh",           # Sh shell
    r"chmod\s+",          # Privilege adjustment
    r"chown\s+",
]

# Blacklisted Python imports for sandbox validation
BLACKLISTED_PYTHON_IMPORTS = [
    "os", "subprocess", "sys", "shutil", "builtins", "eval", "exec", "urllib", "requests"
]

def validate_user_query(query: str) -> Tuple[bool, str]:
    """Validates if a user's prompt is safe to process by agents."""
    if not query or not isinstance(query, str):
        return False, "Query must be a valid non-empty string."

    # Check for shell command injection patterns
    for pattern in BLACKLISTED_PATTERNS:
        if re.search(pattern, query, re.IGNORECASE):
            return False, f"Security Violation: Malicious input pattern detected ({pattern})."

    # Check for directory traversal attempts
    if "../" in query or "..\\" in query:
        return False, "Security Violation: Directory traversal patterns detected."

    return True, "Query validation passed."


def validate_file_path(path: str) -> Tuple[bool, str]:
    """Enforces directory constraint, ensuring all paths are within allowed workspace boundaries."""
    if not path:
        return False, "Path is empty."

    # Normalize path
    norm_path = os.path.abspath(path).replace("\\", "/")
    
    # Resolve absolute paths and check against allowed workspace paths
    is_allowed = False
    for allowed in ALLOWED_PATHS:
        allowed_norm = os.path.abspath(allowed).replace("\\", "/")
        if norm_path.startswith(allowed_norm):
            is_allowed = True
            break

    if not is_allowed:
        return False, f"Security Violation: Path '{path}' is outside the authorized workspace boundaries."

    # Check file extension safety
    _, ext = os.path.splitext(norm_path)
    if ext and ext.lower() not in ALLOWED_EXTENSIONS:
        return False, f"Security Violation: File extension '{ext}' is not permitted."

    return True, "Path validation passed."


def validate_python_code(code: str) -> Tuple[bool, str]:
    """Validates Python code blocks before any execution simulation to prevent imports of harmful modules."""
    for module in BLACKLISTED_PYTHON_IMPORTS:
        # Search for 'import module' or 'from module import'
        import_pattern1 = rf"\bimport\s+{module}\b"
        import_pattern2 = rf"\bfrom\s+{module}\s+import\b"
        exec_pattern = rf"\b(eval|exec)\s*\("
        
        if re.search(import_pattern1, code) or re.search(import_pattern2, code) or re.search(exec_pattern, code):
            return False, f"Security Violation: Blocked use of dangerous modules or execution keywords ({module}/eval/exec)."
            
    return True, "Python code validation passed."


def validate_mcp_tool_arguments(tool_name: str, arguments: Dict[str, Any]) -> Tuple[bool, str]:
    """Validates the structure and parameter limits of MCP tool calls."""
    if not isinstance(arguments, dict):
        return False, "Arguments must be a key-value dictionary."

    if tool_name == "schedule_event":
        event = arguments.get("event")
        date = arguments.get("date")
        time = arguments.get("time")

        if not event or not isinstance(event, str):
            return False, "Tool Argument Error: 'event' must be a non-empty string."
        if not date or not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
            return False, "Tool Argument Error: 'date' must be in YYYY-MM-DD format."
        if not time or not re.match(r"^\d{2}:\d{2}$", time):
            return False, "Tool Argument Error: 'time' must be in HH:MM format."

    elif tool_name == "generate_study_deck":
        topic = arguments.get("topic")
        cards_count = arguments.get("cards_count", 5)

        if not topic or not isinstance(topic, str):
            return False, "Tool Argument Error: 'topic' must be a non-empty string."
        if not isinstance(cards_count, int) or cards_count < 1 or cards_count > 50:
            return False, "Tool Argument Error: 'cards_count' must be an integer between 1 and 50."

    elif tool_name == "search_knowledge":
        query = arguments.get("query")
        if not query or not isinstance(query, str):
            return False, "Tool Argument Error: 'query' must be a non-empty string."
        # Sanitise tool queries
        ok, msg = validate_user_query(query)
        if not ok:
            return False, f"Tool Argument Error: {msg}"

    elif tool_name == "optimize_task":
        task_desc = arguments.get("task_description")
        if not task_desc or not isinstance(task_desc, str):
            return False, "Tool Argument Error: 'task_description' must be a non-empty string."

    return True, "Tool arguments validated successfully."
