import math
import itertools
import datetime

from stream import config


def chain(it):
    return list(itertools.chain.from_iterable(it))


class M3U8Renderer(object):
    def __init__(self, playlist, root, sequence=0, target_duration=config.TARGET_DURATION, version=3):
        self.playlist = playlist
        self.root = root
        self.sequence = sequence
        self.target_duration = int(target_duration)
        self.version = version

    def render_format_identifier(self):
        return ["#EXTM3U"]

    def render_preamble(self):
        return [
            "#EXT-X-ALLOW-CACHE:YES",
            "#EXT-X-VERSION:{}".format(self.version),
            "#EXT-X-TARGETDURATION:{}".format(self.target_duration),
            #"#EXT-X-MEDIA-SEQUENCE:{}".format(self.sequence),
        ]

    def render_segment(self, track, segment_num):
        complete_segments, remainder = divmod(track.length, self.target_duration)
        if segment_num < complete_segments:
            duration = self.target_duration
        else:
            duration = remainder

        title = "{} - {} - {}".format(track.artist, track.album, track.title)
        return [
            #"#EXT-X-DISCONTINUITY",
            "#EXTINF:{},{}".format(float(duration), title),
            "{}/segments/{}/{}".format(self.root, track.digest, segment_num),
        ]

    def render_track(self, scheduled_track):
        track = scheduled_track.track

        now = datetime.datetime.utcnow()
        if scheduled_track.start_time < now:
            offset = int(math.ceil((now - scheduled_track.start_time).total_seconds() / self.target_duration))
            start_time = now
        else:
            offset = 0
            start_time = scheduled_track.start_time

        return [
            "#EXT-X-PROGRAM-DATE-TIME:{}".format(start_time.isoformat("T")),
        ] + chain(self.render_segment(track, i) for i in range(offset, track.num_segments))

    def render_playlist(self, playlist):
        return chain(self.render_track(i) for i in playlist.upcoming_schedule)

    def render(self):
        lines = (
            self.render_format_identifier() +
            self.render_preamble() +
            self.render_playlist(self.playlist)
        )
        return "\n".join(lines)
