from pathlib import Path

from app.constants import DATA_DIR

# ensure data dir exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

from app.storage.hybrid import HybridLMDBOfflineStorageHandler
from app.storage.lmdb import LMDBStorageHandler
from app.storage.tinydb import TinyDBStorageHandler

storage_handlers = {
    "tinydb": TinyDBStorageHandler,
    "lmdb": LMDBStorageHandler,
    "hybrid": HybridLMDBOfflineStorageHandler,
}
