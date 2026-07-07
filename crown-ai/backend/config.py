import os

# Base directory paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE_DIR = os.path.abspath(BASE_DIR)

# Server details
HOST = "127.0.0.1"
PORT = 8000

# Security Configurations
ALLOWED_PATHS = [
    WORKSPACE_DIR,
]
ALLOWED_EXTENSIONS = {".txt", ".md", ".json", ".py", ".html", ".css", ".js"}

# Simulation settings
MOCK_LLM = True  # True to run locally without external LLM API key requirements
MOCK_API_KEY = os.environ.get("GOOGLE_API_KEY", "mock-crown-ai-key-12345")
