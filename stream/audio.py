import os
import hashlib
import tempfile
import logging
import asyncio
import urllib
from asyncio.queues import Queue

from aiohttp import ClientSession
import mutagen

from stream import config
from stream.model import Session, Track, SeenUrl, TrackMetadata, MetadataKeys
from stream.cache import Cache

log = logging.getLogger(__name__)

WORK_QUEUE = None
SENTINEL = object()

MPEGURL_MIME = "audio/x-mpegurl"


async def segment_track(loop, track_path, output_path, segment_duration):
    args = [
        "/usr/bin/ffmpeg",
        "-loglevel", "-8",
        "-i", track_path,
        "-vn",
        "-acodec", "aac",
        "-b:a", config.BITRATE,
        "-map", "0",
        "-flags", "+global_header",
        "-f", "segment",
        "-segment_format", "mpeg_ts",
        "-segment_time", str(segment_duration),
        output_path,
    ]
    proc = await asyncio.create_subprocess_exec(*args, stdout=None, stdin=None, stderr=None, loop=loop)
    return await proc.wait()


ID3_KEY_MAP = {
    MetadataKeys.ARTIST: "TPE1",
    MetadataKeys.ALBUM: "TALB",
    MetadataKeys.TRACK: "TRCK",
    MetadataKeys.TITLE: "TIT2",
}


async def scrape_metadata(track, track_path):
    info = mutagen.File(track_path)
    if not info:
        return []

    metadata = {
        MetadataKeys.LENGTH: [str(info.info.length)],
        MetadataKeys.MIME: [info.mime[0]],
    }
    metadata.update({k: info.tags[v].text for k, v in ID3_KEY_MAP.items()})
    return [TrackMetadata(track=track, key=k, value=v) for k, vs in metadata.items() for v in vs]


async def load_track(loop, url, body):
    cache = Cache()

    log.info("preparing track %s", url)

    with tempfile.NamedTemporaryFile(delete=False, dir=config.TMP_DIR) as f:

        digester = hashlib.sha256()

        while True:
            chunk = await body.read(config.CHUNK_SIZE)
            if not chunk:
                break
            digester.update(chunk)
            f.write(chunk)

        f.close()

        track = Track(digest=digester.hexdigest())
        metadata = await scrape_metadata(track, f.name)
        if metadata:
            Session.add(track)
            Session.add_all(metadata)
            track.metadata_items.extend(metadata)

            tmp_path = os.path.join(config.TMP_DIR, f.name)
            os.makedirs(cache.get_cache_dir(track), exist_ok=True)
            cache_path = cache.get_cache_path(track)
            os.rename(tmp_path, cache_path)
            await segment_track(loop, cache_path, cache.get_segment_format_path(track), config.TARGET_DURATION)
            os.remove(cache_path)

    seen = SeenUrl(url=url, track=track)
    Session.add(seen)
    Session.commit()


def make_absolute(parent_url, url):
    parent_url, url = (urllib.parse.urlparse(u) for u in (parent_url, url))

    if url.scheme and url.netloc:
        rv = url
    else:
        rv = (
            parent_url.scheme,
            parent_url.netloc,
            url.path,
            url.params,
            url.query,
            url.fragment
        )

    return urllib.parse.urlunparse(rv)


async def load_playlist(url, f):
    log.info("loading playlist from %s", url)
    playlist = (await f.read()).decode("utf-8").splitlines()

    for item_url in playlist:
        if not Session.query(SeenUrl).filter_by(url=item_url).first():
            queue_url(item_url)


def queue_url(url):
    WORK_QUEUE.put_nowait(url)


async def queue_worker(loop):
    while True:
        url = await WORK_QUEUE.get()
        if url is SENTINEL:
            log.info("worker shutting down...")
            break

        log.info("loading url: %s", url)

        try:
            async with ClientSession(loop=loop) as session, session.get(url) as response:
                content_type = response.headers['Content-Type']

                if content_type == MPEGURL_MIME:
                    await load_playlist(str(response.url), response.content)
                else:
                    await load_track(loop, str(response.url), response.content)
        except Exception as e:
            log.exception("worker raised exception: %s", e)


def shutdown_workers():
    for _ in range(config.NUM_WORKERS):
        queue_url(SENTINEL)


def spawn_workers(loop):
    global WORK_QUEUE
    WORK_QUEUE = Queue(loop=loop)
    for _ in range(config.NUM_WORKERS):
        asyncio.ensure_future(queue_worker(loop), loop=loop)
