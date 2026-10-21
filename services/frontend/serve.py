from __future__ import annotations

import argparse
import http.server
import socketserver
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


class StaticHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)


def run_server(port: int = 8501):
    print(f"Запуск веб-сервера HRCVHelper Frontend на http://localhost:{port}...")
    print(f"Статические файлы: {STATIC_DIR}")
    with socketserver.TCPServer(("", port), StaticHandler) as httpd:
        print(f"Сервер слушает на http://0.0.0.0:{port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nОстановка сервера.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HRCVHelper Frontend Web Runner")
    parser.add_argument("--port", type=int, default=8501, help="Порт для веб-сервера (по умолчанию 8501)")
    args = parser.parse_args()
    run_server(args.port)
