import os

HERE = os.path.dirname(__file__)
CACHE_DIR = os.path.join(HERE, "..", "cache")

NUM_DOWNLOADS = 4
CHUNK_SIZE = 4 * 1024

TARGET_DURATION = 30