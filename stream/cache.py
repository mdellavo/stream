import os

from stream import config

EXTENSIONS = {
    "audio/mp3": "mp3",
}


class Cache(object):

    def get_cache_dir(self, track):
        return os.path.join(config.CACHE_DIR, track.digest)

    def get_cache_path(self, track):
        ext = EXTENSIONS[track.mime]
        filename = track.digest + "." + ext
        return os.path.join(self.get_cache_dir(track), filename)

    def get_segment_format(self, track):
        return "{}.%05d.ts".format(track.digest)

    def get_segment_format_path(self, track):
        return os.path.join(self.get_cache_dir(track), self.get_segment_format(track))

    def get_segment_path(self, track, i):
        segment_name = "{}.{:05d}.ts".format(track.digest, i)
        return os.path.join(self.get_cache_dir(track), segment_name)
