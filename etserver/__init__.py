import os
from pathlib import Path

from sanic.log import logger


CACHEDIR = Path(
    os.getenv("ETELEMETRY_CACHE") or Path.home() / '.etcache'
)
CACHEDIR.mkdir(parents=True, exist_ok=True)

GITHUB_API_URL = 'https://api.github.com/repos/{}/releases/latest'
