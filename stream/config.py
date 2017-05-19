import os

HERE = os.path.dirname(__file__)

CACHE_DIR = os.path.join(HERE, "..", "cache")

DB_URL = "sqlite:///stream.sqlite"

NUM_DOWNLOADS = 4
CHUNK_SIZE = 64 * 1024

TARGET_DURATION = 10

PLAYLIST_NAME = "test"

BITRATE = "192k"