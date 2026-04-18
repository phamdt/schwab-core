"""
pytest configuration for schwab-core tests.
"""
import sys
from pathlib import Path

# Add parent directory to path to allow importing schwab_core
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
