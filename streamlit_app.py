"""Root Streamlit deployment entrypoint for Streamlit Community Cloud.

When configuring Streamlit Cloud:
- Option A (Recommended): Set 'Main file path' to 'src/dashboard/app.py'
- Option B: Set 'Main file path' to 'streamlit_app.py'
"""
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import runpy
runpy.run_path(str(ROOT_DIR / "src" / "dashboard" / "app.py"), run_name="__main__")
