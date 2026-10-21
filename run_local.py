"""
Скрипт для одновременного локального запуска всех микросервисов HRCVHelper и веб-интерфейса.
Не требует Docker — запускается напрямую через Python (.venv).
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

# Безопасная настройка кодировки вывода для Windows консоли
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent

SERVICES = [
    {
        "name": "DBConnector",
        "cmd": [sys.executable, "-m", "uvicorn", "services.db_connector.app.main:app", "--host", "127.0.0.1", "--port", "8005", "--log-level", "warning"],
        "port": 8005,
    },
    {
        "name": "AuthSystem",
        "cmd": [sys.executable, "-m", "uvicorn", "services.auth_system.app.main:app", "--host", "127.0.0.1", "--port", "8001", "--log-level", "warning"],
        "port": 8001,
    },
    {
        "name": "MDConvertor",
        "cmd": [sys.executable, "-m", "uvicorn", "services.md_convertor.app.main:app", "--host", "127.0.0.1", "--port", "8002", "--log-level", "warning"],
        "port": 8002,
    },
    {
        "name": "LLMConvertor",
        "cmd": [sys.executable, "-m", "uvicorn", "services.llm_convertor.app.main:app", "--host", "127.0.0.1", "--port", "8003", "--log-level", "warning"],
        "port": 8003,
    },
    {
        "name": "JSONToWord",
        "cmd": [sys.executable, "-m", "uvicorn", "services.json_to_word.app.main:app", "--host", "127.0.0.1", "--port", "8004", "--log-level", "warning"],
        "port": 8004,
    },
    {
        "name": "APIGateway",
        "cmd": [sys.executable, "-m", "uvicorn", "services.api_gateway.app.main:app", "--host", "127.0.0.1", "--port", "8000", "--log-level", "info"],
        "port": 8000,
    },
    {
        "name": "Frontend",
        "cmd": [sys.executable, "services/frontend/serve.py", "--port", "8501"],
        "port": 8501,
    },
]


def main():
    print("=" * 70)
    print(" [*] Starting HRCVHelper (Native Local Mode without Docker)")
    print("=" * 70)

    # Устанавливаем переменные окружения
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BASE_DIR)
    env["DATABASE_URL"] = os.getenv("DATABASE_URL", "sqlite:///./hrcvhelper.db")
    env["AUTH_SYSTEM_URL"] = "http://127.0.0.1:8001"
    env["MD_CONVERTOR_URL"] = "http://127.0.0.1:8002"
    env["LLM_CONVERTOR_URL"] = "http://127.0.0.1:8003"
    env["JSON_TO_WORD_URL"] = "http://127.0.0.1:8004"
    env["DB_CONNECTOR_URL"] = "http://127.0.0.1:8005"
    env["OLLAMA_MODEL"] = os.getenv("OLLAMA_MODEL", "qwen3:4b")
    env["PYTHONIOENCODING"] = "utf-8"

    processes: list[subprocess.Popen] = []

    try:
        for s in SERVICES:
            print(f" [+] Launching {s['name']} on port {s['port']}...")
            p = subprocess.Popen(
                s["cmd"],
                env=env,
                cwd=str(BASE_DIR),
            )
            processes.append(p)
            time.sleep(0.4)

        print("\n" + "=" * 70)
        print(" [OK] All HRCVHelper services are running successfully!")
        print(" [>] Frontend Web UI:        http://localhost:8501")
        print(" [>] API Gateway Swagger UI:  http://localhost:8000/docs")
        print(" [>] Demo account:            hr_admin / hrpassword123")
        print("=" * 70)
        print(" Press Ctrl + C to stop all services\n")

        while True:
            time.sleep(1)
            for p in processes:
                if p.poll() is not None:
                    print(f"Service pid {p.pid} exited with code {p.returncode}")

    except KeyboardInterrupt:
        print("\nStopping all services...")
    finally:
        for p in processes:
            try:
                p.terminate()
                p.wait(timeout=2)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass
        print("All services stopped.")


if __name__ == "__main__":
    main()
