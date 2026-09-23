"""Build the Azure App Service ZIP package: FastAPI backend + Vite frontend on one origin.

Usage (from the repository root):  python azure/build_package.py
Output: build/azure/ (unpacked, used by the local E2E test) and build/dane-bu-azure.zip.
"""

import os
import shutil
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
OUT = ROOT / "build" / "azure"
ZIP = ROOT / "build" / "dane-bu-azure.zip"
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "*.db")


def run(*command: str, env_api: str | None = None) -> None:
    env = dict(os.environ)
    if env_api is not None:
        env["VITE_API_URL"] = env_api
    # shell=True lets Windows resolve npm.cmd / npx.cmd.
    subprocess.run(" ".join(command), cwd=FRONTEND, env=env, shell=True, check=True)


def requirements() -> str:
    # Oryx would use Poetry for a bare pyproject.toml; requirements.txt keeps plain pip.
    project = tomllib.loads((BACKEND / "pyproject.toml").read_text(encoding="utf-8"))
    return "\n".join(project["project"]["dependencies"]) + "\n"


def main() -> None:
    run("npm", "ci", "--no-audit", "--no-fund")
    run("npx", "tsc", "--noEmit", "-p", ".")
    run("npx", "vite", "build", env_api="/api")

    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir(parents=True)
    shutil.copytree(BACKEND / "app", OUT / "app", ignore=IGNORE)
    shutil.copytree(BACKEND / "alembic", OUT / "alembic", ignore=IGNORE)
    shutil.copy2(BACKEND / "alembic.ini", OUT / "alembic.ini")
    shutil.copy2(BACKEND / "azure_app.py", OUT / "azure_app.py")
    (OUT / "docs").mkdir()
    shutil.copy2(ROOT / "docs" / "tax-rules.json", OUT / "docs" / "tax-rules.json")
    shutil.copytree(FRONTEND / "dist", OUT / "static")
    (OUT / "requirements.txt").write_text(requirements(), encoding="utf-8", newline="\n")
    # A CRLF checkout would break /bin/sh on Linux.
    startup = (ROOT / "azure" / "startup.sh").read_text(encoding="utf-8").replace("\r\n", "\n")
    (OUT / "startup.sh").write_text(startup, encoding="utf-8", newline="\n")

    ZIP.unlink(missing_ok=True)
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(OUT.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(OUT).as_posix())
    print(f"Package: {ZIP} ({ZIP.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    sys.exit(main())
