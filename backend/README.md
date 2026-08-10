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

乐章生成接口将行情转换为 16–32 小节的 A–A′–B–A″ 曲式。收益率参与主题轮廓，相对成交量控制力度，ATR/波动率控制节奏密度；低活跃行情形成完整静默小节，关键转折形成重音和长音。A′ 对主题进行变奏，B 段切换同主音大小调、加密和声节奏并使用倒影及高音区对比，A″ 回归主题。

和声按 4/4 小节规划，使用最近转位、共同音保持和有限声部移动连接相邻和弦，并按风格生成 comping 节奏。A/A′ 以半终止形成“逗号”，B 以伪终止制造意外，只有最终 A″ 使用 V→I 正格终止。强拍旋律优先使用当前和弦音，趋势状态会自动选择大小调倾向。所有发声音符保留对应的 `candleIndex`，相同请求仍会得到确定性的乐章 ID 与音符结果。

MIDI 导出采用 Type 1 多轨格式，包含指挥轨、主旋律、自动和声和低音轨，可在常见 DAW 或制谱软件中分别编辑。

生成风格不仅是展示标签：轻爵士使用七和弦、统一网格 swing comping 与错位 walking bass；Lo-fi 使用轻摇摆；史诗风扩大力度、音域、使用低音级进并在段首加入 crash；国风使用五声音阶分解和声；极简氛围使用踏板低音和长延音；摇滚使用根音—五度—八度低音，并在段首加入 crash、段尾加入 tom fill。最终小节由 4 拍主音、持续和弦和踏板低音共同收束。低活跃小节会让旋律、和声、低音及鼓组同步呼吸。浏览器播放器加入风格化混响和钢琴踏板式释放，采样失败时使用柔和包络降级。

当前乐章存储属于 MVP 进程内缓存，后端重启后需要重新生成。

## 测试

```powershell
cd backend
python -m pytest -q
```

提供 `MYSQL_PASSWORD` 时会额外执行真实数据库集成测试；未提供时自动跳过。
