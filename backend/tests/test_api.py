from datetime import date

from fastapi.testclient import TestClient

from app.main import app
from app.repository import get_market_repository
from app.schemas import AssetSearchResponse, AssetSummary, Candle, CandleSeriesResponse


ASSET = AssetSummary(
    asset_id="stock:SH:600519",
    source_id="29",
    market="SH",
    symbol="600519",
    name="贵州茅台",
    asset_type="stock",
    status="active",
    last_data_date=date(2026, 8, 7),
    last_price=1309.22,
    currency="CNY",
    change=0.67,
    change_percent=0.05,
)


class FakeRepository:
    def ping(self) -> str:
        return "9.6.0"

    def search_assets(self, query: str = "", asset_type: str | None = None, limit: int = 20):
        del asset_type, limit
        items = [ASSET] if query in ("", "600519", "贵州茅台") else []
        return AssetSearchResponse(items=items, total=len(items))

    def get_candles(self, asset_id: str, start: date, end: date):
        assert asset_id == ASSET.asset_id
        candles = [
            Candle(date=date(2026, 8, 6), open=1308.66, high=1315.28, low=1301, close=1309.22, volume=2497600),
            Candle(date=date(2026, 8, 7), open=1309.22, high=1320, low=1306, close=1317.5, volume=3020000),
        ]
        return CandleSeriesResponse(
            asset=ASSET,
            requested_start_date=start,
            requested_end_date=end,
            actual_start_date=candles[0].date,
            actual_end_date=candles[-1].date,
            items=candles,
        )


app.dependency_overrides[get_market_repository] = lambda: FakeRepository()
client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_database_health() -> None:
    response = client.get("/api/health/database")
    assert response.status_code == 200
    assert response.json()["serverVersion"] == "9.6.0"


def test_asset_search_uses_camel_case_contract() -> None:
    response = client.get("/api/assets", params={"query": "600519"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["assetId"] == "stock:SH:600519"
    assert payload["items"][0]["lastDataDate"] == "2026-08-07"


def test_candle_range() -> None:
    response = client.get(
        "/api/assets/stock:SH:600519/candles",
        params={"start": "2026-08-01", "end": "2026-08-07"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["asset"]["symbol"] == "600519"
    assert payload["items"][0]["close"] == 1309.22


def test_rejects_inverted_date_range() -> None:
    response = client.get(
        "/api/assets/stock:SH:600519/candles",
        params={"start": "2026-08-08", "end": "2026-08-07"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_ASSET_ID"


def test_create_get_and_download_composition() -> None:
    response = client.post(
        "/api/compositions",
        json={
            "assetId": ASSET.asset_id,
            "startDate": "2026-08-01",
            "endDate": "2026-08-07",
            "settings": {"bpm": 96, "musicalKey": "C", "scale": "major-pentatonic"},
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert [track["id"] for track in payload["tracks"]] == ["melody", "harmony", "bass"]
    assert payload["tracks"][0]["notes"][0]["candleIndex"] == 0
    assert payload["tracks"][0]["notes"][0]["midi"] in {48, 50, 52, 55, 57, 60, 62, 64, 67, 69, 72, 74, 76, 79, 81, 84}

    composition_id = payload["id"]
    assert client.get(f"/api/compositions/{composition_id}").status_code == 200
    midi = client.get(f"/api/compositions/{composition_id}/midi")
    assert midi.status_code == 200
    assert midi.headers["content-type"] == "audio/midi"
    assert midi.content.startswith(b"MThd")
    assert midi.content[8:10] == b"\x00\x01"


def test_unknown_composition_returns_contract_error() -> None:
    response = client.get("/api/compositions/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "COMPOSITION_NOT_FOUND"
