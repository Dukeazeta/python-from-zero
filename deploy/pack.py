"""Bundle the course for the server: deploy/out/python-from-zero.tar.gz plus install.sh.

Only what the website needs goes in. Never your .env, the database, your old progress
file, practice code or teaching notes.
    python deploy/pack.py
Then upload both files in deploy/out/ to the server (README.md, "Put it online").
"""

import shutil
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "deploy" / "out"
FILES = ["index.html", "privacy.html", "terms.html", "favicon.ico",
         "app/data/curriculum.json", "app/data/quizbank.json"]
FOLDERS = ["assets", "lessons", "reference"]


def wanted():
    for name in FILES:
        yield ROOT / name
    for path in sorted((ROOT / "app").glob("*.py")):
        yield path
    for folder in FOLDERS:
        for path in sorted((ROOT / folder).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                yield path


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    archive = OUT / "python-from-zero.tar.gz"
    count = 0
    with tarfile.open(archive, "w:gz") as tar:
        for path in wanted():
            if not path.is_file():
                raise SystemExit(f"Missing: {path.relative_to(ROOT)}. Run python tools/build.py first.")
            tar.add(path, arcname=path.relative_to(ROOT).as_posix())
            count += 1
    shutil.copyfile(ROOT / "deploy" / "install.sh", OUT / "install.sh")
    print(f"Packed {count} files into {archive.relative_to(ROOT)} ({archive.stat().st_size // 1024} KB).")
    print("Upload deploy/out/python-from-zero.tar.gz and deploy/out/install.sh to the server.")


if __name__ == "__main__":
    main()
