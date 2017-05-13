import math
import itertools
import datetime

from stream import config


def chain(it):
    return list(itertools.chain.from_iterable(it))


class M3U8Renderer(object):
    def __init__(self, playlist, root, target_duration=config.TARGET_DURATION):
        self.playlist = playlist
        self.root = root
        self.target_duration = target_duration

    def render_format_identifier(self):
        return ["#EXTM3U"]

    def render_preamble(self):
        return [
            "#EXT-X-TARGETDURATION:{}".format(self.target_duration),
            "#EXT-X-INDEPENDENT-SEGMENTS",
        ]

    def render_segment(self, track, segment_num):
        return [
            "#EXTINF:{},{}".format(self.target_duration, track.title),
            "{}/segments/{}/{}".format(self.root, track.digest, segment_num),
        ]

    def render_track(self, scheduled_track):
        track = scheduled_track.track

        now = datetime.datetime.utcnow()
        if scheduled_track.start_time < now:
            offset = int(math.floor((now - scheduled_track.start_time).total_seconds() / self.target_duration))
        else:
            offset = 0

        return [
            "#EXT-X-PROGRAM-DATE-TIME:{}".format(scheduled_track.start_time.isoformat("T")),
        ] + chain(self.render_segment(track, i) for i in range(offset, track.num_segments))

    def render_playlist(self, playlist):
        return chain(self.render_track(i) for i in playlist.upcoming_schedule)

    def render_endlist(self):
        return ["#EXT-X-ENDLIST"]

    def render(self):
        lines = (
            self.render_format_identifier() +
            self.render_preamble() +
            self.render_playlist(self.playlist) +
            self.render_endlist()
        )
        return "\n".join(lines)
