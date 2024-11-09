from os import environ
from pathlib import Path

CONFIG_DIR = environ.get("CONFIG_DIR", Path(__file__, "../../configs"))
DATA_DIR = Path(environ.get("DATA_DIR", Path(Path(__file__).parent, "../")))
IS_DOCKER = bool(environ.get("IS_DOCKER", False))
# overrride this if you feel it's important to point to your fork
GITHUB_LINK = environ.get("GITHUB_LINK", "https://github.com/leozqin/precis")
