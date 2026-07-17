from abc import ABC, abstractmethod
from ..http import HttpClient
from ..models import DatasetRecord
class BaseSource(ABC):
    name="base"
    def __init__(self, config): self.config=config; self.http=HttpClient(config)
    @abstractmethod
    def search(self, query: str) -> list[DatasetRecord]: ...
