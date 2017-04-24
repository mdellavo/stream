import sys
import logging
import asyncio

from aiohttp import web

from stream import server, render

log = logging.getLogger("main")


def main():
    logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    urls = sys.argv[1:]
    playlists = loop.run_until_complete(server.load_playlists(loop, urls))
    app = server.create_server(playlists)
    web.run_app(app, loop=loop)
    return 0


try:
    rv = main()
except KeyboardInterrupt:
    rv = 0
except:
    log.exception("error")
    rv = 1

sys.exit(rv)
