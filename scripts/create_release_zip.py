"""Create clean suvnazorat-final.zip release archive."""
import os
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_ZIP_PROJECT = ROOT_DIR / "suvnazorat-final.zip"
OUTPUT_ZIP_DESKTOP = ROOT_DIR.parent / "suvnazorat-final.zip"

EXCLUDE_DIRS = {
    ".venv",
    "venv",
    "node_modules",
    ".next",
    "__pycache__",
    ".pytest_cache",
    ".git",
    ".idea",
    ".vscode",
    "build",
    "dist",
    "tmp",
}

EXCLUDE_FILES = {
    ".env",
    ".env.local",
    "suvnazorat-full.zip",
    "suvnazorat-final.zip",
    "tsconfig.tsbuildinfo",
}

EXCLUDE_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".log",
}

def should_exclude(rel_path: Path) -> bool:
    parts = rel_path.parts
    for part in parts:
        if part in EXCLUDE_DIRS:
            return True
    filename = rel_path.name
    if filename in EXCLUDE_FILES:
        return True
    return rel_path.suffix in EXCLUDE_EXTENSIONS

def make_zip(dest_path: Path):
    print(f"Creating zip archive at: {dest_path}")
    count = 0
    with zipfile.ZipFile(dest_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(ROOT_DIR):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for file in sorted(files):
                full_path = Path(root) / file
                rel_path = full_path.relative_to(ROOT_DIR)
                if should_exclude(rel_path):
                    continue
                # Archive name rooted with "suvnazorat/"
                archive_name = Path("suvnazorat") / rel_path
                zf.write(full_path, archive_name.as_posix())
                count += 1
    size_mb = dest_path.stat().st_size / (1024 * 1024)
    print(f"Archive created: {count} files packaged ({size_mb:.2f} MB).")

def verify_zip(zip_path: Path):
    print(f"Verifying zip archive: {zip_path}")
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        print(f"Total entries in zip: {len(names)}")
        # Check critical files
        must_have = [
            "suvnazorat/docker-compose.yml",
            "suvnazorat/README.md",
            "suvnazorat/.env.example",
            "suvnazorat/docs/AUDIT_REPORT.md",
            "suvnazorat/docs/STATUS.md",
            "suvnazorat/apps/backend/pyproject.toml",
            "suvnazorat/apps/backend/app/main.py",
            "suvnazorat/apps/backend/tests/test_full_e2e_flow.py",
            "suvnazorat/apps/bot/main.py",
            "suvnazorat/apps/bot/pyproject.toml",
            "suvnazorat/apps/frontend/package.json",
            "suvnazorat/apps/frontend/app/dashboard/page.tsx",
            "suvnazorat/infrastructure/docker/backend.Dockerfile",
        ]
        for item in must_have:
            assert item in names, f"Missing critical file in zip: {item}"
        
        # Check excluded secrets
        for name in names:
            assert not name.endswith("/.env"), f"Secret file found in zip: {name}"
            assert not name.endswith("/.env.local"), f"Secret file found in zip: {name}"
            assert "node_modules" not in name, f"node_modules found in zip: {name}"
            assert ".venv" not in name, f".venv found in zip: {name}"

        print("Verification PASSED! All critical files present, zero secrets or heavy caches found.")

if __name__ == "__main__":
    make_zip(OUTPUT_ZIP_PROJECT)
    verify_zip(OUTPUT_ZIP_PROJECT)
    # Also write/copy to Desktop
    import shutil
    shutil.copy2(OUTPUT_ZIP_PROJECT, OUTPUT_ZIP_DESKTOP)
    print(f"Copied to Desktop at: {OUTPUT_ZIP_DESKTOP}")
