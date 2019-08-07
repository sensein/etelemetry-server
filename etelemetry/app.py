import aiohttp
from sanic import Sanic
from sanic import response
from sanic.exceptions import abort

from .backend import MongoClientHelper
from .utils import is_cached
from .getters import fetch_version

app = Sanic('etelemetry')


@app.listener('before_server_start')
def init(app, loop):
    app.session = aiohttp.ClientSession(loop=loop)


@app.listener('after_server_stop')
def finish(app, loop):
    loop.run_until_complete(app.session.close())
    loop.close()


@app.route("/projects/<project:path>")
async def et_request(request, project: str):
    """
    Check project for latest published release

    1) If no cache is found, query GitHub API and write to cache
    2) If cache is found but query time is insufficient, query and regenerate
    3) If cache is found and query time is acceptable, use cached version

    :param request: The request object
    :type request: Request
    :param project: Github project in the form of "owner/repo"
    :type project: str
    :return: JSON with single key, "release"
    """
    if '/' not in project:
        abort(400)  # return response.text("Bad response")
    owner, repo = project.split('/', 1)
    cached = True
    status = None
    version = await is_cached(owner, repo)
    if not version:
        cached = False
        status, version = await fetch_version(app.session, owner, repo)
    await MongoClientHelper().db_insert(
        request.ip, owner, repo, version, cached, status
    )
    if not version:
        abort(404)
    return response.json({"version": version})


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
