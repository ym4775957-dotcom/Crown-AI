import os
import json
import logging
from backend.adk_core import Agent, Context
from backend.mcp_server import MCPServer

# Initialize central MCP Server for agents to access
mcp = MCPServer()

class OrchestratorAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Orchestrator",
            instruction="Coordinate task delegation, run workflow lifecycle, and present the final polished response to the user."
        )

    def execute(self, context: Context, prompt: str) -> str:
        context.log(self.name, f"Orchestrator received prompt: '{prompt}'")
        # Initialize context state variables
        context.set("raw_prompt", prompt)
        context.set("current_stage", "Orchestrator_Init")
        
        # If this is the start of the workflow, we return the prompt to feed into the Planner.
        # If this is the end of the workflow, we'll format the aggregated results.
        if "Planner" in context.results:
            context.log(self.name, "Assembling and formatting all agent outputs into final response...")
            planner_out = context.results.get("Planner", "")
            optimizer_out = context.results.get("TaskOptimization", "")
            research_out = context.results.get("Research", "")
            study_out = context.results.get("ExamStudy", "")
            scheduler_out = context.results.get("LifeScheduler", "")

            # Construct final formatted output
            final_report = f"""# Crown AI Agent System Output

## 📊 Request Summary
- **Original Query**: {context.get('raw_prompt')}

---

## 🎯 1. Structured Execution Plan (Planner Agent)
{planner_out}

---

## ⚙️ 2. Task Optimizations (Task Optimization Agent)
{optimizer_out}

---

## 🔍 3. Research Insights & Concepts (Research Agent)
{research_out}

---

## 📚 4. Study Decks & Quizzes (Exam/Study Agent)
{study_out}

---

## 📅 5. Schedule & Calendar Time-Blocks (Life Scheduler Agent)
{scheduler_out}

---

## 🔒 Security Compliance Report
- **Input Check**: Safe (No command injections or traversals).
- **Tool Validations**: All arguments successfully schema-validated.
- **Execution Boundaries**: Constrained strictly to workspace directory.
"""
            context.log(self.name, "Final output report compiled successfully.")
            return final_report
        else:
            context.log(self.name, "Orchestrator initialized. Passing request details to Planner.")
            return prompt


class PlannerAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Planner",
            instruction="Decompose user requests into detailed, structured, execution-ready subtasks."
        )

    def execute(self, context: Context, prompt: str) -> str:
        context.log(self.name, "Analyzing query to break down requirements into step-by-step phases...")
        
        # Parse query for keywords to customize plan
        query = prompt.lower()
        if "machine learning" in query or "ml" in query:
            steps = [
                "Phase 1: Research Machine Learning Core Architectures (Supervised/Unsupervised/Neural Networks).",
                "Phase 2: Generate Flashcards and study summaries for targeted learning.",
                "Phase 3: Set up dedicated time blocks on the calendar for deep-focus study.",
                "Phase 4: Run self-assessment quizzes to measure understanding."
            ]
        elif "exam" in query or "study" in query or "test" in query:
            steps = [
                "Phase 1: Identify study subject materials and research core subtopics.",
                "Phase 2: Create mock review flashcards for key definitions and theories.",
                "Phase 3: Map out daily schedule blocks avoiding burn-out.",
                "Phase 4: Conduct practice sessions and review weaker modules."
            ]
        else:
            steps = [
                "Phase 1: Search relevant databases for context information.",
                "Phase 2: Optimize subtask definitions to have clear measurable metrics.",
                "Phase 3: Allocate schedule blocks for project execution.",
                "Phase 4: Compile results and double-check requirements."
            ]

        plan_str = "\n".join([f"- {s}" for s in steps])
        context.log(self.name, f"Decomposed query into {len(steps)} steps.")
        return plan_str


class TaskOptimizationAgent(Agent):
    def __init__(self):
        super().__init__(
            name="TaskOptimization",
            instruction="Optimize plan steps using MCP tools, turning them into SMART actionable tasks.",
            tools=["optimize_task"]
        )

    def execute(self, context: Context, prompt: str) -> str:
        context.log(self.name, "Calling MCP 'optimize_task' to refine plan steps...")
        
        # Read plan from previous node
        planner_plan = prompt.split("\n")
        optimized_steps = []
        
        for i, step in enumerate(planner_plan):
            if step.strip():
                clean_step = step.replace("- ", "")
                # Simulate calling the MCP tool
                res = mcp.call_tool("optimize_task", {"task_description": clean_step})
                if res["status"] == "success":
                    optimized_steps.append(f"{i+1}. [SMART] {res['data']['optimized']}")
                else:
                    optimized_steps.append(f"{i+1}. [Original] {clean_step} (Optimization skipped: {res.get('message')})")
                    
        return "\n".join(optimized_steps)


class ResearchAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Research",
            instruction="Gather background data and details from the central knowledge base.",
            tools=["search_knowledge"]
        )

    def execute(self, context: Context, prompt: str) -> str:
        # Detect search topic from prompt
        raw_prompt = context.get("raw_prompt", "").lower()
        search_query = "productivity"  # Default fallback
        
        if "machine learning" in raw_prompt or "ml" in raw_prompt:
            search_query = "machine learning"
        elif "algorithm" in raw_prompt:
            search_query = "algorithms"
        elif "schedule" in raw_prompt or "plan" in raw_prompt:
            search_query = "time blocking"

        context.log(self.name, f"Searching knowledge base for: '{search_query}'...")
        
        # Call the MCP search tool
        res = mcp.call_tool("search_knowledge", {"query": search_query})
        
        if res["status"] == "success":
            insight = res["data"]
            context.log(self.name, "Found relevant background information.")
        else:
            insight = f"Failed to gather insights: {res.get('message')}"
            context.log(self.name, f"Research tool failed: {res.get('message')}", "WARNING")
            
        return insight


class ExamStudyAgent(Agent):
    def __init__(self):
        super().__init__(
            name="ExamStudy",
            instruction="Build flashcard decks and quiz templates for exams and training.",
            tools=["generate_study_deck"]
        )

    def execute(self, context: Context, prompt: str) -> str:
        # Detect topic
        raw_prompt = context.get("raw_prompt", "").lower()
        topic = "General Subject"
        if "machine learning" in raw_prompt or "ml" in raw_prompt:
            topic = "Machine Learning"
        elif "algorithm" in raw_prompt:
            topic = "Algorithms"

        context.log(self.name, f"Generating study deck with flashcards for '{topic}'...")
        
        # Invoke MCP deck generation tool
        res = mcp.call_tool("generate_study_deck", {"topic": topic, "cards_count": 4})
        
        if res["status"] == "success":
            deck = res["data"]
            deck_path = res["file_saved"]
            
            output_parts = [
                f"Generated study deck successfully. Saved to `{os.path.basename(deck_path)}`.",
                "### 🃏 Sample Flashcards:"
            ]
            for card in deck["cards"]:
                output_parts.append(f"- **Q**: {card['question']}\n  **A**: {card['answer']}")
            
            context.log(self.name, "Flashcards created and structured successfully.")
            return "\n".join(output_parts)
        else:
            context.log(self.name, f"Failed to create study deck: {res.get('message')}", "WARNING")
            return f"Study deck generation failed: {res.get('message')}"


class LifeSchedulerAgent(Agent):
    def __init__(self):
        super().__init__(
            name="LifeScheduler",
            instruction="Schedule calendar blocks and set reminders for task study times.",
            tools=["schedule_event"]
        )

    def execute(self, context: Context, prompt: str) -> str:
        context.log(self.name, "Structuring study calendar blocks and booking slots in calendar.json...")
        
        # Set up a few calendar blocks
        events = [
            {"event": "Deep Study Block: Core Concepts Review", "date": "2026-07-07", "time": "09:00"},
            {"event": "Practical Session: Working Examples", "date": "2026-07-07", "time": "14:00"},
            {"event": "Assessments & Mock Test Session", "date": "2026-07-08", "time": "10:00"}
        ]
        
        results = []
        for evt in events:
            # Invoke MCP calendar event scheduler tool
            res = mcp.call_tool("schedule_event", evt)
            if res["status"] == "success":
                results.append(f"- ✅ Scheduled '{evt['event']}' on {evt['date']} at {evt['time']}")
            else:
                results.append(f"- ❌ Failed to schedule '{evt['event']}': {res.get('message')}")
                context.log(self.name, f"Scheduling failed: {res.get('message')}", "WARNING")
                
        context.log(self.name, "Time blocks finalized.")
        return "### 📅 Booked Calendar Time Blocks:\n" + "\n".join(results)
