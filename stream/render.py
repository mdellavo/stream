import itertools
from stream import config

from pydub import AudioSegment


def chain(it):
    return list(itertools.chain.from_iterable(it))


class M3U8Renderer(object):
    def __init__(self, playlist, root, target_duration=config.TARGET_DURATION):
        self.playlist = playlist
        self.root = root
        self.target_duration = target_duration

    def render_format_identifier(self):
        return ["#EXTM3U"]

    def render_tag_duration(self):
        return ["#EXT-X-TARGETDURATION:{}".format(self.target_duration)]

    def render_segment(self, track, segment_num):
        return [
            "#EXTINF:{},{}".format(self.target_duration, track.title),
            "{}/segments/{}/{}".format(self.root, track.digest, segment_num),
        ]

    def render_track(self, track):
        return chain(self.render_segment(track, i) for i in range(track.num_segments))

    def render_playlist(self, playlist):
        return chain(self.render_track(i.track) for i in playlist.upcoming_schedule)

    def render_endlist(self):
        return ["EXT-X-ENDLIST"]

    def render(self):
        lines = (
            self.render_format_identifier() +
            self.render_tag_duration() +
            self.render_playlist(self.playlist) +
            self.render_endlist()
        )
        return "\n".join(lines)
