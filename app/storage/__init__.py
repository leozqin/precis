from app.storage.lmdb import LMDBStorageHandler
from app.storage.tinydb import TinyDBStorageHandler

storage_handlers = {"tinydb": TinyDBStorageHandler, "lmdb": LMDBStorageHandler}
