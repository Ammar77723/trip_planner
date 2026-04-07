"""Start the MCP server"""
import uvicorn
from mcp_server.server import app

if __name__ == "__main__":
    print("=" * 50)
    print("Starting MCP Server")
    print("=" * 50)
    print("Server URL: http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/health")
    print("=" * 50)
    print("\nPress Ctrl+C to stop the server\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

