"""
Helper module to fix import paths for tests.
This adds the correct paths to sys.path so that imports like 'from src.xyz' work correctly.
"""

import os
import sys
from pathlib import Path

# Add the flask-service directory to path so that 'src' is a top-level module
flask_service_dir = Path(__file__).parent.parent.absolute()
if str(flask_service_dir) not in sys.path:
    sys.path.insert(0, str(flask_service_dir))

# Add the project root directory to path so that 'meeting_shared' is a top-level module
project_root_dir = flask_service_dir.parent.parent.absolute()
if str(project_root_dir) not in sys.path:
    sys.path.insert(0, str(project_root_dir)) 