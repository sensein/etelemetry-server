import os

from . import GITHUB_RELEASE_URL, GITHUB_TAG_URL, IPSTACK_URL, logger
from .utils import query_project_cache, write_project_cache


async def fetch_response(app, url, params=None):
    async with app.sem, app.session.get(url, params=params) as response:
        try:
            resp = await response.json()
        except ValueError:
            resp = await response.text()
        status = response.status
    return status, resp


async def fetch_project(app, owner, repo):
    """
    Reuse cached information or query GitHub API for project information.

    1) If no cache is found, query GitHub API and write to cache
    2) If cache is found but query time is insufficient, query and regenerate
    3) Otherwise, use cached version

    Parameters
    ----------
    app : Sanic
        server app
    owner : str
        GitHub user or organization
    repo : str
        GitHub repository

    Returns
    -------
    project_info : dict
        Composed of `version`, `cached`, `status`, and `notes` fields
    """
    # TODO: developer notes from .etelemetry file in repo
    # https://api.github.com/repos/<project>/contents/.etelemetry.yml
    # base64 encoding
    project_info = await query_project_cache(owner, repo)
    if project_info is None:
        # unable to reuse cache
        project_info = await fetch_project_version(app, owner, repo)
        project_info["cached"] = False
    else:
        project_info["cached"] = True
    return project_info


async def fetch_project_version(app, owner, repo):
    """
    Query GitHub API and write to cache

    Parameters
    ----------
    app : Sanic
        server app
    owner : str
        GitHub user or organization
    repo : str
        GitHub repository

    Returns
    -------
    status_code : int
        Status code of response
    project_info : dict
        Composed of required 'version' field with additional optional fields
    """
    project_info = {}

    status_code, resp = await fetch_response(
        app, GITHUB_RELEASE_URL.format(owner=owner, repo=repo)
    )
    # check for tag if no release is found
    if status_code == 404:
        logger.info(f"No release found for {owner}/{repo}, checking tags...")
        status, resp = await fetch_response(
            app, GITHUB_TAG_URL.format(owner=owner, repo=repo)
        )
        try:
            resp = resp[0]  # latest tag
        except (KeyError, IndexError):
            # invalid JSON
            resp = {}

    version = (resp.get("tag_name") or resp.get("name", "Unknown")).lstrip("v")
    project_info["version"] = version
    project_info["status"] = status_code
    # TODO: query .etelemetry.json to add additional fields to project_info
    if status_code == 200:
        await write_project_cache(owner, repo, project_info)
    return project_info


async def fetch_request_info(app, rip):
    """Reuse cache or query request information"""

    # check cache for rip
    cached = await app.mongo.query_geocookie(rip)
    if cached is not None:
        # already have information, nothing to do here
        return

    # if not found, send a request
    access_key = os.getenv("IPSTACK_API_KEY")
    if access_key is None:
        logger.warn("Access key is undefined")
        return

    params = {"access_key": access_key, "hostname": 1}
    status, resp = await fetch_response(app, IPSTACK_URL.format(ip=rip), params)
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

    keys = (
        "continent_name",
        "country_name",
        "region_name",
        "city",
        "hostname",
        "latitude",
        "longitude",
    )
    geoloc = {key: resp.get(key) for key, _ in resp.items() if key in keys}
    geoloc["remote_addr"] = rip
    # cache for future requests
    await app.mongo.insert_geo(rip, geoloc)
