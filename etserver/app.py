import asyncio
import os

import aiohttp
from sanic import Sanic, response
from sanic.exceptions import abort

from . import logger, CACHEDIR
from .database import MongoClientHelper
from .getters import fetch_project, fetch_geoloc
# from .utils import query_project_cache

app = Sanic('etelemetry')
if os.getenv("ETELEMETRY_APP_CONFIG"):
    app.config.from_envvar("ETELEMETRY_APP_CONFIG")


@app.listener('before_server_start')
async def init(app, loop):
    app.sem = asyncio.Semaphore(100, loop=loop)
    app.session = aiohttp.ClientSession(loop=loop)
    app.mongo = MongoClientHelper()
    logger.info("Using %s as cache directory" % str(CACHEDIR))
    # ensure mongo is responsive
    await app.mongo.is_valid()


@app.listener('after_server_stop')
async def finish(app, loop):
    await app.session.close()


@app.route("/projects/<project:path>")
async def get_project_info(request, project: str):
    """
    GETs GitHub project information.

    :param request: The request object
    :type request: Request
    :param project: GitHub project in the form of "owner/repo"
    :type project: str
    :return: JSON with single key, "release"
    """
    if len(project.split('/')) != 2:
        abort(400, message="Invalid project")
    owner, repo = project.split('/')

    # fetch_project_info
    project_info = await fetch_project(app, owner, repo)

    rip = request.remote_addr or request.ip
    # fetch_geoloc
    geoloc = await fetch_geoloc(app, rip)
    await app.mongo.db_insert(
        rip, owner, repo, version, cached, status
    )
    if not version:
        abort(404, "Version not found")

    # TODO: developer notes from .etelemetry file in repo
    # https://api.github.com/repos/<project>/contents/.etelemetry.yml
    # base64 encoding
    return response.json({"version": version})


@app.route("/")
async def test(request):
    return response.json({"hello": "world"})


def get_parser():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("command", choices=("up",), help="action")
    parser.add_argument("--host", default="0.0.0.0", help="hostname")
    parser.add_argument("--port", default=8000, help="server port")
    parser.add_argument("--workers", default=1, help="worker processes")
    return parser


def main(argv=None):
    parser = get_parser()
    pargs = parser.parse_args(argv)
    app.run(**vars(pargs))


if __name__ == '__main__':
    main()
