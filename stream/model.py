import datetime
import collections

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
session_factory = sessionmaker(expire_on_commit=False)
Session = session_factory()


class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True)
    digest = Column(String, unique=True)

    metadata_items = relationship("TrackMetadata")

    @property
    def metatada(self):
        rv = collections.defaultdict(list)
        for item in self.metadata_items:
            rv[item.key].append(item.value)
        return rv

    @property
    def mime(self):
        return self.metatada[MetadataKeys.MIME][0]

    @property
    def length(self):
        return float(self.metatada[MetadataKeys.LENGTH][0])


class MetadataKeys(object):
    LENGTH = "len"
    TITLE = "tit"
    ARTIST = "art"
    ALBUM = "alb"
    TRACK = "trk"
    MIME = "mime"


class TrackMetadata(Base):
    __tablename__ = "track_metadata"

    id = Column(Integer, primary_key=True)
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=False)
    key = Column(String)
    value = Column(String)
    track = relationship(Track)


class SeenUrl(Base):
    __tablename__ = "seen_urls"

    url = Column(String, primary_key=True)
    track_id = Column(Integer, ForeignKey("tracks.id"))
    track = relationship(Track)


class Playlist(Base):
    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    schedule = relationship("ScheduledTrack", lazy="dynamic",
                            order_by="ScheduledTrack.start_time")

    @classmethod
    def find_or_create(cls, name):
        playlist = Session.query(cls).filter_by(name=name).first()
        if not playlist:
            playlist = cls(name=name)
            Session.add(playlist)
            Session.commit()
        return playlist

    @property
    def upcoming_schedule(self):
        now = datetime.datetime.utcnow()
        return self.schedule.filter(ScheduledTrack.start_time > now)

    def append(self, track):
        last_scheduled = (Session.query(ScheduledTrack)
                                 .filter_by(playlist=self)
                                 .order_by(ScheduledTrack.start_time.desc())
                                 .first())

        start_time = last_scheduled.end_time if last_scheduled else datetime.datetime.utcnow()
        end_time = start_time + datetime.timedelta(seconds=track.length)
        scheduled_track = ScheduledTrack(
            playlist=self,
            track=track,
            start_time=start_time,
            end_time=end_time,
        )
        self.schedule.append(scheduled_track)
        return scheduled_track


class ScheduledTrack(Base):
    __tablename__ = "scheduled_tracks"

    id = Column(Integer, primary_key=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id"), nullable=False)
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)

    playlist = relationship(Playlist)
    track = relationship(Track)
