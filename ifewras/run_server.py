"""Server launcher for IFEWRAS System.
Run: python run_server.py
Access dashboard: http://127.0.0.1:8000
API Docs: http://127.0.0.1:8000/docs
"""
import sys
import os
import uvicorn

# Add backend directory to python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if __name__ == "__main__":
    print("=" * 70)
    print("  IFEWRAS: Integrated Flood Early Warning + Rescue Allocation System")
    print("  Smart India Hackathon 2026 | Assam Disaster Management (ASDMA/SDRF)")
    print("=" * 70)
    print("  * Dashboard URL : http://127.0.0.1:8000")
    print("  * API Docs      : http://127.0.0.1:8000/docs")
    print("=" * 70)
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
