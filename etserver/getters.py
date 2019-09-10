import os

from . import (
    GITHUB_RELEASE_URL,
    GITHUB_TAG_URL,
    IPSTACK_URL,
    logger
)
from .utils import write_cache


async def fetch_response(app, url, params=None):
    async with app.sem, app.session.get(url, params=params) as response:
        try:
            resp = await response.json()
        except ValueError:
            resp = await response.text()
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


async def fetch_geoloc(app, rip):
    access_key = os.getenv("IPSTACK_API_KEY")
    if access_key is None:
        logger.warn("Access key is undefined")
        return

    params = {
        "access_key": access_key,
        "hostname": 1
    }
    status, resp = await fetch_response(
        app, IPSTACK_URL.format(rip), params
    )
    if status != 200:
        logger.info(f"Geoloc failed with code {resp.status}")
        return
    elif not resp.get("success", True):
        logger.info(f"Geoloc failed: {resp.get('error')}")
        return
    # ensure information is extracted
    vals = set(val for val in resp.values() if not isinstance(val, dict))
    if len(vals) <= 2:
        logger.info(f"Invalid geoloc information for {rip}")
        return
    # new valid information, so write to cache

    keys = (
        "continent_name",
        "country_name",
        "region_name",
        "city",
        "hostname",
        "latitude",
        "longitude"
    )
    geoloc = {key: resp.get(key) for key, _ in resp if key in keys}
    return geoloc
