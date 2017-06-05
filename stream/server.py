import logging

from aiohttp import web

from stream.audio import MPEGURL_MIME
from stream.model import Session, Playlist, Track
from stream.render import M3U8Renderer
from stream.cache import Cache

log = logging.getLogger(__name__)


def resp(status, **kwargs):
    rv = {"status": status}
    rv.update(kwargs)
    return web.json_response(rv)


def ok(**kwargs):
    return resp("ok", **kwargs)


def error(**kwargs):
    return resp("error", **kwargs)


async def handle_request(request):
    return ok()


async def handle_playlists(request):
    cursor = Session.query(Playlist).order_by(Playlist.name)
    playlists = [{"id": pl.id, "name": pl.name} for pl in cursor]
    return ok(playlists=playlists)


async def handle_playlist(request):
    playlist_id = request.match_info["playlist_id"]
    playlist = Session.query(Playlist).filter_by(id=playlist_id).first()
    renderer = M3U8Renderer(playlist, "http://localhost:8080")
    filename = playlist.name + ".m3u8"
    headers = {
        "Content-Type": MPEGURL_MIME,
        "Content-Disposition": "inline; filename=\"{}\"".format(filename),
    }
    return web.Response(body=renderer.render().encode("utf-8"), headers=headers)


async def handle_segment(request):
    digest = request.match_info["digest"]
    segment_num = int(request.match_info["num"])
    track = Session.query(Track).filter_by(digest=digest).one()
    segment_path = Cache().get_segment_path(track, segment_num)
    return web.FileResponse(segment_path)


def create_server():
    app = web.Application()
    app.router.add_get("/", handle_request)
    app.router.add_get("/playlists", handle_playlists)
    app.router.add_get("/playlists/{playlist_id}", handle_playlist)
    app.router.add_get("/segments/{digest}/{num}", handle_segment)
    return app
