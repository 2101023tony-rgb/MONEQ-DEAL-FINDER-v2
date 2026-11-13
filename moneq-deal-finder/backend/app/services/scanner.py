from typing import List, Dict, Any
from ..adapters.naver_api import NaverShoppingAdapter
from ..adapters.marketplace import PartnerMarketplaceAdapter
from ..config import settings
from ..database import upsert_deal, get_all_deals
from ..models import DealItem
from .profit_calc import calculate_profit

CATEGORIES = [
    "아이폰 및 갤럭시",
    "명품 가방 및 지갑",
    "명품 시계",
    "에어팟 및 헤드폰",
    "노트북 및 태블릿",
    "게임기",
    "카메라",
    "기타 중고 전자제품",
]


class DealScannerService:
    def __init__(self):
        self.naver = NaverShoppingAdapter()
        self.daangn = PartnerMarketplaceAdapter(
            "당근", settings.daangn_partner_api_key, settings.daangn_partner_endpoint
        )
        self.bunjang = PartnerMarketplaceAdapter(
            "번개장터", settings.bunjang_partner_api_key, settings.bunjang_partner_endpoint
        )

    def _enrich_deal(self, raw: Dict[str, Any]) -> DealItem:
        price = int(raw["price"])
        avg_price = int(raw["market_avg_price"])
        discount_amount = max(0, avg_price - price)
        discount_percent = round((discount_amount / avg_price) * 100, 1) if avg_price > 0 else 0.0

        expected_sell = int(round(avg_price * 0.96, -2))
        target_sell_platform = "번개장터" if raw["platform"] == "당근" else "당근"
        profit = calculate_profit(
            buy_price=price,
            expected_sell_price=expected_sell,
            target_sell_platform=target_sell_platform,
        )

        return DealItem(
            uid=f"{raw['platform']}:{raw['external_id']}",
            platform=raw["platform"],
            external_id=raw["external_id"],
            category=raw.get("category", "기타 중고 전자제품"),
            title=raw["title"],
            model_name=raw.get("model_name", raw["title"]),
            price=price,
            market_avg_price=avg_price,
            discount_amount=discount_amount,
            discount_percent=discount_percent,
            condition=raw.get("condition", "A급"),
            region=raw.get("region", "전국"),
            posted_at=raw.get("posted_at", "방금 전"),
            url=raw["url"],
            data_source_type=raw.get("data_source_type", "SAMPLE_DEMO"),
            is_saved=bool(raw.get("is_saved", 0)),
            profit=profit,
        )

    async def scan_and_store(self, query: str = "", category: str = "전체") -> List[DealItem]:
        collected: List[Dict[str, Any]] = []
        collected.extend(await self.daangn.search_listings(query=query, category=category))
        collected.extend(await self.bunjang.search_listings(query=query, category=category))
        if query and self.naver.is_configured:
            collected.extend(await self.naver.search_listings(query=query, category=category))

        for item in collected:
            upsert_deal(item)

        db_rows = get_all_deals(category=category)
        enriched = [self._enrich_deal(r) for r in db_rows]
        if query:
            q_lower = query.lower()
            enriched = [
                d for d in enriched
                if q_lower in d.title.lower() or q_lower in d.model_name.lower() or q_lower in d.category.lower()
            ]
        return enriched
