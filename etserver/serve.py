import asyncio
import os

import aiohttp
from sanic import Sanic, response
from sanic.exceptions import abort

from . import logger, CACHEDIR, __version__
from .database import MongoClientHelper
from .getters import fetch_project, fetch_request_info

app = Sanic('etelemetry')
if os.getenv("ETELEMETRY_APP_CONFIG"):
    app.config.from_envvar("ETELEMETRY_APP_CONFIG")


@app.listener('before_server_start')
async def init(app, loop):
    app.sem = asyncio.Semaphore(100, loop=loop)
    app.session = aiohttp.ClientSession(loop=loop)
    app.mongo = MongoClientHelper()
    logger.info("Using %s as project cache directory" % str(CACHEDIR))
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
    request_ip = request.remote_addr or request.ip
    # get information about project
    project_info = await fetch_project(app, owner, repo)
    if not project_info.get('version'):
        abort(404, "Version not found")
    await app.mongo.insert_project(
        request_ip, owner, repo, project_info
    )
    # get request information
    await fetch_request_info(app, request_ip)
    # keys exclude for response
    crud = ('status', 'last_update', 'cached')
    for k in crud:
        if k in project_info:
            del project_info[k]
    return response.json(project_info)


@app.route("/")
async def server_info(request):
    return response.json(
        {"package": "etelemetry-server",
         "version": __version__,
         "message": "ET phones home"}
    )


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
