import os
from pathlib import Path

from sanic.log import logger

from ._version import get_versions

__version__ = get_versions()["version"]
del get_versions


CACHEDIR = Path(os.getenv("ETELEMETRY_CACHE") or Path.home() / ".etcache")
CACHEDIR.mkdir(parents=True, exist_ok=True)

GITHUB_RELEASE_URL = "https://api.github.com/repos/{owner}/{repo}/releases/latest"
GITHUB_TAG_URL = "https://api.github.com/repos/{owner}/{repo}/tags"
GITHUB_ET_FILE = "https://raw.githubusercontent.com/{owner}/{repo}/master/.et"
IPSTACK_URL = "http://api.ipstack.com/{ip}"
