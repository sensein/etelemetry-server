import asyncio
import os
import sys

import aiohttp
from sanic import Sanic, response
from sanic.exceptions import abort

from . import logger, CACHEDIR, __version__
from .database import MongoClientHelper
from .getters import fetch_project, fetch_request_info

if os.path.exists("/vagrant"):
    logdir = "/vagrant"
else:
    logdir = os.getcwd()

LOG_SETTINGS = dict(
    version=1,
    disable_existing_loggers=False,
    loggers={
        "sanic.root": {"level": "INFO", "handlers": ["consolefile"]},
        "sanic.error": {
            "level": "INFO",
            "handlers": ["error_consolefile"],
            "propagate": True,
            "qualname": "sanic.error",
        },
        "sanic.access": {
            "level": "INFO",
            "handlers": ["access_consolefile"],
            "propagate": True,
            "qualname": "sanic.access",
        },
    },
    handlers={
        "consolefile": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "when": "D",
            "interval": 7,
            "backupCount": 10,
            "filename": f"{logdir}/console.log",
            "formatter": "generic",
        },
        "error_consolefile": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "when": "D",
            "interval": 7,
            "backupCount": 10,
            "filename": f"{logdir}/error.log",
            "formatter": "generic",
        },
        "access_consolefile": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "when": "D",
            "interval": 7,
            "backupCount": 10,
            "filename": f"{logdir}/access.log",
            "formatter": "access",
        },
    },
    formatters={
        "generic": {
            "format": "%(asctime)s [%(process)d] [%(levelname)s] %(message)s",
            "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
            "class": "logging.Formatter",
        },
        "access": {
            "format": "%(asctime)s - (%(name)s)[%(levelname)s][%(host)s]: "
            + "%(request)s %(message)s %(status)d %(byte)d",
            "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
            "class": "logging.Formatter",
        },
    },
)
app = Sanic("etelemetry", log_config=LOG_SETTINGS)
if os.getenv("ETELEMETRY_APP_CONFIG"):
    app.config.from_envvar("ETELEMETRY_APP_CONFIG")


@app.listener("before_server_start")
async def init(app, loop):
    app.sem = asyncio.Semaphore(100)
    app.session = aiohttp.ClientSession(loop=loop)
    app.mongo = MongoClientHelper()
    logger.info("Using %s as project cache directory" % str(CACHEDIR))
    # ensure mongo is responsive
    await app.mongo.is_valid()


@app.listener("after_server_stop")
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
    if len(project.split("/")) != 2:
        abort(400, message="Invalid project")
    owner, repo = project.split("/")
    request_ip = request.remote_addr or request.ip
    # get information about project
    project_info = await fetch_project(app, owner, repo)
    if not project_info.get("version"):
        abort(404, "Version not found")
    if "is_ci" in request.args:
        project_info["is_ci"] = True
    await app.mongo.insert_project(request_ip, owner, repo, project_info)
    # get request information
    await fetch_request_info(app, request_ip)
    # keys exclude for response
    crud = ("status", "last_update", "cached", "stats")
    for k in crud:
        if k in project_info:
            del project_info[k]
    return response.json(project_info)


@app.route("/stats/<project:path>")
async def get_project_stats(request, project: str):
    """
    GETs project statistics from server.

    :param request: The request object
    :type request: Request
    :param project: GitHub project in the form of "owner/repo"
    :type project: str
    :return: JSON with single key, "release"
    """
    if len(project.split("/")) != 2:
        abort(400, message="Invalid project")
    owner, repo = project.split("/")
    stats = await app.mongo.get_status(owner, repo)
    return response.json(stats)


@app.route("/")
async def server_info(request):
    return response.json(
        {
            "package": "etelemetry-server",
            "version": __version__,
            "message": "ET phones home",
        }
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


if __name__ == "__main__":
    main()
