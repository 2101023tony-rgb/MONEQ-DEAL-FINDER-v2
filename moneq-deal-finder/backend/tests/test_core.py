import os
import sys
import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_PATH"] = "./test_moneq.db"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.services.profit_calc import calculate_profit
from app.database import init_db, upsert_deal


@pytest.fixture(autouse=True)
def setup_and_teardown():
    if os.path.exists("./test_moneq.db"):
        os.remove("./test_moneq.db")
    init_db()
    yield
    if os.path.exists("./test_moneq.db"):
        os.remove("./test_moneq.db")


def test_profit_calculation_formula():
    res = calculate_profit(
        buy_price=200000,
        expected_sell_price=250000,
        target_sell_platform="당근",
        shipping_cost=4000,
        other_cost=1000,
    )
    assert res.net_profit == 45000
    assert res.roi_percent == 22.5


def test_duplicate_deal_prevention():
    sample = {
        "platform": "당근",
        "external_id": "unique_999",
        "category": "게임기",
        "title": "테스트 스위치",
        "price": 250000,
        "market_avg_price": 320000,
        "url": "https://www.daangn.com",
        "data_source_type": "SAMPLE_DEMO",
    }
    first_insert = upsert_deal(sample)
    second_insert = upsert_deal(sample)
    assert first_insert is True
    assert second_insert is False


def test_api_endpoints_end_to_end():
    with TestClient(app) as client:
        r_health = client.get("/api/health")
        assert r_health.status_code == 200
        assert r_health.json()["status"] == "ok"

        r_rec = client.post("/api/recommend", json={"budget": 500000, "min_roi_percent": 5.0})
        assert r_rec.status_code == 200
        items = r_rec.json()
        assert len(items) > 0
        for item in items:
            assert item["deal"]["price"] <= 500000
            assert item["deal"]["profit"]["net_profit"] > 0

        r_analyze = client.get("/api/analyze", params={"q": "존재하지않는희귀우주선모델XYZ999"})
        assert r_analyze.status_code == 200
        assert r_analyze.json()["status"] == "INSUFFICIENT_DATA"

        r_list = client.post(
            "/api/listing/generate",
            json={
                "product_name": "에어팟 프로 2세대",
                "condition": "S급",
                "buy_price": 190000,
                "target_platform": "당근",
            },
        )
        assert r_list.status_code == 200
        assert "platform_formats" in r_list.json()
