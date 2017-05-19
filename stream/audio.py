import os
import hashlib
import tempfile
import urllib
import logging
import asyncio

from aiohttp import ClientSession
import mutagen

from stream import config
from stream.model import Session, Track, SeenUrl, TrackMetadata, MetadataKeys
from stream.cache import Cache
from stream.utils import TaskPool

log = logging.getLogger(__name__)


async def segment_track(track_path, output_path, segment_duration):
    args = [
        "/usr/local/bin/ffmpeg",
        #"-loglevel", "-8",
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
    proc = await asyncio.create_subprocess_exec(*args, stdout=None, stdin=None, stderr=None)
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


async def prepare_track(loop, url):
    cache = Cache()
    seen = Session.query(SeenUrl).filter_by(url=url).first()
    if seen:
        return seen.track

    log.info("caching item %s", url)

    with tempfile.NamedTemporaryFile(delete=False) as f:

        digester = hashlib.sha256()

        async with ClientSession(loop=loop) as session, session.get(url) as response:

            while True:
                chunk = await response.content.read(config.CHUNK_SIZE)
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

            os.makedirs(cache.get_cache_dir(track), exist_ok=True)
            cache_path = cache.get_cache_path(track)
            os.rename(f.name, cache_path)
            await segment_track(cache_path, cache.get_segment_format_path(track), config.TARGET_DURATION)
            os.remove(cache_path)

    seen = SeenUrl(url=url, track=track)
    Session.add(seen)
    Session.commit()

    return track if metadata else None


async def load_playlist(loop, url):
    log.info("loading playlist: %s", url)

    parsed_url = urllib.parse.urlparse(url)
    if parsed_url.scheme in ("http", "https"):
        async with ClientSession(loop=loop) as session, session.get(url) as response:
            body = response.text()
    elif not parsed_url.scheme or parsed_url.scheme == "file":
        with open(parsed_url.path) as f:
            body = f.read()
    else:
        raise ValueError("unknown url scheme: {}".format(url))
    items_urls = body.splitlines()

    pool = TaskPool(loop, config.NUM_DOWNLOADS)
    futures = [pool.submit(prepare_track(loop, url)) for url in items_urls]
    await pool.join()

    tracks = []
    for future in futures:
        track = future.result()
        if track:
            tracks.append(track)
    return tracks


async def load_playlists(loop, urls):
    tracks = []
    for url in urls:
        tracks.extend(await load_playlist(loop, url))
    return tracks