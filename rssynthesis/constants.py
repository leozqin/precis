from os import environ
from pathlib import Path

CONFIG_DIR = environ.get("CONFIG_DIR", Path(__file__, "../../configs"))
DATA_DIR = environ.get("DATA_DIR", Path(Path(__file__).parent, "../"))
