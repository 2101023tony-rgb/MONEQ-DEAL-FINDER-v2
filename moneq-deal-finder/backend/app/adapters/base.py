from abc import ABC, abstractmethod
from typing import List, Dict, Any


class DataSourceAdapter(ABC):
    platform_name: str

    @abstractmethod
    async def search_listings(self, query: str, category: str = "전체") -> List[Dict[str, Any]]:
        pass
