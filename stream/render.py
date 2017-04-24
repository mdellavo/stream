import itertools
from stream import config

from pydub import AudioSegment


def chain(it):
    return list(itertools.chain.from_iterable(it))


class M3U8Renderer(object):
    def __init__(self, playlists, target_duration=config.TARGET_DURATION):
        self.playlists = playlists
        self.target_duration = target_duration

    def render_format_identifier(self):
        return ["#EXTM3U"]

    def render_tag_duration(self):
        return ["#EXT-X-TARGETDURATION:{}".format(self.target_duration)]

    def render_segment(self, item, segment_num):
        return [
            "#EXTINF:{},{}".format(self.target_duration, item.title),
            "/asset/{}/{}/{}".format(item.playlist.name, item.name, segment_num),
        ]

    def render_playlist_item(self, item):
        audio = AudioSegment.from_file(item.cache_path)
        segments, remainder = divmod(round(audio.duration_seconds), self.target_duration)
        lines = chain(self.render_segment(item, i) for i in range(segments))
        if remainder:
            pass
        return lines

    def render_playlist(self, playlist):
        return chain(self.render_playlist_item(i) for i in playlist.items)

    def render_playlists(self):
        return chain(self.render_playlist(p) for p in self.playlists)

    def render_endlist(self):
        return ["EXT-X-ENDLIST"]

    def render(self):
        lines = (
            self.render_format_identifier() +
            self.render_tag_duration() +
            self.render_playlists() +
            self.render_endlist()
        )
        return "\n".join(lines)
