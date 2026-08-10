from datetime import date
from uuid import uuid4

from fastapi import Depends, FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from sqlalchemy.exc import SQLAlchemyError

from .compositions import CompositionNotFoundError, composition_store
from .config import get_settings
from .midi import composition_to_midi
from .music import CompositionGenerationError
from .repository import (
    AssetNotFoundError,
    InvalidAssetIdError,
    MarketRepository,
    get_market_repository,
)
from .schemas import (
    AssetSearchResponse,
    AssetType,
    CandleSeriesResponse,
    Composition,
    CompositionCreateRequest,
    DatabaseHealthResponse,
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
)

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="K线乐章行情与音乐生成 API",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _error_response(request: Request, status_code: int, code: str, message: str) -> JSONResponse:
    request_id = request.headers.get("x-request-id") or str(uuid4())
    payload = ErrorResponse(error=ErrorDetail(code=code, message=message, request_id=request_id))
    return JSONResponse(status_code=status_code, content=payload.model_dump(by_alias=True))


@app.exception_handler(AssetNotFoundError)
async def asset_not_found_handler(request: Request, exception: AssetNotFoundError) -> JSONResponse:
    return _error_response(request, 404, "ASSET_NOT_FOUND", str(exception))


@app.exception_handler(InvalidAssetIdError)
async def invalid_asset_handler(request: Request, exception: InvalidAssetIdError) -> JSONResponse:
    return _error_response(request, 422, "INVALID_ASSET_ID", str(exception))


@app.exception_handler(CompositionGenerationError)
async def composition_generation_handler(request: Request, exception: CompositionGenerationError) -> JSONResponse:
    return _error_response(request, 422, "COMPOSITION_GENERATION_FAILED", str(exception))


@app.exception_handler(CompositionNotFoundError)
async def composition_not_found_handler(request: Request, exception: CompositionNotFoundError) -> JSONResponse:
    return _error_response(request, 404, "COMPOSITION_NOT_FOUND", str(exception))


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(request: Request, _: SQLAlchemyError) -> JSONResponse:
    return _error_response(request, 503, "DATABASE_UNAVAILABLE", "行情数据库暂时不可用")


@app.exception_handler(RuntimeError)
async def configuration_error_handler(request: Request, exception: RuntimeError) -> JSONResponse:
    return _error_response(request, 503, "SERVICE_NOT_CONFIGURED", str(exception))


@app.get("/api/health", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    return HealthResponse(service=settings.app_name, environment=settings.app_environment)


@app.get("/api/health/database", response_model=DatabaseHealthResponse, tags=["health"])
def database_health(
    repository: MarketRepository = Depends(get_market_repository),
) -> DatabaseHealthResponse:
    version = repository.ping()
    return DatabaseHealthResponse(database=settings.mysql_database, server_version=version)


@app.get(
    "/api/assets",
    response_model=AssetSearchResponse,
    responses={503: {"model": ErrorResponse}},
    tags=["market"],
)
def search_assets(
    query: str = Query(default="", max_length=64),
    asset_type: AssetType | None = Query(default=None, alias="type"),
    limit: int = Query(default=20, ge=1, le=100),
    repository: MarketRepository = Depends(get_market_repository),
) -> AssetSearchResponse:
    return repository.search_assets(query=query, asset_type=asset_type, limit=limit)


@app.get(
    "/api/assets/{asset_id:path}/candles",
    response_model=CandleSeriesResponse,
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
    tags=["market"],
)
def get_candles(
    asset_id: str,
    start: date = Query(...),
    end: date = Query(...),
    timeframe: str = Query(default="1d", pattern="^1d$"),
    repository: MarketRepository = Depends(get_market_repository),
) -> CandleSeriesResponse:
    del timeframe
    if start > end:
        raise InvalidAssetIdError("开始日期不能晚于结束日期")
    if (end - start).days > 8000:
        raise InvalidAssetIdError("单次查询日期范围不能超过 8000 天")
    return repository.get_candles(asset_id=asset_id, start=start, end=end)


@app.post(
    "/api/compositions",
    response_model=Composition,
    status_code=201,
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
    tags=["music"],
)
def create_composition(
    payload: CompositionCreateRequest,
    repository: MarketRepository = Depends(get_market_repository),
) -> Composition:
    if payload.start_date > payload.end_date:
        raise CompositionGenerationError("开始日期不能晚于结束日期")
    return composition_store.create(payload, repository)


@app.get(
    "/api/compositions/{composition_id}",
    response_model=Composition,
    responses={404: {"model": ErrorResponse}},
    tags=["music"],
)
def get_composition(composition_id: str) -> Composition:
    return composition_store.get(composition_id)


@app.get(
    "/api/compositions/{composition_id}/midi",
    responses={404: {"model": ErrorResponse}},
    tags=["music"],
)
def download_composition_midi(composition_id: str) -> Response:
    composition = composition_store.get(composition_id)
    filename = f"kline-melody-{composition.asset.symbol}-{composition.id}.mid"
    return Response(
        content=composition_to_midi(composition),
        media_type="audio/midi",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
