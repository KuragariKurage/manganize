"""Jinja2 templates configuration"""

from pathlib import Path

from fastapi.templating import Jinja2Templates

# Templates directory
templates_dir = Path(__file__).parent / "templates"

# Jinja2 templates instance
templates = Jinja2Templates(directory=templates_dir)
