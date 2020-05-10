import os

from . import GITHUB_RELEASE_URL, GITHUB_TAG_URL, GITHUB_ET_FILE, IPSTACK_URL, logger
from .utils import (
    query_project_cache,
    write_project_cache,
    get_current_time,
    utc_timediff,
)


async def fetch_response(app, url, params=None, content_type="application/json"):
    async with app.sem, app.session.get(url, params=params) as response:
        try:
            resp = await response.json(content_type=content_type)
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
    project_info, state = await query_project_cache(owner, repo)
    if project_info is None or state == "stale":
        # unable to reuse cache
        project_info = await fetch_project_version(app, owner, repo, project_info)
        project_info["cached"] = False
    else:
        project_info["cached"] = True
    return project_info


async def fetch_project_version(app, owner, repo, project_info=None):
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
    project_info = project_info or {}

    status_code, resp = await fetch_response(
        app, GITHUB_RELEASE_URL.format(owner=owner, repo=repo)
    )
    logger.info(f"RELEASEURL: {owner}/{repo}/{status_code}")
    # check for tag if no release is found
    if status_code == 403:
        return project_info

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
        logger.info(f"TAGURL: {owner}/{repo}/{status}{resp}")
        if status == 404 or status == 403:
            return project_info

    version = (resp.get("tag_name") or resp.get("name", "Unknown")).lstrip("v")
    project_info["version"] = version
    project_info["status"] = status_code

    if status_code == 200:
        status, resp = await fetch_response(
            app, GITHUB_ET_FILE.format(owner=owner, repo=repo), content_type=None
        )
        if status == 200:
            project_info["bad_versions"] = resp.get("bad_versions", None)
        else:
            logger.info(f"et file status code: {status} for {owner}/{repo}")
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


async def get_stats(app, owner, repo):
    project_info = await fetch_project(app, owner, repo)
    logger.info(project_info)
    if "version" not in project_info:
        return None
    lastmod = project_info.get("stats_update")
    now = await get_current_time()
    stale_stats = lastmod is None or await utc_timediff(lastmod, now) > 21600
    if not project_info["cached"] or "stats" not in project_info or stale_stats:
        stats = await app.mongo.get_status(owner, repo, project_info)
        project_info["stats"] = stats
        del project_info["cached"]
        project_info["stats_update"] = now
        await write_project_cache(owner, repo, project_info, update=False)
    return project_info["stats"]
