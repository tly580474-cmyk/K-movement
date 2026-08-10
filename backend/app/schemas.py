from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


AssetType = Literal["stock", "index", "etf"]
MarketCode = Literal["SH", "SZ", "BJ", "GLOBAL"]


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class AssetSummary(ApiModel):
    asset_id: str
    source_id: str
    market: MarketCode
    symbol: str
    name: str
    asset_type: AssetType
    status: Literal["active", "delisted"]
    last_data_date: date | None = None
    last_price: float = 0
    currency: Literal["CNY", "POINT"]
    change: float = 0
    change_percent: float = 0


class AssetSearchResponse(ApiModel):
    items: list[AssetSummary]
    total: int


class Candle(ApiModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None
    amount: float | None = None


class IndicatorPoint(ApiModel):
    date: date
    return_pct: float | None = None
    ma5: float | None = None
    ma10: float | None = None
    ma20: float | None = None
    ma60: float | None = None
    rsi14: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    macd_histogram: float | None = None
    atr14: float | None = None
    relative_volume20: float | None = None


class MarketAnalysis(ApiModel):
    trend_state: Literal["bullish", "bearish", "sideways", "unknown"] = "unknown"
    volatility20: float | None = None
    latest_rsi14: float | None = None
    latest_macd: float | None = None
    latest_atr14: float | None = None
    latest_ma20: float | None = None
    latest_ma60: float | None = None


class CandleSeriesResponse(ApiModel):
    asset: AssetSummary
    timeframe: Literal["1d"] = "1d"
    requested_start_date: date
    requested_end_date: date
    actual_start_date: date | None = None
    actual_end_date: date | None = None
    items: list[Candle]
    indicators: list[IndicatorPoint] = Field(default_factory=list)
    analysis: MarketAnalysis | None = None
    warnings: list[str] = Field(default_factory=list)


MusicStyle = Literal[
    "orchestral",
    "piano",
    "synth",
    "lofi",
    "jazz-lounge",
    "cinematic-epic",
    "chinese-folk",
    "ambient-minimal",
    "pop-rock",
]
MusicScale = Literal["major-pentatonic", "minor-pentatonic", "major", "minor"]
MusicMood = Literal["upward", "calm", "tense", "dark"]


class GenerationSettings(ApiModel):
    style: MusicStyle = "orchestral"
    instruments: list[str] = Field(default_factory=lambda: ["piano", "strings", "bass"])
    bpm: int = Field(default=96, ge=60, le=160)
    musical_key: Literal["C", "A", "G", "D"] = "C"
    scale: MusicScale = "major-pentatonic"
    mood: MusicMood = "upward"
    mapping_strength: float = Field(default=0.88, ge=0, le=1)


class CompositionCreateRequest(ApiModel):
    asset_id: str
    start_date: date
    end_date: date
    settings: GenerationSettings = Field(default_factory=GenerationSettings)


class MusicNote(ApiModel):
    id: str
    track_id: str
    midi: int = Field(ge=0, le=127)
    pitch_name: str
    start_seconds: float = Field(ge=0)
    duration_seconds: float = Field(gt=0)
    velocity: int = Field(ge=1, le=127)
    candle_index: int = Field(ge=0)
    motif_id: str


class MusicTrack(ApiModel):
    id: str
    name: str
    instrument: str
    notes: list[MusicNote]


class MarketMotif(ApiModel):
    id: str
    label: str
    start_candle_index: int
    end_candle_index: int
    start_seconds: float
    end_seconds: float
    title: str
    description: str
    color: Literal["mint", "blue", "violet", "gold"]
    values: list[float]


class Composition(ApiModel):
    id: str
    asset: AssetSummary
    start_date: date
    end_date: date
    settings: GenerationSettings
    time_signature: Literal["4/4"] = "4/4"
    duration_seconds: float
    total_bars: int
    tracks: list[MusicTrack]
    motifs: list[MarketMotif]
    warnings: list[str] = Field(default_factory=list)


class HealthResponse(ApiModel):
    status: Literal["ok"] = "ok"
    service: str
    environment: str


class DatabaseHealthResponse(ApiModel):
    status: Literal["ok"] = "ok"
    database: str
    server_version: str


class ErrorDetail(ApiModel):
    code: str
    message: str
    request_id: str | None = None


class ErrorResponse(ApiModel):
    error: ErrorDetail
