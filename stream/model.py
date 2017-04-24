import os

from stream.config import CACHE_DIR


class PlaylistItem(object):
    def __init__(self, playlist, url):
        self.playlist = playlist
        self.url = url

    def get_url(self):
        return self.url.geturl()

    @property
    def name(self):
        return os.path.basename(self.url.path)

    @property
    def cache_path(self):
        return os.path.join(self.playlist.cache_path, self.name)

    @property
    def temp_path(self):
        return self.cache_path + ".tmp"

    @property
    def title(self):
        return "{} - {}".format(self.playlist.name, self.name)


class Playlist(object):
    def __init__(self, url):
        self.url = url
        self.items = []

    @property
    def name(self):
        return os.path.basename(self.url.path)

    @property
    def cache_path(self):
        return os.path.join(CACHE_DIR, self.name)

    def add_item(self, url):
        self.items.append(PlaylistItem(self, url))

    def add_items(self, urls):
        for url in urls:
            self.add_item(url)
