from __future__ import annotations

from pathlib import Path
from .json_to_docx import generate_cv

BASE_DIR = Path(__file__).resolve().parent
DOCX_TEMPLATE_PATH = BASE_DIR / "template" / "placeholders_cv_docx.docx"
STYLE_PATH = BASE_DIR / "template" / "style.json"

__all__ = ["generate_cv", "DOCX_TEMPLATE_PATH", "STYLE_PATH"]
