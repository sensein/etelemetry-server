import os
from pathlib import Path

CACHEDIR = Path(os.environ.get("ETELEMETRY_CACHE") or (Path.home() / '.etcache'))
CACHEDIR.mkdir(parents=True, exist_ok=True)

GITHUB_API_URL = 'https://api.github.com/repos/{}/releases/latest'
