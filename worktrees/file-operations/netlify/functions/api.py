"""
Netlify function entry point for OrdnungsHub
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set environment variable for cloud deployment
os.environ['NETLIFY'] = 'true'

from src.backend.main import app
from mangum import Mangum

# Create the Mangum adapter for Netlify Functions
handler = Mangum(app, lifespan="off")