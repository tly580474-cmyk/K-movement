from math import sqrt
from statistics import pstdev

from .schemas import Candle, IndicatorPoint, MarketAnalysis


def _moving_average(values: list[float], window: int) -> list[float | None]:
    result: list[float | None] = []
    running = 0.0
    for index, value in enumerate(values):
        running += value
        if index >= window:
            running -= values[index - window]
        result.append(running / window if index >= window - 1 else None)
    return result


def _ema(values: list[float], period: int) -> list[float]:
    if not values:
        return []
    alpha = 2 / (period + 1)
    result = [values[0]]
    for value in values[1:]:
        result.append(alpha * value + (1 - alpha) * result[-1])
    return result


def _rsi(values: list[float], period: int = 14) -> list[float | None]:
    result: list[float | None] = [None] * len(values)
    if len(values) <= period:
        return result

    gains: list[float] = []
    losses: list[float] = []
    for index in range(1, len(values)):
        change = values[index] - values[index - 1]
        gains.append(max(change, 0))
        losses.append(max(-change, 0))

    average_gain = sum(gains[:period]) / period
    average_loss = sum(losses[:period]) / period
    result[period] = 100 if average_loss == 0 else 100 - 100 / (1 + average_gain / average_loss)
    for index in range(period + 1, len(values)):
        average_gain = (average_gain * (period - 1) + gains[index - 1]) / period
        average_loss = (average_loss * (period - 1) + losses[index - 1]) / period
        result[index] = 100 if average_loss == 0 else 100 - 100 / (1 + average_gain / average_loss)
    return result


def _atr(candles: list[Candle], period: int = 14) -> list[float | None]:
    true_ranges: list[float] = []
    for index, candle in enumerate(candles):
        if index == 0:
            true_ranges.append(candle.high - candle.low)
            continue
        previous_close = candles[index - 1].close
        true_ranges.append(
            max(
                candle.high - candle.low,
                abs(candle.high - previous_close),
                abs(candle.low - previous_close),
            )
        )

    result: list[float | None] = [None] * len(candles)
    if len(true_ranges) < period:
        return result
    current = sum(true_ranges[:period]) / period
    result[period - 1] = current
    for index in range(period, len(true_ranges)):
        current = (current * (period - 1) + true_ranges[index]) / period
        result[index] = current
    return result


def calculate_indicators(candles: list[Candle]) -> tuple[list[IndicatorPoint], MarketAnalysis]:
    if not candles:
        return [], MarketAnalysis()

    closes = [candle.close for candle in candles]
    volumes = [float(candle.volume or 0) for candle in candles]
    ma5 = _moving_average(closes, 5)
    ma10 = _moving_average(closes, 10)
    ma20 = _moving_average(closes, 20)
    ma60 = _moving_average(closes, 60)
    volume_ma20 = _moving_average(volumes, 20)
    rsi14 = _rsi(closes)
    atr14 = _atr(candles)
    ema12 = _ema(closes, 12)
    ema26 = _ema(closes, 26)
    macd = [fast - slow for fast, slow in zip(ema12, ema26, strict=True)]
    signal = _ema(macd, 9)
    histogram = [(value - signal_value) * 2 for value, signal_value in zip(macd, signal, strict=True)]

    returns: list[float | None] = [None]
    for index in range(1, len(closes)):
        previous = closes[index - 1]
        returns.append((closes[index] / previous - 1) * 100 if previous else None)

    points: list[IndicatorPoint] = []
    for index, candle in enumerate(candles):
        average_volume = volume_ma20[index]
        points.append(
            IndicatorPoint(
                date=candle.date,
                return_pct=returns[index],
                ma5=ma5[index], ma10=ma10[index], ma20=ma20[index], ma60=ma60[index],
                rsi14=rsi14[index],
                macd=macd[index], macd_signal=signal[index], macd_histogram=histogram[index],
                atr14=atr14[index],
                relative_volume20=(volumes[index] / average_volume if average_volume else None),
            )
        )

    recent_returns = [value for value in returns[-20:] if value is not None]
    volatility = pstdev(recent_returns) * sqrt(252) if len(recent_returns) >= 2 else None
    latest = points[-1]
    if latest.ma20 is None or latest.ma60 is None:
        trend_state = "unknown"
    elif latest.ma20 > latest.ma60 * 1.002:
        trend_state = "bullish"
    elif latest.ma20 < latest.ma60 * 0.998:
        trend_state = "bearish"
    else:
        trend_state = "sideways"

    analysis = MarketAnalysis(
        trend_state=trend_state,
        volatility20=volatility,
        latest_rsi14=latest.rsi14,
        latest_macd=latest.macd,
        latest_atr14=latest.atr14,
        latest_ma20=latest.ma20,
        latest_ma60=latest.ma60,
    )
    return points, analysis
