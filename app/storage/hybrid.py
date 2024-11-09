from os import remove
from pathlib import Path
from pickle import dump, load
from typing import Union

from app.constants import DATA_DIR
from app.models import EntryContent, FeedEntry
from app.storage.lmdb import LMDBStorageHandler


class HybridLMDBOfflineStorageHandler(LMDBStorageHandler):
    def __init__(self) -> None:
        super().__init__()

        self.offline_media_path = Path(DATA_DIR, "media")
        self.offline_media_path.mkdir(parents=True, exist_ok=True)

    def _content_path(self, content: Union[EntryContent, FeedEntry]):
        return self.offline_media_path.joinpath(content.id).with_suffix(".pickle")

    async def upsert_entry_content(self, content: EntryContent):

        content_path = self._content_path(content)

        with open(content_path.resolve(), "wb") as fp:
            dump(content, fp)

    def entry_content_exists(self, entry: FeedEntry):

        content_path = self._content_path(entry)

        return content_path.exists() and content_path.stat().st_size > 0

    def retrieve_entry_content(self, entry: FeedEntry) -> EntryContent:

        content_path = self._content_path(entry)
        with open(content_path, "rb") as fp:
            content: EntryContent = load(fp)

            return content

    def delete_entry_content(self, entry: EntryContent):

        content_path = self._content_path(entry)
        remove(content_path)
