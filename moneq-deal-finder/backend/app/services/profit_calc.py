from ..models import ProfitBreakdown

PLATFORM_FEE_RATES = {
    "당근": 0.0,
    "번개장터": 0.035,
    "네이버쇼핑": 0.055,
    "기타": 0.035,
}


def calculate_profit(
    buy_price: int,
    expected_sell_price: int,
    target_sell_platform: str = "번개장터",
    shipping_cost: int = 4000,
    other_cost: int = 1000,
) -> ProfitBreakdown:
    fee_rate = PLATFORM_FEE_RATES.get(target_sell_platform, 0.035)
    platform_fee = int(round(expected_sell_price * fee_rate))
    net_profit = expected_sell_price - buy_price - platform_fee - shipping_cost - other_cost
    roi_percent = round((net_profit / buy_price) * 100, 2) if buy_price > 0 else 0.0

    return ProfitBreakdown(
        buy_price=buy_price,
        expected_sell_price=expected_sell_price,
        platform_fee=platform_fee,
        shipping_cost=shipping_cost,
        other_cost=other_cost,
        net_profit=net_profit,
        roi_percent=roi_percent,
    )
