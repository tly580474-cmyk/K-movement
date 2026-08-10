from datetime import date, timedelta
from typing import Any

from sqlalchemy import Engine, text

from .database import get_engine
from .indicators import calculate_indicators
from .schemas import AssetSearchResponse, AssetSummary, AssetType, Candle, CandleSeriesResponse


class AssetNotFoundError(LookupError):
    pass


class InvalidAssetIdError(ValueError):
    pass


def _index_market(symbol: str) -> str:
    if symbol in {"NDX"} or not symbol.isdigit():
        return "GLOBAL"
    if symbol.startswith("399"):
        return "SZ"
    return "SH"


def _change_values(close: float | None, previous_close: float | None) -> tuple[float, float]:
    if close is None or previous_close in (None, 0):
        return 0.0, 0.0
    change = close - previous_close
    return change, change / previous_close * 100


class MarketRepository:
    def __init__(self, engine: Engine):
        self.engine = engine

    def ping(self) -> str:
        with self.engine.connect() as connection:
            return str(connection.execute(text("SELECT VERSION()")).scalar_one())

    def search_assets(
        self,
        query: str = "",
        asset_type: AssetType | None = None,
        limit: int = 20,
    ) -> AssetSearchResponse:
        items: list[AssetSummary] = []
        if asset_type in (None, "stock", "etf"):
            items.extend(self._search_instruments(query, asset_type, limit))
        if asset_type in (None, "index"):
            items.extend(self._search_indices(query, limit))

        keyword = query.strip().lower()
        items.sort(
            key=lambda asset: (
                0 if asset.symbol.lower() == keyword else 1,
                0 if keyword and keyword in asset.name.lower() else 1,
                asset.symbol,
                asset.name,
            )
        )
        selected = items[:limit]
        return AssetSearchResponse(items=selected, total=len(selected))

    def get_candles(self, asset_id: str, start: date, end: date) -> CandleSeriesResponse:
        if asset_id.startswith("index:dataset:"):
            return self._get_index_candles(asset_id, start, end)

        parts = asset_id.split(":")
        if len(parts) == 3 and parts[0] in {"stock", "etf"}:
            return self._get_instrument_candles(parts[0], parts[1], parts[2], start, end)
        raise InvalidAssetIdError(f"不支持的 assetId：{asset_id}")

    def _search_instruments(
        self,
        query: str,
        asset_type: AssetType | None,
        limit: int,
    ) -> list[AssetSummary]:
        type_clause = "i.type IN ('stock', 'etf')" if asset_type is None else "i.type = :asset_type"
        statement = text(
            f"""
            SELECT
                i.instrument_key, i.market, i.symbol, i.name, i.type, i.status,
                (SELECT b.trade_date FROM daily_bars_v2 b
                 WHERE b.instrument_key = i.instrument_key
                 ORDER BY b.trade_date DESC LIMIT 1) AS last_date,
                (SELECT b.close FROM daily_bars_v2 b
                 WHERE b.instrument_key = i.instrument_key
                 ORDER BY b.trade_date DESC LIMIT 1) AS last_close,
                (SELECT b.previous_close FROM daily_bars_v2 b
                 WHERE b.instrument_key = i.instrument_key
                 ORDER BY b.trade_date DESC LIMIT 1) AS previous_close
            FROM instruments i
            WHERE i.status = 'active'
              AND {type_clause}
              AND (:query = '' OR i.symbol LIKE :pattern OR i.name LIKE :pattern)
            ORDER BY
              CASE WHEN i.symbol = :query THEN 0 ELSE 1 END,
              i.symbol
            LIMIT :limit
            """
        )
        params = {
            "query": query.strip(),
            "pattern": f"%{query.strip()}%",
            "asset_type": asset_type,
            "limit": limit,
        }
        with self.engine.connect() as connection:
            rows = connection.execute(statement, params).mappings().all()
        return [self._instrument_asset(row) for row in rows]

    def _search_indices(self, query: str, limit: int) -> list[AssetSummary]:
        statement = text(
            """
            SELECT
                d.id, d.symbol, d.name,
                (SELECT c.time FROM candles c WHERE c.dataset_id = d.id
                 ORDER BY c.time DESC LIMIT 1) AS last_date,
                (SELECT c.close FROM candles c WHERE c.dataset_id = d.id
                 ORDER BY c.time DESC LIMIT 1) AS last_close,
                (SELECT c.change FROM candles c WHERE c.dataset_id = d.id
                 ORDER BY c.time DESC LIMIT 1) AS last_change,
                (SELECT c.change_percent FROM candles c WHERE c.dataset_id = d.id
                 ORDER BY c.time DESC LIMIT 1) AS change_percent
            FROM market_datasets d
            WHERE d.asset_type = 'index'
              AND (:query = '' OR d.symbol LIKE :pattern OR d.name LIKE :pattern)
            ORDER BY
              CASE WHEN d.symbol = :query THEN 0 ELSE 1 END,
              d.symbol
            LIMIT :limit
            """
        )
        params = {"query": query.strip(), "pattern": f"%{query.strip()}%", "limit": limit}
        with self.engine.connect() as connection:
            rows = connection.execute(statement, params).mappings().all()

        results: list[AssetSummary] = []
        for row in rows:
            close = float(row["last_close"] or 0)
            change = float(row["last_change"] or 0)
            percentage = float(row["change_percent"] or 0)
            results.append(
                AssetSummary(
                    asset_id=f"index:dataset:{row['id']}",
                    source_id=str(row["id"]),
                    market=_index_market(str(row["symbol"])),
                    symbol=str(row["symbol"]),
                    name=str(row["name"]),
                    asset_type="index",
                    status="active",
                    last_data_date=row["last_date"],
                    last_price=close,
                    currency="POINT",
                    change=change,
                    change_percent=percentage,
                )
            )
        return results

    @staticmethod
    def _instrument_asset(row: Any) -> AssetSummary:
        close = float(row["last_close"] or 0)
        previous_close = float(row["previous_close"] or 0)
        change, percentage = _change_values(close, previous_close)
        asset_type = str(row["type"])
        return AssetSummary(
            asset_id=f"{asset_type}:{row['market']}:{row['symbol']}",
            source_id=str(row["instrument_key"]),
            market=str(row["market"]),
            symbol=str(row["symbol"]),
            name=str(row["name"]),
            asset_type=asset_type,
            status=str(row["status"]),
            last_data_date=row["last_date"],
            last_price=close,
            currency="CNY",
            change=change,
            change_percent=percentage,
        )

    def _get_instrument_candles(
        self,
        asset_type: str,
        market: str,
        symbol: str,
        start: date,
        end: date,
    ) -> CandleSeriesResponse:
        metadata_statement = text(
            """
            SELECT instrument_key, market, symbol, name, type, status
            FROM instruments
            WHERE market = :market AND symbol = :symbol AND type = :asset_type
            LIMIT 1
            """
        )
        candle_statement = text(
            """
            SELECT trade_date, open, high, low, close, volume, amount, previous_close
            FROM daily_bars_v2
            WHERE instrument_key = :instrument_key
              AND trade_date BETWEEN :start_date AND :end_date
            ORDER BY trade_date
            """
        )
        with self.engine.connect() as connection:
            metadata = connection.execute(
                metadata_statement,
                {"market": market, "symbol": symbol, "asset_type": asset_type},
            ).mappings().first()
            if metadata is None:
                raise AssetNotFoundError(f"未找到标的：{asset_type}:{market}:{symbol}")
            rows = connection.execute(
                candle_statement,
                {
                    "instrument_key": metadata["instrument_key"],
                    "start_date": start - timedelta(days=150),
                    "end_date": end,
                },
            ).mappings().all()

        candles = [
            Candle(
                date=row["trade_date"],
                open=row["open"], high=row["high"], low=row["low"], close=row["close"],
                volume=row["volume"], amount=row["amount"],
            )
            for row in rows
        ]
        latest = rows[-1] if rows else None
        asset_row = dict(metadata)
        asset_row.update(
            last_date=latest["trade_date"] if latest else None,
            last_close=latest["close"] if latest else 0,
            previous_close=latest["previous_close"] if latest else 0,
        )
        return self._series_response(self._instrument_asset(asset_row), candles, start, end)

    def _get_index_candles(self, asset_id: str, start: date, end: date) -> CandleSeriesResponse:
        dataset_id = asset_id.removeprefix("index:dataset:")
        if not dataset_id:
            raise InvalidAssetIdError("指数 assetId 缺少 dataset id")

        metadata_statement = text(
            """
            SELECT id, symbol, name FROM market_datasets
            WHERE id = :dataset_id AND asset_type = 'index' LIMIT 1
            """
        )
        candle_statement = text(
            """
            SELECT c.time, c.open, c.high, c.low, c.close, c.volume, c.turnover,
                   c.`change` AS price_change, c.change_percent
            FROM candles c
            WHERE c.dataset_id = :dataset_id AND c.time BETWEEN :start_date AND :end_date
            ORDER BY c.time
            """
        )
        with self.engine.connect() as connection:
            metadata = connection.execute(metadata_statement, {"dataset_id": dataset_id}).mappings().first()
            if metadata is None:
                raise AssetNotFoundError(f"未找到指数数据集：{dataset_id}")
            rows = connection.execute(
                candle_statement,
                {
                    "dataset_id": dataset_id,
                    "start_date": (start - timedelta(days=150)).isoformat(),
                    "end_date": end.isoformat(),
                },
            ).mappings().all()

        candles = [
            Candle(
                date=date.fromisoformat(str(row["time"])),
                open=row["open"], high=row["high"], low=row["low"], close=row["close"],
                volume=row["volume"], amount=row["turnover"],
            )
            for row in rows
        ]
        latest = rows[-1] if rows else None
        asset = AssetSummary(
            asset_id=asset_id,
            source_id=str(metadata["id"]),
            market=_index_market(str(metadata["symbol"])),
            symbol=str(metadata["symbol"]),
            name=str(metadata["name"]),
            asset_type="index",
            status="active",
            last_data_date=date.fromisoformat(str(latest["time"])) if latest else None,
            last_price=float(latest["close"] if latest else 0),
            currency="POINT",
            change=float(latest["price_change"] or 0) if latest else 0,
            change_percent=float(latest["change_percent"] or 0) if latest else 0,
        )
        return self._series_response(asset, candles, start, end)

    @staticmethod
    def _series_response(
        asset: AssetSummary,
        candles: list[Candle],
        start: date,
        end: date,
    ) -> CandleSeriesResponse:
        indicator_points, analysis = calculate_indicators(candles)
        selected_pairs = [
            (candle, indicator)
            for candle, indicator in zip(candles, indicator_points, strict=True)
            if candle.date >= start
        ]
        selected_candles = [pair[0] for pair in selected_pairs]
        selected_indicators = [pair[1] for pair in selected_pairs]

        warnings: list[str] = []
        if not selected_candles:
            warnings.append("所选日期范围内没有行情数据")
        elif selected_candles[-1].date < end:
            warnings.append(f"行情数据仅更新至 {selected_candles[-1].date.isoformat()}")
        return CandleSeriesResponse(
            asset=asset,
            requested_start_date=start,
            requested_end_date=end,
            actual_start_date=selected_candles[0].date if selected_candles else None,
            actual_end_date=selected_candles[-1].date if selected_candles else None,
            items=selected_candles,
            indicators=selected_indicators,
            analysis=analysis,
            warnings=warnings,
        )


def get_market_repository() -> MarketRepository:
    return MarketRepository(get_engine())
