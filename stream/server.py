import logging

from aiohttp import web

log = logging.getLogger(__name__)


async def handle_request(request):
    return web.Response(text="hello")


def create_server(playlist):
    app = web.Application()
    app["playlist"] = playlist
    app.router.add_get("/", handle_request)
    return app
