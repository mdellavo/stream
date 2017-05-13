import sys
import logging
import asyncio

import uvloop
from sqlalchemy import create_engine
from aiohttp import web

from stream import server, model, audio, config, playlist

log = logging.getLogger("main")


def main():
    engine = create_engine('sqlite:///stream.sqlite')
    model.Base.metadata.create_all(engine)
    model.Session.bind = engine

    logging.basicConfig(level=logging.DEBUG)

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    loop = asyncio.get_event_loop()

    urls = sys.argv[1:]
    loop.run_until_complete(audio.load_playlists(loop, urls))

    pl = model.Playlist.find_or_create(config.PLAYLIST_NAME)

    asyncio.ensure_future(playlist.schedule(pl))

    app = server.create_server()
    web.run_app(app, loop=loop)

    return 0


# noinspection PyBroadException
try:
    rv = main()
except KeyboardInterrupt:
    rv = 0
except:
    log.exception("error")
    rv = 1

sys.exit(rv)
