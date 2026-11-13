import httpx
import re
from datetime import datetime
from typing import List, Dict, Any
from .base import DataSourceAdapter
from ..config import settings


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


class NaverShoppingAdapter(DataSourceAdapter):
    platform_name = "네이버쇼핑"
    endpoint = "https://openapi.naver.com/v1/search/shop.json"

    @property
    def is_configured(self) -> bool:
        return bool(settings.naver_client_id and settings.naver_client_secret)

    async def search_listings(self, query: str, category: str = "전체") -> List[Dict[str, Any]]:
        if not self.is_configured:
            return []

        headers = {
            "X-Naver-Client-Id": settings.naver_client_id,
            "X-Naver-Client-Secret": settings.naver_client_secret,
        }
        params = {
            "query": query,
            "display": 15,
            "sort": "sim",
        }

        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(self.endpoint, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()

        items = data.get("items", [])
        results: List[Dict[str, Any]] = []
        valid_prices = [int(i["lprice"]) for i in items if str(i.get("lprice", "")).isdigit() and int(i["lprice"]) > 0]
        avg_price = int(sum(valid_prices) / len(valid_prices)) if valid_prices else 0

        for item in items:
            lprice = int(item.get("lprice", 0))
            if lprice <= 0:
                continue
            title = _strip_html(item.get("title", query))
            product_id = str(item.get("productId", hash(title)))
            results.append({
                "platform": self.platform_name,
                "external_id": f"naver_{product_id}",
                "category": category,
                "title": title,
                "model_name": title,
                "price": lprice,
                "market_avg_price": avg_price or lprice,
                "condition": "새상품/리퍼 기준가",
                "region": item.get("mallName", "온라인"),
                "posted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "url": item.get("link", "https://shopping.naver.com"),
                "data_source_type": "LIVE_API",
            })
        return results
