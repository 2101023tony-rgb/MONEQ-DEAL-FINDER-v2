import asyncio
import time
from contextlib import asynccontextmanager
from typing import List, Dict
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db, get_cache, set_cache, toggle_save_deal, get_all_deals
from .models import (
    DealItem,
    MarketAnalysisResponse,
    BudgetRecommendRequest,
    BudgetRecommendationItem,
    ListingGenerateRequest,
    ListingGenerateResponse,
)
from .services.scanner import DealScannerService, CATEGORIES
from .services.ai_engine import GeminiAnalyzer

scanner_service = DealScannerService()
ai_analyzer = GeminiAnalyzer()

_rate_limit_store: Dict[str, List[float]] = {}


async def _background_category_scanner():
    while True:
        try:
            await scanner_service.scan_and_store(query="", category="전체")
        except Exception:
            pass
        await asyncio.sleep(900)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    await scanner_service.scan_and_store(query="", category="전체")
    task = asyncio.create_task(_background_category_scanner())
    yield
    task.cancel()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="AI 기반 중고거래 차익 분석 및 꿀매물 자동 탐색 백엔드 API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    timestamps = [t for t in _rate_limit_store.get(client_ip, []) if now - t < 60]
    if len(timestamps) >= 60:
        raise HTTPException(status_code=429, detail="API 호출 한도 초과 (분당 최대 60회). 잠시 후 다시 시도해 주세요.")
    timestamps.append(now)
    _rate_limit_store[client_ip] = timestamps
    return await call_next(request)


@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "service": settings.app_name,
        "integrations": {
            "naver_shopping_api": "LIVE_CONNECTED" if scanner_service.naver.is_configured else "UNCONFIGURED (키 미설정)",
            "gemini_ai_api": "LIVE_CONNECTED" if ai_analyzer.is_configured else "FALLBACK_TEMPLATE (키 미설정)",
            "daangn_api": "LIVE_PARTNER" if scanner_service.daangn.is_live_connected else "SAMPLE_DEMO (공식 개인 API 미제공)",
            "bunjang_api": "LIVE_PARTNER" if scanner_service.bunjang.is_live_connected else "SAMPLE_DEMO (공식 개인 API 미제공)",
        },
        "categories": CATEGORIES,
    }


@app.get("/api/deals", response_model=List[DealItem])
async def search_deals(
    q: str = Query(default="", description="검색 상품명"),
    category: str = Query(default="전체", description="카테고리 필터"),
    sort_by: str = Query(default="profit", pattern="^(profit|lowest_price|latest|roi)$"),
    saved_only: bool = Query(default=False),
):
    cache_key = f"deals:{q}:{category}:{sort_by}:{saved_only}"
    cached = get_cache(cache_key)
    if cached and not saved_only:
        return cached

    if saved_only:
        rows = get_all_deals(category=category, saved_only=True)
        deals = [scanner_service._enrich_deal(r) for r in rows]
    else:
        deals = await scanner_service.scan_and_store(query=q, category=category)

    if sort_by == "profit":
        deals.sort(key=lambda x: x.profit.net_profit, reverse=True)
    elif sort_by == "roi":
        deals.sort(key=lambda x: x.profit.roi_percent, reverse=True)
    elif sort_by == "lowest_price":
        deals.sort(key=lambda x: x.price)

    serialized = [d.model_dump() for d in deals]
    if not saved_only:
        set_cache(cache_key, serialized, ttl=120)
    return serialized


@app.post("/api/deals/{platform}/{external_id}/save")
async def save_or_unsave_deal(platform: str, external_id: str):
    saved = toggle_save_deal(platform, external_id)
    return {"platform": platform, "external_id": external_id, "is_saved": saved}


@app.get("/api/analyze", response_model=MarketAnalysisResponse)
async def analyze_product_market(q: str = Query(..., min_length=1, description="분석할 상품명")):
    cache_key = f"analyze:{q.strip().lower()}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    deals = await scanner_service.scan_and_store(query=q, category="전체")
    prices = [d.price for d in deals]
    sources = sorted(list({f"{d.platform} ({d.data_source_type})" for d in deals}))
    source_type = "LIVE_API" if any(d.data_source_type == "LIVE_API" for d in deals) else ("SAMPLE_DEMO" if deals else "INSUFFICIENT_DATA")

    result = await ai_analyzer.analyze_market(
        query=q,
        observed_prices=prices,
        sources=sources,
        data_source_type=source_type,
    )
    set_cache(cache_key, result.model_dump(), ttl=300)
    return result


@app.post("/api/recommend", response_model=List[BudgetRecommendationItem])
async def recommend_by_budget(req: BudgetRecommendRequest):
    deals = await scanner_service.scan_and_store(query="", category=req.category or "전체")
    affordable = [
        d for d in deals
        if d.price <= req.budget and d.profit.net_profit > 0 and d.profit.roi_percent >= req.min_roi_percent
    ]
    affordable.sort(key=lambda x: (x.profit.roi_percent, x.profit.net_profit), reverse=True)

    recommendations: List[BudgetRecommendationItem] = []
    for d in affordable[:10]:
        reason = (
            f"보유 예산({req.budget:,}원) 이내 매입 가능(잔여 예산 {req.budget - d.price:,}원)하며, "
            f"동일 모델 평균 시세({d.market_avg_price:,}원) 대비 {d.discount_percent}% 저렴하게 출회된 고수익 매물입니다."
        )
        caution = (
            "직거래 시 외관 기스·배터리 성능·정품 시리얼 번호를 현장에서 반드시 교차 검증하고, "
            "택배 거래 시 플랫폼 공식 안전결제만 이용하세요."
        )
        recommendations.append(
            BudgetRecommendationItem(deal=d, reason=reason, caution=caution)
        )
    return recommendations


@app.post("/api/listing/generate", response_model=ListingGenerateResponse)
async def create_resale_listing(req: ListingGenerateRequest):
    return await ai_analyzer.generate_listing(req)
