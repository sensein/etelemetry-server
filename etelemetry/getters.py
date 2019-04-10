import json
import aiofiles
import aiohttp

from . import GITHUB_API_URL, CACHEDIR
from .utils import write_cache

async def fetch_response(session, url):
    async with session.get(url) as response:
        resp = await response.json()
        status = response.status
        return status, resp

async def fetch_version(owner, repo):
    """Query GitHub API and write to cache"""
    project = "/".join([owner, repo])
    async with aiohttp.ClientSession() as session:
        status, resp = await fetch_response(session, GITHUB_API_URL.format(project))

    vtag = resp.get('tag_name')
    if vtag and vtag.startswith('v'):
        vtag = vtag[1:]
    if status == 200:
        await write_cache(owner, repo, vtag)
    return status, vtag
