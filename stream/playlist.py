import logging
import datetime

from stream import config
from stream.model import Session, Track, Playlist

import sqlalchemy as sa


log = logging.getLogger(__name__)


def calc_scheduled_minutes(playlist):
    durations = [st.duration.total_seconds() for st in playlist.upcoming_schedule]
    return datetime.timedelta(seconds=sum(durations))


async def schedule(playlist):
    while calc_scheduled_minutes(playlist) < datetime.timedelta(minutes=config.SCHEDULED_PLAYLIST_MINUES):

        track = Session.query(Track).order_by(sa.func.random()).first()
        scheduled_track = playlist.append(track)
        Session.add(scheduled_track)
        Session.commit()

        log.info("scheduled track %s from %s to %s", track.id, scheduled_track.start_time, scheduled_track.end_time)


async def schedule_all():
    for playlist in Session.query(Playlist):
        await schedule(playlist)