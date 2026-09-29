"""PostToolUse-хук: форматує змінений файл (ruff для .py, djlint для шаблонів)."""

import json
import subprocess
import sys
from pathlib import Path

payload = json.load(sys.stdin)
file_path = payload.get("tool_input", {}).get("file_path")
if not file_path:
    sys.exit(0)

path = Path(file_path)
if not path.exists() or ".venv" in path.parts:
    sys.exit(0)

if path.suffix == ".py" and "migrations" not in path.parts:
    commands = [["uv", "run", "--no-sync", "ruff", "format", "-q", str(path)]]
elif path.suffix == ".html" and "templates" in path.parts:
    commands = [["uv", "run", "--no-sync", "djlint", "--reformat", "--quiet", str(path)]]
else:
    sys.exit(0)

for command in commands:
    subprocess.run(command, check=False, capture_output=True)  # noqa: S603
