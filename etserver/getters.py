from . import GITHUB_API_URL
from .utils import write_cache


async def fetch_response(app, url):
    async with app.sem, app.session.get(url) as response:
        resp = await response.json()
        status = response.status
    return status, resp


async def fetch_version(app, owner, repo):
    """Query GitHub API and write to cache"""
    project = "/".join((owner, repo))
    status, resp = await fetch_response(
        app, GITHUB_API_URL.format(project)
    )
    vtag = resp.get('tag_name')
    if not vtag:
        return status, None
    vtag = vtag.lstrip('v')
    if status == 200:
        await write_cache(owner, repo, vtag)
    return status, vtag
