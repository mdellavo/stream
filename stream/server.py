import os
import logging
import urllib

from aiohttp import ClientSession, web

from stream.model import Playlist
from stream.utils import TaskPool
from stream.config import NUM_DOWNLOADS, CHUNK_SIZE

log = logging.getLogger(__name__)


async def handle_request(request):
    return web.Response(text="hello")


def create_server(playlists):
    app = web.Application()
    app["playlists"] = playlists
    app.router.add_get("/", handle_request)
    return app


async def cache_item(loop, playlist, item):

    if os.path.exists(item.cache_path):
        return

    log.info("caching item %s", item.ge_turl())

    async with ClientSession(loop=loop) as session, session.get(item.get_url()) as response:
        with open(item.temp_path, "wb") as fd:
            while True:
                chunk = await response.content.read(CHUNK_SIZE)
                if not chunk:
                    break
                fd.write(chunk)

    os.rename(item.temp_path, item.cache_path)


async def load_playlist(loop, url):
    log.info("loading playlist: {}".format(url.geturl()))

    if url.scheme in ("http", "https"):
        async with ClientSession(loop=loop) as session, session.get(url.geturl()) as response:
            body = response.text()
    elif not url.scheme or url.scheme == "file":
        with open(url.path) as f:
            body = f.read()
    else:
        raise ValueError("unknown url scheme: {}".format(url.geturl()))

    playlist = Playlist(url)
    item_urls = [urllib.parse.urlparse(item_url) for item_url in body.splitlines()]
    playlist.add_items(item_urls)

    os.makedirs(playlist.cache_path, exist_ok=True)

    pool = TaskPool(loop, NUM_DOWNLOADS)
    for item in playlist.items:
        pool.submit(cache_item(loop, playlist, item))
    await pool.join()

    return playlist


async def load_playlists(loop, urls):
    playlists = [await load_playlist(loop, urllib.parse.urlparse(url)) for url in urls]
    return playlists
