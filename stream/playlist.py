import logging
import datetime

from stream import config
from stream.model import Session, Track, Playlist

import sqlalchemy as sa


log = logging.getLogger(__name__)


def calc_scheduled_minutes(playlist):
    durations = [st.duration.total_seconds() for st in playlist.upcoming_schedule]
    return datetime.timedelta(seconds=sum(durations))


def now_playing(loop, st):
    def _now_playing():
        log.info("now playing: %s", st.track.description)

    delta = (st.start_time - datetime.datetime.utcnow()).total_seconds()

    loop.call_later(delta, _now_playing)


def current_playlists(loop):
    for playlist in Session.query(Playlist):
        for st in playlist.upcoming_schedule:
            log.info("upcoming %s at %s", st.track.description, st.start_time.isoformat())
            now_playing(loop, st)


async def schedule(loop, playlist):
    while calc_scheduled_minutes(playlist) < datetime.timedelta(minutes=config.SCHEDULED_PLAYLIST_MINUES):

        track = Session.query(Track).order_by(sa.func.random()).first()
        scheduled_track = playlist.append(track)
        Session.add(scheduled_track)
        Session.commit()

        log.info("scheduled %s at %s", track.description, scheduled_track.start_time.isoformat())
        now_playing(loop, scheduled_track)

async def schedule_all(loop):
    for playlist in Session.query(Playlist):
        await schedule(loop, playlist)