from datetime import date, timedelta

from app.indicators import calculate_indicators
from app.schemas import Candle


def test_indicator_lengths_and_latest_analysis() -> None:
    candles = [
        Candle(
            date=date(2026, 1, 1) + timedelta(days=index),
            open=100 + index,
            high=102 + index,
            low=99 + index,
            close=101 + index,
            volume=1000 + index * 10,
        )
        for index in range(80)
    ]

    points, analysis = calculate_indicators(candles)

    assert len(points) == len(candles)
    assert points[-1].ma5 == 178
    assert points[-1].ma60 == 150.5
    assert points[-1].rsi14 == 100
    assert points[-1].atr14 is not None
    assert analysis.trend_state == "bullish"
    assert analysis.latest_ma20 == points[-1].ma20
