import math
import itertools
import datetime

from stream import config


def chain(it):
    return list(itertools.chain.from_iterable(it))


class M3U8Renderer(object):
    def __init__(self, root, target_duration=config.TARGET_DURATION, version=6, lookback=10):
        self.root = root
        self.target_duration = int(target_duration)
        self.version = version
        self.lookback = lookback

    def render_format_identifier(self):
        return ["#EXTM3U"]

    def render_preamble(self):
        return [
            "#EXT-X-VERSION:{}".format(self.version),
            "#EXT-X-TARGETDURATION:{}".format(self.target_duration),
        ]

    def render_segment(self, track, segment_num):
        complete_segments, remainder = divmod(track.length, self.target_duration)
        if segment_num < complete_segments:
            duration = self.target_duration
        else:
            duration = remainder

        title = "{} - {} - {}".format(track.artist, track.album, track.title)
        return [
            "#EXTINF:{:.04},{}".format(float(duration), title),
            "{}/segments/{}/{}".format(self.root, track.digest, segment_num),
        ]

    def select_tracks(self, playlist, start_time):
        rv = []
        cursor = playlist.recent_schedule(start_time).all()

        def next_track():
            return cursor.pop(0)

        scheduled_track = next_track()
        segment_num = 0
        for i in range(self.lookback):
            t = start_time - datetime.timedelta(seconds=i * self.target_duration)

            if t < scheduled_track.start_time:
                scheduled_track = next_track()

            segment_num = int(math.ceil((t - scheduled_track.start_time).total_seconds() / self.target_duration))
            rv.append((scheduled_track, segment_num))

        sequence_num = segment_num
        sequence_num += sum(scheduled_track.track.calc_num_segments(self.target_duration) for scheduled_track in cursor)

        return reversed(rv), sequence_num

    def render_playlist(self, playlist, start_time):
        parts, sequence_num = self.select_tracks(playlist, start_time)
        return [
            "#EXT-X-MEDIA-SEQUENCE:{}".format(sequence_num)
        ] + chain(self.render_segment(scheduled_track.track, segment_num) for scheduled_track, segment_num in parts)

    def render(self, playlist, start_time):
        lines = (
            self.render_format_identifier() +
            self.render_preamble() +
            self.render_playlist(playlist, start_time)
        )
        return "\n".join(lines) + "\n"
