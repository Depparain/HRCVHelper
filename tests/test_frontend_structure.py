from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "services" / "frontend"


def test_flutter_project_structure():
    assert (FRONTEND_DIR / "pubspec.yaml").exists()
    assert (FRONTEND_DIR / "web" / "index.html").exists()
    assert (FRONTEND_DIR / "web" / "manifest.json").exists()
    assert (FRONTEND_DIR / "lib" / "main.dart").exists()
    assert (FRONTEND_DIR / "Dockerfile").exists()
    assert (FRONTEND_DIR / "nginx.conf").exists()


def test_flutter_screens_exist():
    screens_dir = FRONTEND_DIR / "lib" / "screens"
    assert (screens_dir / "login_screen.dart").exists()
    assert (screens_dir / "dashboard_screen.dart").exists()
    assert (screens_dir / "validation_screen.dart").exists()
    assert (screens_dir / "admin_screen.dart").exists()


def test_static_distribution_and_runner():
    assert (FRONTEND_DIR / "static" / "index.html").exists()
    assert (FRONTEND_DIR / "serve.py").exists()

    html_content = (FRONTEND_DIR / "static" / "index.html").read_text(encoding="utf-8")
    assert "HRCVHelper" in html_content
    assert "Human-in-the-Loop" in html_content
    assert "/api/v1/cv/upload" in html_content
    assert "/api/v1/auth/login" in html_content
