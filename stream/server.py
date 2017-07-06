import logging
import datetime

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


def project_track(track):
    return {
        "title": track.title,
        "artist": track.artist,
        "album": track.album,
        "length": track.length,
    }


def project_scheduled_track(scheduled_track):
    return {
        "start_time": scheduled_track.start_time.isoformat(" "),
        "end_time": scheduled_track.end_time.isoformat(" "),
        "track": project_track(scheduled_track.track),
    }


def project_playlist(playlist, host):
    return {
        "id": playlist.id,
        "name": playlist.name,
        "scheduled": [project_scheduled_track(st) for st in playlist.upcoming_schedule(datetime.datetime.utcnow())],
        "url": "//{}/playlists/{}".format(host, playlist.id)
    }


async def handle_playlists(request):
    host = request.headers["Host"]
    cursor = Session.query(Playlist).order_by(Playlist.name)
    playlists = [project_playlist(pl, host) for pl in cursor]
    return ok(playlists=playlists)


async def handle_playlist(request):
    playlist_id = request.match_info["playlist_id"]
    playlist = Session.query(Playlist).filter_by(id=playlist_id).first()
    renderer = M3U8Renderer("http://localhost:8080")
    filename = playlist.name + ".m3u8"
    headers = {
        "Content-Type": MPEGURL_MIME,
        "Content-Disposition": "inline; filename=\"{}\"".format(filename),
    }
    return web.Response(body=renderer.render(playlist, datetime.datetime.utcnow()).encode("utf-8"), headers=headers)


async def handle_segment(request):
    digest = request.match_info["digest"]
    segment_num = int(request.match_info["num"])
    track = Session.query(Track).filter_by(digest=digest).one()
    segment_path = Cache().get_segment_path(track, segment_num)
    return web.FileResponse(segment_path)


def cors_headers():
    headers = {
        "Access-Control-Allow-Origin": "*"
    }
    return headers


async def handle_preflight(request):
    return web.Response()


async def cors_middleware(app, handler):
    async def middleware_handler(request):

        if request.method == "OPTIONS":
            response = await handle_preflight(request)
        else:
            response = await handler(request)
        response.headers.update(cors_headers())
        return response
    return middleware_handler


def create_server():
    app = web.Application(middlewares=[cors_middleware])
    app.router.add_get("/", handle_request)
    app.router.add_get("/playlists", handle_playlists)
    app.router.add_get("/playlists/{playlist_id}", handle_playlist)
    app.router.add_get("/segments/{digest}/{num}", handle_segment)
    return app
