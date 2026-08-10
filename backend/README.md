# K线乐章后端

FastAPI 行情与音乐生成服务。行情部分只读访问 MySQL 中分开存储的股票和指数数据；生成结果当前保存在进程内存中，并可导出 MIDI。

## 配置

从仓库根目录复制环境变量模板：

```powershell
Copy-Item .env.example .env
```

填写本地 `MYSQL_PASSWORD`。`.env` 已被 Git 忽略，禁止提交真实密码。

## 启动

```powershell
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

接口文档：`http://127.0.0.1:8000/docs`

## 接口

- `GET /api/health`
- `GET /api/health/database`
- `GET /api/assets?query=600519&type=stock`
- `GET /api/assets/{assetId}/candles?start=2026-01-01&end=2026-08-07`
- `POST /api/compositions`
- `GET /api/compositions/{compositionId}`
- `GET /api/compositions/{compositionId}/midi`

行情响应同时包含逐日 MA5/10/20/60、RSI14、MACD、ATR14、相对成交量，以及最新波动率和趋势状态。服务会自动读取额外预热数据，但仅返回用户指定日期范围。

乐章生成接口使用行情收益率、相对成交量和 ATR 生成确定性音符序列。所有音符携带对应的 `candleIndex`，并受到所选调式、MIDI 音域和力度范围约束。旋律经过级进约束和连奏处理，并自动补全三和弦和声及根音/五度低音。相同请求会得到相同的乐章 ID 与音符结果。

MIDI 导出采用 Type 1 多轨格式，包含指挥轨、主旋律、自动和声和低音轨，可在常见 DAW 或制谱软件中分别编辑。

当前乐章存储属于 MVP 进程内缓存，后端重启后需要重新生成。

## 测试

```powershell
cd backend
python -m pytest -q
```

提供 `MYSQL_PASSWORD` 时会额外执行真实数据库集成测试；未提供时自动跳过。
