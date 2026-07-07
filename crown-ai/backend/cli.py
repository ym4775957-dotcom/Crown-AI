import sys
import io

# Force UTF-8 output encoding on Windows to safely print reports with emojis
if sys.platform.startswith("win"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import argparse
from backend.security import validate_user_query
from backend.adk_core import Workflow
from backend.agents import (
    OrchestratorAgent,
    PlannerAgent,
    TaskOptimizationAgent,
    ResearchAgent,
    ExamStudyAgent,
    LifeSchedulerAgent,
    mcp
)

def run_workflow_locally(prompt: str):
    """Executes the full multi-agent pipeline directly from the command line."""
    print("=" * 60)
    print("CROWN AI - COMMAND LINE INTERFACE")
    print("=" * 60)
    print(f"Task Input: '{prompt}'\n")

    # 1. Input Security Guard
    print("[SecurityGuard] Performing prompt safety checks...")
    valid, msg = validate_user_query(prompt)
    if not valid:
        print(f"[SecurityGuard] [BLOCKED]: {msg}")
        sys.exit(1)
    print("[SecurityGuard] [VALIDATED]: Prompt is safe for execution.\n")

    # 2. Build multi-agent DAG
    workflow = Workflow("Crown_AI_CLI_Workflow")
    
    orchestrator = OrchestratorAgent()
    planner = PlannerAgent()
    task_opt = TaskOptimizationAgent()
    research = ResearchAgent()
    exam_study = ExamStudyAgent()
    life_sched = LifeSchedulerAgent()

    workflow.add_node("Orchestrator_Start", orchestrator)
    workflow.add_node("Planner", planner)
    workflow.add_node("TaskOptimization", task_opt)
    workflow.add_node("Research", research)
    workflow.add_node("ExamStudy", exam_study)
    workflow.add_node("LifeScheduler", life_sched)
    workflow.add_node("Orchestrator_End", orchestrator)

    workflow.add_edge("START", "Orchestrator_Start")
    workflow.add_edge("Orchestrator_Start", "Planner")
    workflow.add_edge("Planner", "TaskOptimization")
    workflow.add_edge("TaskOptimization", "Research")
    workflow.add_edge("Research", "ExamStudy")
    workflow.add_edge("ExamStudy", "LifeScheduler")
    workflow.add_edge("LifeScheduler", "Orchestrator_End")

    # Define a clean stdout logger callback
    def cli_log_callback(log_entry):
        agent = log_entry["agent"]
        msg = log_entry["message"]
        level = log_entry["level"]
        
        # Color coding for terminal output
        if level == "STATUS":
            print(f"\033[94m[{agent}]\033[0m state change -> {msg}")
        elif level == "ERROR":
            print(f"\033[91m[{agent}] [ERROR] {msg}\033[0m")
        elif level == "SUCCESS":
            print(f"\033[92m[{agent}] [SUCCESS] {msg}\033[0m")
        elif level == "WARNING":
            print(f"\033[93m[{agent}] [WARNING] {msg}\033[0m")
        else:
            print(f"[{agent}] {msg}")

    workflow.set_log_callback(cli_log_callback)

    # 3. Execution
    print("Initiating Multi-Agent Workflow Engine...")
    context = workflow.run(prompt)
    
    print("\n" + "=" * 60)
    print("WORKFLOW COMPLETE - FINAL REPORT")
    print("=" * 60)
    print(context.results.get("Orchestrator_End", "Error: Final report not assembled."))
    print("=" * 60)

def list_mcp_tools():
    """Prints registered MCP tools schema."""
    print("=" * 60)
    print("REGISTERED MCP TOOLS SCHEMAS")
    print("=" * 60)
    tools = mcp.list_tools()
    for tool in tools:
        print(f"- Tool: {tool['name']}")
        print(f"  Description: {tool['description']}")
        print(f"  Schema: {tool['inputSchema']}\n")
    print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="Crown AI CLI Multi-Agent System runner.")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Run subcommand
    run_parser = subparsers.add_parser("run", help="Run the multi-agent system on a prompt")
    run_parser.add_argument("prompt", type=str, help="The prompt to analyze and schedule")

    # Tools subcommand
    subparsers.add_parser("tools", help="List registered MCP tools and capabilities")

    # Validate subcommand
    val_parser = subparsers.add_parser("validate", help="Check security validation of a query")
    val_parser.add_argument("prompt", type=str, help="Prompt to run safety check on")

    args = parser.parse_args()

    if args.command == "run":
        run_workflow_locally(args.prompt)
    elif args.command == "tools":
        list_mcp_tools()
    elif args.command == "validate":
        valid, msg = validate_user_query(args.prompt)
        status = "[SAFE]" if valid else "[DANGEROUS/BLOCKED]"
        print(f"Prompt Check: {status} - Details: {msg}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
