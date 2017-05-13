import logging

from stream.model import Session, Track

import sqlalchemy as sa


log = logging.getLogger(__name__)
LOOKAHEAD = 10


async def schedule(playlist):
    while playlist.upcoming_schedule.count() < LOOKAHEAD:
        track = Session.query(Track).order_by(sa.func.random()).first()
        scheduled_track = playlist.append(track)
        Session.add(scheduled_track)
        Session.commit()

        log.info("scheduled track %s from %s to %s", track.id, scheduled_track.start_time, scheduled_track.end_time)
