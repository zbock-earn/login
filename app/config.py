from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
TMP_DIR = STORAGE_DIR / "tmp"
OUTPUT_DIR = STORAGE_DIR / "out"
MAX_CONTENT_LENGTH = 500 * 1024 * 1024
RETENTION_TTL_SECONDS = 300

for directory in (STORAGE_DIR, TMP_DIR, OUTPUT_DIR):
    directory.mkdir(parents=True, exist_ok=True)
