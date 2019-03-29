import requests
import json
import sys

from sanic import Sanic
from sanic import response
from sanic.exceptions import abort

app = Sanic()

PROJECT_API_URLS = {
    'heudiconv': 'https://api.github.com/repos/nipy/heudiconv/releases/latest',
}

@app.route("api/v1/projects/<project>")
async def get_version(request, project: str):
    """
    Query latest release of project and return JSON.
    :param request: The request object
    :type request: Request
    :param project: Project key
    :type project: str
    :return: JSON with single key, "release"
    """
    if project not in PROJECT_API_URLS:
        abort(404)
    resp = requests.get(PROJECT_API_URLS[project])
    if resp.status_code != 200:
        abort(resp.status_code)  # something went wrong, raise the error
    tag = json.loads(resp.content)['tag_name']
    if tag.startswith('v'):
        tag = tag[1:]
    # TODO: add any release specific warnings to response?
    return response.json({"release": tag})

def get_parser():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("command", choices=("up",), help="command")
    parser.add_argument("--host", default="0.0.0.0", help="hostname")
    parser.add_argument("--port", default=8000, help="port")
    return parser

def main(argv=None):
    parser = get_parser()
    args = parser.parse_args(argv)
    app.run(host=args.host, port=args.port)


if __name__ == '__main__':
    main()
