import datetime
from abc import abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict


@dataclass
class URLEntry:
    long_url: str
    short_url: str
    times_accessed: int
    last_accessed: Optional[datetime.datetime]


class DB:

    @abstractmethod
    def create_url_entry(self, long_url: str, short_url: str) -> bool: pass

    @abstractmethod
    def get_url_entry(self, short_url: str) -> Optional[str]: pass


class InMemoryDb(DB):
    def __init__(self):
        self.mapping_dict: Dict[str, URLEntry] = {}

    def create_url_entry(self, long_url: str, short_url: str) -> bool:
        if short_url not in self.mapping_dict:
            self.mapping_dict[short_url] = URLEntry(long_url, short_url, 0, None)
            return True
        else:
            return False

    def get_url_entry(self, short_url: str) -> str:
        print(self.mapping_dict)
        return self.mapping_dict[short_url].long_url if short_url in self.mapping_dict else None
