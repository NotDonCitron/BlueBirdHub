"""
Vercel serverless function entry point for OrdnungsHub
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set environment variable for cloud deployment
os.environ['VERCEL'] = 'true'

from src.backend.main import app

# Vercel expects the app to be available as 'app'
# No need to do anything else - Vercel handles the rest!