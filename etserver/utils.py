"""Utility functions"""
import datetime
import json
import aiofiles

from . import CACHEDIR, logger

timefmt = "%Y-%m-%d'T'%H:%M:%SZ"


async def get_current_time():
    """Return local time as UTC time string"""
    cur_time = datetime.datetime.now(datetime.timezone.utc)
    return cur_time.strftime(timefmt)


async def utc_timediff(t1, t2):
    """
    Calculate the absolute difference between two UTC time strings

    Parameters
    ----------
    t1, t2 : str

    """
    time1 = datetime.datetime.strptime(t1, timefmt)
    time2 = datetime.datetime.strptime(t2, timefmt)
    timedelt = time1 - time2
    return abs(timedelt.total_seconds())


async def query_project_cache(owner, repo, stale_time=21600):
    """
    Search for project cache - if found and valid, return it.

    :param project: Github project in the form of "owner/repo"
    :param stale_time: limit until cached results are stale (secs)
    """
    cache = CACHEDIR / "{}--{}.json".format(owner, repo)
    if not cache.exists():
        return None, "no cache"

    async with aiofiles.open(str(cache)) as fp:
        project_info = json.loads(await fp.read())

    lastmod = project_info.get("last_update")
    if (
        lastmod is None
        or await utc_timediff(lastmod, await get_current_time()) > stale_time
    ):
        return project_info, "stale"
    logger.info(f"Reusing {owner}/{repo} cached version.")
    return project_info, "cached"


async def write_project_cache(owner, repo, project_info, update=True):
    """
    Write project information to cached file
    """
    cache = CACHEDIR / "{}--{}.json".format(owner, repo)
    if update:
        project_info["last_update"] = await get_current_time()
    async with aiofiles.open(str(cache), "w") as fp:
        await fp.write(json.dumps(project_info))
