import os
import asyncio
import json
import logging
from typing import List, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.config import HOST, PORT, BASE_DIR, WORKSPACE_DIR
from backend.security import validate_user_query
from backend.adk_core import Workflow, Context
from backend.agents import (
    OrchestratorAgent,
    PlannerAgent,
    TaskOptimizationAgent,
    ResearchAgent,
    ExamStudyAgent,
    LifeSchedulerAgent,
    mcp
)

# Logger setup
logger = logging.getLogger("crown_server")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Crown AI API Server", version="1.0.0")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        disconnected_sockets = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send websocket message: {e}")
                disconnected_sockets.append(connection)
        
        # Clean up dead sockets
        for dead_ws in disconnected_sockets:
            self.disconnect(dead_ws)

manager = ConnectionManager()

# Request schemas
class TaskRequest(BaseModel):
    prompt: str

# Endpoints
@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "Crown AI Engine"}

@app.get("/api/agents")
def get_agents():
    """Returns metadata of the registered multi-agent system."""
    return {
        "agents": [
            {"name": "Orchestrator", "role": "Coordinator", "tools": []},
            {"name": "Planner", "role": "Task Planner & Decomposer", "tools": []},
            {"name": "TaskOptimization", "role": "SMART Refiner", "tools": ["optimize_task"]},
            {"name": "Research", "role": "Knowledge Researcher", "tools": ["search_knowledge"]},
            {"name": "ExamStudy", "role": "Flashcard Generator", "tools": ["generate_study_deck"]},
            {"name": "LifeScheduler", "role": "Calendar time blocker", "tools": ["schedule_event"]}
        ]
    }

@app.get("/api/mcp-tools")
def get_mcp_tools():
    """Exposes the MCP tools registry directly to clients."""
    return {"tools": mcp.list_tools()}

@app.get("/api/calendar")
def get_calendar_events():
    """Returns scheduled calendar items from workspace calendar.json."""
    calendar_file = os.path.join(WORKSPACE_DIR, "calendar.json")
    if not os.path.exists(calendar_file):
        return []
    try:
        with open(calendar_file, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading calendar: {e}")
        return []

@app.post("/api/execute")
async def execute_workflow(request: TaskRequest):
    """Executes the complete multi-agent workflow for a given prompt."""
    prompt = request.prompt
    
    # 1. Security check: Validate user query
    is_valid, msg = validate_user_query(prompt)
    if not is_valid:
        await manager.broadcast({
            "agent": "SecurityGuard",
            "message": f"Execution BLOCKED: {msg}",
            "level": "ERROR"
        })
        raise HTTPException(status_code=400, detail=msg)

    await manager.broadcast({
        "agent": "SecurityGuard",
        "message": "Input validation complete. Prompt matches security guidelines.",
        "level": "SUCCESS"
    })

    # 2. Build the ADK Multi-Agent Workflow
    workflow = Workflow("Crown_AI_Main_Workflow")
    
    # Instantiate agents
    orchestrator = OrchestratorAgent()
    planner = PlannerAgent()
    task_opt = TaskOptimizationAgent()
    research = ResearchAgent()
    exam_study = ExamStudyAgent()
    life_sched = LifeSchedulerAgent()

    # Register nodes
    workflow.add_node("Orchestrator_Start", orchestrator)
    workflow.add_node("Planner", planner)
    workflow.add_node("TaskOptimization", task_opt)
    workflow.add_node("Research", research)
    workflow.add_node("ExamStudy", exam_study)
    workflow.add_node("LifeScheduler", life_sched)
    workflow.add_node("Orchestrator_End", orchestrator)

    # Establish edges (workflow graph pipeline)
    workflow.add_edge("START", "Orchestrator_Start")
    workflow.add_edge("Orchestrator_Start", "Planner")
    workflow.add_edge("Planner", "TaskOptimization")
    workflow.add_edge("TaskOptimization", "Research")
    workflow.add_edge("Research", "ExamStudy")
    workflow.add_edge("ExamStudy", "LifeScheduler")
    workflow.add_edge("LifeScheduler", "Orchestrator_End")

    # Set up log callback to stream steps live to connected WebSocket clients
    def ws_log_streamer(log_data: Dict[str, Any]):
        # Run async call in background thread using run_coroutine_threadsafe if needed,
        # but since FastAPI is running in a loop we can run it on the current event loop.
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(manager.broadcast(log_data), loop)
        except Exception as err:
            logger.error(f"Failed to stream logs via websocket: {err}")

    workflow.set_log_callback(ws_log_streamer)

    # 3. Execute Workflow in a separate thread/task so it doesn't block the API
    try:
        # Run synchronous workflow execution in an executor thread
        loop = asyncio.get_running_loop()
        context = await loop.run_in_executor(None, workflow.run, prompt)
        
        final_output = context.results.get("Orchestrator_End", "Workflow executed without compiled final output.")
        return {
            "status": "success",
            "final_report": final_output,
            "logs": context.logs
        }
    except Exception as e:
        await manager.broadcast({
            "agent": "SYSTEM",
            "message": f"Fatal workflow crash: {str(e)}",
            "level": "ERROR"
        })
        raise HTTPException(status_code=500, detail=f"Workflow failed: {str(e)}")

# WebSocket route
@app.websocket("/api/ws/logs")
async def websocket_logs_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Respond to ping or other messages if needed
            await websocket.send_json({"agent": "SYSTEM", "message": "Connection active", "level": "INFO"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Mount frontend static files
# Make sure frontend dir exists
frontend_path = os.path.join(BASE_DIR, "frontend")
os.makedirs(frontend_path, exist_ok=True)
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting Crown AI Server on http://{HOST}:{PORT}")
    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=True)
