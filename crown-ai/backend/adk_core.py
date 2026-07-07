import logging
from typing import Dict, List, Tuple, Callable, Any, Union

# Set up logger
logger = logging.getLogger("adk_core")
logging.basicConfig(level=logging.INFO)

class Context:
    """Represents the execution context shared between agents in a workflow."""
    def __init__(self, initial_input: str = ""):
        self.input: str = initial_input
        self.variables: Dict[str, Any] = {}
        self.logs: List[Dict[str, Any]] = []
        self.active_agent: str = "START"
        self.results: Dict[str, Any] = {}

    def log(self, agent_name: str, message: str, level: str = "INFO"):
        """Logs agent activity."""
        log_entry = {
            "agent": agent_name,
            "message": message,
            "level": level
        }
        self.logs.append(log_entry)
        logger.info(f"[{agent_name}] {message}")

    def set(self, key: str, value: Any):
        self.variables[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.variables.get(key, default)


class Agent:
    """Represents a single AI Agent in the ADK multi-agent framework."""
    def __init__(self, name: str, instruction: str, tools: List[str] = None):
        self.name = name
        self.instruction = instruction
        self.tools = tools or []

    def execute(self, context: Context, prompt: str) -> str:
        """Executes the agent's logic. In a live system, this connects to Gemini/LLM."""
        context.log(self.name, f"Thinking about: '{prompt[:100]}...'")
        
        # We will implement custom specialized simulated response logic in agents.py,
        # but this base execution function provides a fallback standard execution.
        response = f"Agent [{self.name}] processed prompt: {prompt}"
        context.log(self.name, f"Finished execution successfully.")
        return response


class Workflow:
    """Orchestrates multiple agents and functions as a graph-based workflow."""
    def __init__(self, name: str):
        self.name = name
        self.nodes: Dict[str, Union[Agent, Callable[[Context], Any]]] = {}
        self.edges: List[Tuple[str, str]] = []
        self.log_callback: Callable[[Dict[str, Any]], None] = None

    def set_log_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Sets a callback function to stream logs in real-time (e.g., to WebSockets)."""
        self.log_callback = callback

    def add_node(self, name: str, node: Union[Agent, Callable[[Context], Any]]):
        """Adds an Agent or simple function to the workflow execution graph."""
        self.nodes[name] = node

    def add_edge(self, from_node: str, to_node: str):
        """Adds a directed connection between two nodes in the execution workflow."""
        self.edges.append((from_node, to_node))

    def _trigger_log(self, agent: str, message: str, level: str = "INFO"):
        if self.log_callback:
            try:
                self.log_callback({"agent": agent, "message": message, "level": level})
            except Exception as e:
                logger.error(f"Error in workflow log callback: {e}")

    def run(self, initial_input: str) -> Context:
        """Runs the workflow. Executes nodes sequentially along the defined edges."""
        context = Context(initial_input)
        context.log("SYSTEM", f"Starting workflow: {self.name}")
        self._trigger_log("SYSTEM", f"Starting workflow: {self.name}")

        # Find starting nodes (nodes that have edges originating from 'START' or no incoming edges)
        current_node_name = "START"
        
        # In this simple but robust implementation, we run nodes sequentially following
        # defined edges. Since we have a specific pipeline:
        # Orchestrator -> Planner -> Task Optimizer -> Research -> Exam/Study -> Life Scheduler -> Orchestrator (Final Output)
        # We trace paths starting from START, going node to node.
        path = []
        visited = set()
        
        # Traverse the defined edges sequentially
        curr = "START"
        while True:
            # Find next node connected to curr
            next_nodes = [to_n for from_n, to_n in self.edges if from_n == curr]
            if not next_nodes:
                break
            
            # Pick first unvisited connected node
            next_node = None
            for n in next_nodes:
                if n not in visited:
                    next_node = n
                    break
            
            if not next_node:
                # If all are visited or no forward node, stop
                break
                
            path.append(next_node)
            visited.add(next_node)
            curr = next_node

        context.log("SYSTEM", f"Workflow execution path: {' -> '.join(path)}")
        self._trigger_log("SYSTEM", f"Workflow execution path: {' -> '.join(path)}")

        # Execute each node in path
        current_input = initial_input
        for node_name in path:
            if node_name not in self.nodes:
                context.log("SYSTEM", f"Warning: Node {node_name} not found in nodes dictionary.", "WARNING")
                self._trigger_log("SYSTEM", f"Warning: Node {node_name} not found.", "WARNING")
                continue

            node = self.nodes[node_name]
            context.active_agent = node_name
            
            context.log("SYSTEM", f"Transitioning to Agent: {node_name}")
            self._trigger_log(node_name, f"Active State: RUNNING", "STATUS")

            try:
                if isinstance(node, Agent):
                    # For agents, invoke execute
                    output = node.execute(context, current_input)
                else:
                    # For callable functions/nodes
                    output = node(context)

                context.results[node_name] = output
                # The output of this agent becomes the input for the next agent
                current_input = output
                context.log("SYSTEM", f"Completed Agent: {node_name}")
                self._trigger_log(node_name, f"Active State: IDLE", "STATUS")
                
            except Exception as e:
                context.log(node_name, f"Execution failed with error: {str(e)}", "ERROR")
                self._trigger_log(node_name, f"Execution failed: {str(e)}", "ERROR")
                self._trigger_log(node_name, f"Active State: ERROR", "STATUS")
                # Stop execution on failure
                break

        context.log("SYSTEM", f"Workflow {self.name} finished.")
        self._trigger_log("SYSTEM", f"Workflow finished.", "SUCCESS")
        return context
