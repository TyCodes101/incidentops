"""Copy only built frontend assets to the platform's public directory."""

import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[1]
shutil.copytree(root / "frontend" / "dist", root / "public", dirs_exist_ok=True)
