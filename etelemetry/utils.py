"""Utility functions"""
import datetime
import json
import aiofiles

from . import CACHEDIR

timefmt = "%Y-%m-%d'T'%H:%M:%SZ"

def get_current_time():
    """Return local time as UTC time string"""
    cur_time = datetime.datetime.now(datetime.timezone.utc)
    return cur_time.strftime(timefmt)

def utc_timediff(t1, t2):
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

async def is_cached(owner, repo, stale_time=3600):
    """
    Search for project cache - if found and valid, return it.

    :param project: Github project in the form of "owner/repo"
    :param stale_time: limit until cached results are stale (secs)
    """
    cached = CACHEDIR / "{}.{}.json".format(owner, repo)
    if not cached.exists():
        return False
    async with aiofiles.open(str(cached), mode='r') as fp:
        info = await json.load(fp)
    lastmod = info.get("last_update")
    if not lastmod or (utc_timediff(lastmod, get_current_time()) > stale_time):
        return False
    return info.get("version")

async def write_cache(owner, repo, version):
    """
    Write to cache file

    TODO: consider moving towards relational DB
    """
    cached = CACHEDIR / "{}.{}.json".format(owner, repo)
    async with aiofiles.open(cached, 'w') as fp:
        await json.dump({'version': version,
                         'last_update': get_current_time()},
                        fp)
    return True
