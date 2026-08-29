"""IFEWRAS Test Suite Package.
"""
import sys
import os

# Add backend directory to sys.path for test discovery
backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
