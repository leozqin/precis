from os import environ
from pathlib import Path

CONFIG_DIR = environ.get("CONFIG_DIR", Path(__file__, "../../configs"))