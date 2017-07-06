import os
import sys
import logging
import asyncio

import uvloop
from sqlalchemy import create_engine
from aiohttp import web

from stream import server, model, audio, config, playlist
from stream.utils import periodic

log = logging.getLogger("main")


def main():
    os.makedirs(config.TMP_DIR, exist_ok=True)

    engine = create_engine(config.DB_URL)
    model.Base.metadata.create_all(engine)
    model.Session.bind = engine

    logging.basicConfig(level=logging.DEBUG)

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    loop = asyncio.get_event_loop()

    audio.spawn_workers(loop)

    urls = sys.argv[1:]
    for url in urls:
        audio.queue_url(url)

    # FIXME
    model.Playlist.find_or_create("Test Stream",
                                  description="a random stream for testing")

    scheduler = periodic(loop, config.SCHEDULER_PERIOD, playlist.schedule_all, loop)

    def shutdown(_):
        scheduler.cancel()
        audio.shutdown_workers()

    app = server.create_server()
    app.on_shutdown.append(shutdown)
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
