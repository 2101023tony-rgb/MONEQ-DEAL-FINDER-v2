import httpx
from typing import List, Dict, Any
from .base import DataSourceAdapter

VERIFIED_SAMPLE_FEED: List[Dict[str, Any]] = [
    {
        "platform": "당근",
        "external_id": "dg_sample_1001",
        "category": "에어팟 및 헤드폰",
        "title": "[테스트샘플] 애플 에어팟 프로 2세대 USB-C 미개봉급 풀박스",
        "model_name": "AirPods Pro 2 (USB-C)",
        "price": 195000,
        "market_avg_price": 245000,
        "condition": "S급 (실사용 2회)",
        "region": "서울 강남구 역삼동",
        "posted_at": "12분 전",
        "url": "https://www.daangn.com",
        "data_source_type": "SAMPLE_DEMO",
    },
    {
        "platform": "번개장터",
        "external_id": "bj_sample_2001",
        "category": "아이폰 및 갤럭시",
        "title": "[테스트샘플] 아이폰 15 프로 256GB 내추럴 티타늄 배터리 94%",
        "model_name": "iPhone 15 Pro 256GB",
        "price": 960000,
        "market_avg_price": 1120000,
        "condition": "A급 (찍힘 없음)",
        "region": "경기 성남시 분당구",
        "posted_at": "24분 전",
        "url": "https://m.bunjang.co.kr",
        "data_source_type": "SAMPLE_DEMO",
    },
    {
        "platform": "당근",
        "external_id": "dg_sample_1002",
        "category": "게임기",
        "title": "[테스트샘플] 닌텐도 스위치 OLED 화이트 + 젤다 왕눈 칩 포함",
        "model_name": "Nintendo Switch OLED",
        "price": 265000,
        "market_avg_price": 335000,
        "condition": "A급 (보호필름 부착)",
        "region": "서울 마포구 합정동",
        "posted_at": "38분 전",
        "url": "https://www.daangn.com",
        "data_source_type": "SAMPLE_DEMO",
    },
    {
        "platform": "번개장터",
        "external_id": "bj_sample_2002",
        "category": "노트북 및 태블릿",
        "title": "[테스트샘플] 아이패드 에어 5세대 M1 Wi-Fi 64GB 스페이스그레이",
        "model_name": "iPad Air 5 M1 64GB",
        "price": 430000,
        "market_avg_price": 530000,
        "condition": "S급 (애플케어 만료전)",
        "region": "서울 송파구 잠실동",
        "posted_at": "51분 전",
        "url": "https://m.bunjang.co.kr",
        "data_source_type": "SAMPLE_DEMO",
    },
    {
        "platform": "당근",
        "external_id": "dg_sample_1003",
        "category": "카메라",
        "title": "[테스트샘플] 소니 ZV-E10 바디 + 번들렌즈 16-50mm 급처",
        "model_name": "Sony ZV-E10 Kit",
        "price": 540000,
        "market_avg_price": 660000,
        "condition": "A급 (셔터수 3천컷 미만)",
        "region": "부산 해운대구 우동",
        "posted_at": "1시간 전",
        "url": "https://www.daangn.com",
        "data_source_type": "SAMPLE_DEMO",
    },
    {
        "platform": "번개장터",
        "external_id": "bj_sample_2003",
        "category": "명품 가방 및 지갑",
        "title": "[테스트샘플] 보테가베네타 카세트 반지갑 블랙 정품 개런티포함",
        "model_name": "Bottega Veneta Cassette Wallet",
        "price": 460000,
        "market_avg_price": 580000,
        "condition": "A급 (모서리 마모 미세)",
        "region": "서울 용산구 한남동",
        "posted_at": "1시간 전",
        "url": "https://m.bunjang.co.kr",
        "data_source_type": "SAMPLE_DEMO",
    },
    {
        "platform": "당근",
        "external_id": "dg_sample_1004",
        "category": "명품 시계",
        "title": "[테스트샘플] 태그호이어 포뮬러1 쿼츠 41mm WAZ1110 백화점 스탬핑",
        "model_name": "TAG Heuer Formula 1 WAZ1110",
        "price": 980000,
        "market_avg_price": 1220000,
        "condition": "A급 (폴리싱 이력 없음)",
        "region": "서울 서초구 반포동",
        "posted_at": "2시간 전",
        "url": "https://www.daangn.com",
        "data_source_type": "SAMPLE_DEMO",
    },
    {
        "platform": "번개장터",
        "external_id": "bj_sample_2004",
        "category": "기타 중고 전자제품",
        "title": "[테스트샘플] 다이슨 에어랩 멀티 스타일러 롱 배럴 코퍼",
        "model_name": "Dyson Airwrap Complete Long",
        "price": 340000,
        "market_avg_price": 430000,
        "condition": "A급 (정품 등록 가능)",
        "region": "인천 연수구 송도동",
        "posted_at": "2시간 전",
        "url": "https://m.bunjang.co.kr",
        "data_source_type": "SAMPLE_DEMO",
    },
    {
        "platform": "당근",
        "external_id": "dg_sample_1005",
        "category": "에어팟 및 헤드폰",
        "title": "[테스트샘플] 소니 WH-1000XM5 블랙 노이즈캔슬링 헤드폰 케이스포함",
        "model_name": "Sony WH-1000XM5",
        "price": 230000,
        "market_avg_price": 295000,
        "condition": "S급 (이어패드 깨끗함)",
        "region": "경기 수원시 영통구",
        "posted_at": "3시간 전",
        "url": "https://www.daangn.com",
        "data_source_type": "SAMPLE_DEMO",
    },
]


class PartnerMarketplaceAdapter(DataSourceAdapter):
    def __init__(self, platform_name: str, api_key: str = "", endpoint: str = ""):
        self.platform_name = platform_name
        self.api_key = api_key
        self.endpoint = endpoint

    @property
    def is_live_connected(self) -> bool:
        return bool(self.api_key and self.endpoint)

    async def search_listings(self, query: str, category: str = "전체") -> List[Dict[str, Any]]:
        if self.is_live_connected:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            params = {"q": query, "category": category}
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(self.endpoint, headers=headers, params=params)
                resp.raise_for_status()
                raw_items = resp.json().get("items", [])
                for item in raw_items:
                    item["data_source_type"] = "LIVE_API"
                return raw_items

        q_lower = query.strip().lower()
        filtered = []
        for item in VERIFIED_SAMPLE_FEED:
            if item["platform"] != self.platform_name:
                continue
            if category != "전체" and item["category"] != category:
                continue
            if q_lower and q_lower not in item["title"].lower() and q_lower not in item["model_name"].lower() and q_lower not in item["category"].lower():
                continue
            filtered.append(item)
        return filtered
