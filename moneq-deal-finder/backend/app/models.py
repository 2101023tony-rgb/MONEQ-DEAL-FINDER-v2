from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class ProfitBreakdown(BaseModel):
    buy_price: int
    expected_sell_price: int
    platform_fee: int
    shipping_cost: int
    other_cost: int
    net_profit: int
    roi_percent: float


class DealItem(BaseModel):
    uid: str
    platform: str
    external_id: str
    category: str
    title: str
    model_name: str
    price: int
    market_avg_price: int
    discount_amount: int
    discount_percent: float
    condition: str
    region: str
    posted_at: str
    url: str
    data_source_type: str
    is_saved: bool = False
    profit: ProfitBreakdown


class MarketAnalysisResponse(BaseModel):
    query: str
    status: str
    message: Optional[str] = None
    product_name: str
    exact_model: str
    current_used_price: Optional[int] = None
    recent_prices: List[int] = []
    expected_resale_price: Optional[int] = None
    average_price: Optional[int] = None
    median_price: Optional[int] = None
    condition_price_matrix: Dict[str, int] = {}
    competition_level: str = "알 수 없음"
    checked_at: str
    sources: List[str] = []
    data_source_type: str = "INSUFFICIENT_DATA"


class BudgetRecommendRequest(BaseModel):
    budget: int = Field(..., gt=0, description="보유 예산 (원)")
    min_roi_percent: float = Field(default=8.0, ge=0)
    category: Optional[str] = None


class BudgetRecommendationItem(BaseModel):
    deal: DealItem
    reason: str
    caution: str


class ListingGenerateRequest(BaseModel):
    product_name: str
    condition: str = "S급 (미세 사용감)"
    buy_price: int
    target_platform: str = "당근"
    included_items: str = "풀박스, 정품 충전 케이블"
    defects: str = "기능 이상 없음, 외관 깨끗함"


class ListingGenerateResponse(BaseModel):
    ai_title: str
    recommended_price: int
    description: str
    platform_formats: Dict[str, str]
    auto_publish_supported: bool
    publish_notice: str
    ai_engine_mode: str
