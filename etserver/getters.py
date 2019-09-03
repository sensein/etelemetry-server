from . import GITHUB_RELEASE_URL, GITHUB_TAG_URL, logger
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
        app, GITHUB_RELEASE_URL.format(project)
    )
    # check for tag if no release is found
    if status == 404:
        logger.info(f"No release found for {project}, checking tags...")
        status, resp = await fetch_response(
            app, GITHUB_TAG_URL.format(project)
        )
        try:
            resp = resp[0]  # latest tag
        except (KeyError, IndexError):
            resp = {}

    vtag = resp.get('tag_name') or resp.get('name')
    if not vtag:
        return status, None
    vtag = vtag.lstrip('v')
    if status == 200:
        await write_cache(owner, repo, vtag)
    return status, vtag
