import httpx
import statistics
from datetime import datetime
from typing import List
from ..config import settings
from ..models import MarketAnalysisResponse, ListingGenerateRequest, ListingGenerateResponse


class GeminiAnalyzer:
    model_name = "gemini-2.5-flash"

    @property
    def is_configured(self) -> bool:
        return bool(settings.gemini_api_key)

    async def analyze_market(
        self,
        query: str,
        observed_prices: List[int],
        sources: List[str],
        data_source_type: str,
    ) -> MarketAnalysisResponse:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not observed_prices:
            return MarketAnalysisResponse(
                query=query,
                status="INSUFFICIENT_DATA",
                message="확인된 실제 거래/매물 데이터가 부족합니다. 정확한 모델명으로 다시 검색하거나 API 연동을 확인해 주세요.",
                product_name=query,
                exact_model="데이터 부족",
                checked_at=now_str,
                sources=sources,
                data_source_type="INSUFFICIENT_DATA",
            )

        sorted_prices = sorted(observed_prices)
        avg_price = int(round(statistics.mean(sorted_prices)))
        median_price = int(round(statistics.median(sorted_prices)))
        current_used_price = sorted_prices[0]
        q75_idx = min(len(sorted_prices) - 1, int(len(sorted_prices) * 0.7))
        expected_resale = sorted_prices[q75_idx] if len(sorted_prices) > 1 else avg_price

        condition_matrix = {
            "S급 (미개봉/단순개봉)": int(round(avg_price * 1.08)),
            "A급 (외관 깨끗함)": avg_price,
            "B급 (생활기스 존재)": int(round(avg_price * 0.86)),
            "C급 (하자/수리필요)": int(round(avg_price * 0.68)),
        }

        competition = "높음 (매물 10건 이상)" if len(sorted_prices) >= 10 else ("보통" if len(sorted_prices) >= 4 else "낮음 (희소 매물)")

        return MarketAnalysisResponse(
            query=query,
            status="OK",
            product_name=query,
            exact_model=f"{query} (확인된 매물 {len(sorted_prices)}건 기준)",
            current_used_price=current_used_price,
            recent_prices=sorted_prices[:8],
            expected_resale_price=expected_resale,
            average_price=avg_price,
            median_price=median_price,
            condition_price_matrix=condition_matrix,
            competition_level=competition,
            checked_at=now_str,
            sources=sources,
            data_source_type=data_source_type,
        )

    async def generate_listing(self, req: ListingGenerateRequest) -> ListingGenerateResponse:
        recommended_price = int(round(req.buy_price * 1.18, -3))

        fallback_title = f"[{req.condition.split()[0]}] {req.product_name} 풀구성 급처/직거래·택배"
        fallback_desc = (
            f"■ 상품명: {req.product_name}\n"
            f"■ 제품 상태: {req.condition}\n"
            f"■ 구성품: {req.included_items}\n"
            f"■ 상세 설명: {req.defects}. 모든 기능 정상 작동 확인 완료했습니다.\n"
            f"■ 거래 방식: 직거래 및 안전결제 택배 모두 가능합니다. 쿨거래 시 네고 소폭 협의 가능합니다."
        )

        ai_title = fallback_title
        description = fallback_desc
        engine_mode = "RULE_BASED_TEMPLATE (GEMINI_API_KEY 미설정 시 기본 템플릿)"

        if self.is_configured:
            prompt = (
                f"당신은 중고거래 리셀 전문 카피라이터입니다. 다음 정보로 구매 전환율이 높은 중고 판매글을 작성하세요.\n"
                f"상품명: {req.product_name}, 상태: {req.condition}, 희망판매가: {recommended_price}원, "
                f"구성품: {req.included_items}, 특이사항: {req.defects}\n"
                f"첫 줄에는 '제목: ...' 형식으로 35자 이내 제목을 쓰고, 둘째 줄부터 본문을 작성하세요."
            )
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={settings.gemini_api_key}"
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    res = await client.post(
                        url,
                        json={"contents": [{"parts": [{"text": prompt}]}]},
                    )
                    res.raise_for_status()
                    text = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    lines = [line.strip() for line in text.splitlines() if line.strip()]
                    if lines and lines[0].startswith("제목:"):
                        ai_title = lines[0].replace("제목:", "").strip()
                        description = "\n".join(lines[1:]).strip()
                    else:
                        description = text
                    engine_mode = "GEMINI_LIVE_AI (gemini-2.5-flash)"
            except Exception as e:
                engine_mode = f"RULE_BASED_FALLBACK (API 오류: {type(e).__name__})"

        platform_formats = {
            "당근": f"{ai_title}\n\n희망가: {recommended_price:,}원\n\n{description}\n\n#직거래환영 #당근페이가능",
            "번개장터": f"[안전결제환영] {ai_title}\n판매가: {recommended_price:,}원\n\n{description}\n\n* 번개페이 안전결제 즉시 구매 가능합니다.",
            "중고나라": f"[판매] {ai_title} ({recommended_price:,}원)\n\n{description}",
        }

        return ListingGenerateResponse(
            ai_title=ai_title,
            recommended_price=recommended_price,
            description=description,
            platform_formats=platform_formats,
            auto_publish_supported=False,
            publish_notice="당근·번개장터는 일반 계정 대상 자동 게시 API를 지원하지 않습니다. 생성된 플랫폼별 양식을 복사하여 직접 등록해 주세요.",
            ai_engine_mode=engine_mode,
        )
