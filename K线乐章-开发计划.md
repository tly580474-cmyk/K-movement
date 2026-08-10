# K线乐章开发计划

> 项目目标：将股票与指数的 K 线数据映射为可辨识、受音乐理论约束且具备良好视听体验的音乐作品。
>
> 开发方式：采用“前端驱动后端”。先完成高保真界面、Mock 数据与核心交互，再由前端数据模型冻结 API 契约，最后接入 MySQL 和音乐生成引擎。

## 1. 项目现状

项目已经完成前端高保真骨架、Mock 交互、FastAPI 行情服务、MySQL 只读接入及第一轮前后端契约联调。当前页面默认请求真实 API，并保留可通过环境变量启用的 Mock 降级模式。参考图为 1680×945 的深色桌面数据工作台，主要包含：

- 左侧主导航；
- K 线、成交量、RSI、MACD 图表区；
- 旋律可视化与钢琴卷帘；
- 市场信息和音乐生成参数；
- 播放控制条；
- 市场动机/小节列表；
- 乐章结构摘要。

MySQL 已完成只读探查：

- 服务地址：本机 `127.0.0.1:3306`；
- 数据库：`quant_backtest`；
- 账户权限：仅可读取 `quant_backtest`，不能写入项目结果；
- 个股日线：`instruments + daily_bars_v2`，约 1,690 万条；
- 指数日线：`market_datasets + candles`；
- 个股数据覆盖至 2026-08-07；
- 中证2000代码为 `932000`，当前数据覆盖至 2026-08-05；
- `000852` 在指数中代表中证1000，在深市股票中代表石化机械，不能只用代码作为唯一标识。

## 2. 首版目标与边界

### 2.1 首版目标

完成一个可以演示的桌面端 Web MVP：

1. 用户选择股票或指数及日期范围；
2. 页面展示 K 线、成交量和技术指标；
3. 用户调整音乐风格、乐器、BPM、调式和情绪；
4. 系统根据行情生成音符时间轴；
5. 播放时 K 线、音符、钢琴键和小节卡片同步高亮；
6. 用户可以重新生成并导出 MIDI。

### 2.2 首版包含

- 首页完整视觉框架；
- 股票/指数搜索与选择；
- 日 K、成交量、MA5/10/20/60；
- RSI、MACD；
- 钢琴卷帘和播放光标；
- 播放、暂停、跳转、音量；
- 风格、乐器、BPM、调式、情绪参数；
- 市场状态、OHLC、成交量和指标摘要；
- 市场动机/小节卡片；
- MIDI 导出；
- 加载、空数据、错误、数据过期等状态。

### 2.3 首版暂缓

- 社区、用户关注与社交分享；
- 乐谱市场和付费体系；
- AI 自由作曲；
- 分钟级实时行情；
- 复杂 3D 粒子、全屏谱线流体动画；
- 多股票同时编曲；
- WAV/MP3 服务端高质量渲染。

侧栏可保留这些入口以还原设计，但未实现页面必须标记“即将开放”，不能表现成已经可用。

## 3. 前端驱动后端的开发原则

### 3.1 工作顺序

```text
设计令牌与布局骨架
→ 静态高保真首页
→ Mock 数据与交互状态
→ TypeScript 领域模型
→ API 契约冻结
→ FastAPI 实现契约
→ MySQL 行情接入
→ 音乐引擎接入
→ 端到端联调与验收
```

### 3.2 前端先行的交付要求

在后端开始业务实现前，前端必须能够使用 Mock 数据完整演示：

- 搜索并切换标的；
- 切换周期和日期；
- 显示不同市场状态；
- 修改音乐参数并触发生成状态；
- 播放、暂停和拖动进度；
- 同步高亮 K 线、音符和小节；
- 展示加载、失败、无数据和数据过期状态。

Mock 数据不直接散落在组件中，统一由 Mock API 层提供。建议使用 MSW，使 Mock API 与正式 API 共享请求路径和响应类型。

## 4. 推荐技术栈

### 4.1 前端

- React + TypeScript + Vite；
- Tailwind CSS：布局和设计令牌；
- Zustand：播放器、选中标的和生成参数等客户端状态；
- TanStack Query：服务端数据、缓存和请求状态；
- TradingView Lightweight Charts：K 线与成交量；
- ECharts：RSI、MACD、结构图等辅助图表；
- Tone.js：浏览器音频调度与播放；
- Lucide React：统一 SVG 图标；
- MSW：Mock API；
- Vitest + Testing Library：组件和状态测试；
- Playwright：核心流程与视觉回归测试。

### 4.2 后端

- Python + FastAPI；
- SQLAlchemy 2.x；
- PyMySQL 或 asyncmy；
- Pandas + NumPy：行情清洗与指标计算；
- Mido：MIDI 生成；
- music21：后续和声、调式与乐句规则；
- Pytest：数据访问、映射规则与接口测试。

### 4.3 存储

- `quant_backtest`：只读行情来源；
- MVP 生成文件：项目本地 `outputs/`，并加入 `.gitignore`；
- MVP 项目元数据：SQLite；
- 正式版本：独立 `kline_music` 数据库和独立写入账户，不给行情只读账户扩权。

## 5. 前端信息架构

### 5.1 页面布局

```text
AppShell
├── TopHeader
├── SideNavigation
└── DashboardPage
    ├── MainWorkspace
    │   ├── MarketChartPanel
    │   ├── MelodyVisualizerPanel
    │   ├── TransportBar
    │   └── MotifTimeline
    └── InspectorRail
        ├── MarketSummaryPanel
        ├── GenerationSettingsPanel
        └── CompositionStructurePanel
```

### 5.2 核心组件

| 组件 | 职责 | 首版关键状态 |
| --- | --- | --- |
| `AssetSelector` | 搜索并选择股票/指数 | 默认、搜索中、无结果、代码冲突 |
| `MarketChartPanel` | K 线、均线和成交量 | 加载、无数据、区间变化、当前 K 线 |
| `IndicatorStrip` | RSI、MACD | 加载、指标不可用、当前指标值 |
| `PianoRoll` | 音符时间轴与键盘 | 当前音符、悬停、缩放、播放光标 |
| `TransportBar` | 播放与时间控制 | 未生成、缓冲、播放、暂停、结束 |
| `GenerationSettings` | 音乐参数编辑 | 已保存、已修改、生成中、失败 |
| `MarketSummary` | 行情摘要和趋势 | 正常、过期、部分指标缺失 |
| `MotifTimeline` | 展示市场动机和小节 | 当前小节、可跳转、未识别动机 |
| `CompositionStructure` | 乐章结构摘要 | 时长、结构、当前片段 |

### 5.3 响应式策略

首轮开发桌面优先，但组件不能写死为单一分辨率。

- `≥1440px`：完整三栏布局，作为设计稿还原基准；
- `1024px–1439px`：左侧导航收起为图标，右侧信息栏改为抽屉；
- `768px–1023px`：主模块上下排列，播放条固定在底部；
- `<768px`：保留查看和播放能力，复杂参数进入全屏面板，钢琴卷帘允许内部横向滚动；
- 首次视觉验收尺寸：1680×945、1440×900；
- 后续响应式验收尺寸：1024×768、768×1024、390×844。

## 6. 视觉设计系统

### 6.1 视觉方向

- 主题：OLED 深色金融数据工作台；
- 气质：专业、沉浸、音乐化、低光环境友好；
- 主背景：接近黑色的午夜蓝；
- 数据强调：电光蓝、青绿色、紫色；
- 播放焦点：暖金色；
- 效果：克制的描边、内发光和局部辉光，不使用大面积高亮阴影。

### 6.2 建议设计令牌

```css
:root {
  --color-bg-canvas: #020617;
  --color-bg-panel: #07101f;
  --color-bg-elevated: #0b1528;
  --color-border: #1e3352;
  --color-border-active: #5268ff;

  --color-text-primary: #f8fafc;
  --color-text-secondary: #a9b5c8;
  --color-text-muted: #6f7d92;

  --color-blue: #38bdf8;
  --color-indigo: #5b6cff;
  --color-violet: #8b5cf6;
  --color-gold: #f6c768;
  --color-positive: #21d6a2;
  --color-negative: #fb5a78;

  --radius-panel: 10px;
  --radius-control: 8px;
  --motion-fast: 160ms;
  --motion-normal: 240ms;
}
```

最终颜色需通过实际组件对比度检测；正常文字对比度不低于 4.5:1。涨跌不能只依赖红绿，同时使用箭头、正负号或文本标签。

### 6.3 字体与图标

- 中文正文优先使用系统无衬线字体栈；
- 英文与数字可使用 IBM Plex Sans；
- 产品标题可采用更具音乐气质的展示字体，但不能用于小字号数据；
- 全站使用同一套 SVG 图标，禁止使用 Emoji 代替功能图标；
- 图标按钮最小点击区域 44×44px，并提供 `aria-label` 和 Tooltip。

### 6.4 动效规范

- 普通悬停和状态过渡为 150–300ms；
- 主要使用 `transform` 和 `opacity`；
- 播放光标使用独立动画层，避免驱动整个 React 组件树高频重渲染；
- 用户开启 `prefers-reduced-motion` 时关闭粒子、谱线流动和强闪烁效果；
- 发光效果只用于当前播放位置、选中卡片和主要操作。

## 7. 前端状态与领域模型

### 7.1 标的唯一标识

不能仅使用 `symbol`。前端统一使用稳定的 `assetId`：

```ts
type AssetType = 'stock' | 'index' | 'etf';

interface AssetSummary {
  assetId: string;
  sourceId: string;
  market: 'SH' | 'SZ' | 'BJ' | 'GLOBAL';
  symbol: string;
  name: string;
  assetType: AssetType;
  status: 'active' | 'delisted';
  lastDataDate: string | null;
}
```

建议的 `assetId` 示例：

```text
stock:SH:600519
index:dataset:7de97d1e-3d0c-4102-9fd8-c85126568dec
```

### 7.2 播放同步模型

音符必须携带对应 K 线索引：

```ts
interface MusicNote {
  id: string;
  trackId: string;
  midi: number;
  startSeconds: number;
  durationSeconds: number;
  velocity: number;
  candleIndex: number;
  motifId?: string;
}
```

播放器以 `currentTime` 推导 `activeNoteId`、`activeCandleIndex` 和 `activeMotifId`，三个视图不各自维护播放进度。

### 7.3 参数模型

```ts
interface GenerationSettings {
  style: 'orchestral' | 'piano' | 'synth' | 'lofi';
  instruments: string[];
  bpm: number;
  key: string;
  scale: 'major-pentatonic' | 'minor-pentatonic' | 'major' | 'minor';
  mood: 'upward' | 'calm' | 'tense' | 'dark';
  mappingStrength: number;
}
```

## 8. API 契约草案

前端完成 Mock 交互后，以实际类型为准冻结 OpenAPI 契约。

### 8.1 标的搜索

```http
GET /api/assets?query=中证2000&type=index
```

### 8.2 行情查询

```http
GET /api/assets/{assetId}/candles?start=2025-01-01&end=2025-12-31&timeframe=1d
```

响应需包括：

- 统一 OHLCV；
- MA、RSI、MACD、ATR；
- 数据起止日期；
- 最后更新时间；
- 缺失日期和数据质量警告。

### 8.3 生成乐章

```http
POST /api/compositions
```

请求：

```json
{
  "assetId": "stock:SH:600519",
  "startDate": "2025-01-01",
  "endDate": "2025-12-31",
  "settings": {
    "style": "orchestral",
    "instruments": ["piano", "strings", "bass"],
    "bpm": 96,
    "key": "C",
    "scale": "major-pentatonic",
    "mood": "upward",
    "mappingStrength": 0.88
  }
}
```

### 8.4 获取乐章和导出

```http
GET /api/compositions/{id}
GET /api/compositions/{id}/midi
```

生成结果包含市场摘要、音乐元数据、多轨音符、市场动机和 `candleIndex` 映射。

## 9. 后端数据适配方案

```text
MarketCatalog
├── StockCatalog：instruments
└── IndexCatalog：market_datasets

MarketRepository
├── StockBarRepository：daily_bars_v2
└── IndexBarRepository：candles
            ↓
统一 Candle 模型
            ↓
Data Quality + Indicators
            ↓
Music Mapper + Music Grammar
```

### 9.1 个股读取

通过 `instrument_key + trade_date` 查询 `daily_bars_v2`。该组合为主键，当前查询计划能够使用索引。

### 9.2 指数读取

通过 `dataset_id + time` 查询 `candles`。`time` 当前为 ISO 格式字符串 `YYYY-MM-DD`，范围查询可用，但 Repository 层必须转换为日期类型后再向业务层返回。

### 9.3 技术指标

以下指标在服务端按所选区间及预热窗口计算：

- Return；
- K 线实体与上下影线；
- MA5/10/20/60；
- ATR14；
- RSI14；
- MACD 12/26/9；
- 相对成交量；
- 趋势与市场状态。

查询 MA60 等指标时，后端要自动多读取至少 60 个交易日作为预热数据，但只向前端返回用户选定范围。

## 10. 音乐映射 MVP

首版先保持规则可解释和可测试：

| 行情特征 | 音乐参数 | 首版规则 |
| --- | --- | --- |
| 每日收益率 | Pitch | 滚动归一化后吸附至指定音阶 |
| 相对成交量 | Velocity | 映射至 MIDI 力度 45–110 |
| ATR | Duration/密度 | 高波动缩短音符并增加节奏密度 |
| MA20-MA60 | 乐句方向 | 趋势向上/向下改变旋律重心 |
| 阳线/阴线 | 明暗倾向 | 在既定调式内选择稳定音或紧张音 |

默认配置：

- C Major 五声音阶：C、D、E、G、A；
- 音域：C3–C5；
- BPM：96；
- 拍号：4/4；
- 主乐器：Piano；
- 极端值使用分位数截断；
- 同一输入和参数必须生成同一结果。

第二轮再加入和弦进行、量化、乐句、鼓组、多轨编曲和 Market Motif。

## 11. 里程碑与排期

以下为单人全职开发估算，总计约 7–9 周。

### 阶段 A：前端基础与设计系统（2–3 天）

- 初始化 React/TypeScript/Vite；
- 配置 Tailwind、Lint、测试和路径别名；
- 建立设计令牌、字体、图标和基础控件；
- 建立 AppShell、网格布局和响应式骨架。

验收：空白工作台在 1680×945 和 1440×900 下布局稳定，无横向溢出。

### 阶段 B：静态高保真首页（5–7 天）

- 完成导航、页头和全部面板；
- 使用固定 Mock 数据绘制 K 线、指标和钢琴卷帘；
- 还原选中态、描边、阴影、渐变和局部发光；
- 加入 Skeleton、Empty State、Error State。

验收：与参考图完成逐区视觉对比，主要布局、层级、间距和色彩达到可演示水平。

### 阶段 C：Mock 交互原型（5–7 天）

- 引入 MSW 和多组行情 Mock；
- 完成标的切换、参数编辑、生成流程；
- 完成播放、暂停、拖动和音量控制；
- K 线、音符、钢琴键、小节卡片同步高亮；
- 完成键盘操作、焦点和减弱动效。

验收：不依赖后端即可完整演示用户主流程。

### 阶段 D：API 契约与后端骨架（3–4 天）

- 从前端类型生成/整理 OpenAPI 契约；
- 初始化 FastAPI；
- 建立统一错误结构、请求 ID 和日志；
- 前端切换到真实接口但保留 Mock 开关。

验收：Mock 与真实空实现返回结构一致，契约测试通过。

### 阶段 E：MySQL 行情接入（4–6 天）

- 实现股票、指数两个 Catalog 与 Repository；
- 统一标的标识和 Candle 模型；
- 实现范围查询、指标预热和数据质量检查；
- 接入标的搜索、行情和指标接口；
- 对查询耗时和最大日期范围设置限制。

验收：贵州茅台、中证2000、沪深300、创业板指均可查询并正确渲染；代码碰撞不会返回错误标的。

### 阶段 F：音乐引擎 MVP（5–7 天）

- 实现收益率、成交量、ATR 映射；
- 实现音阶吸附、音域限制和确定性生成；
- 输出 Note Timeline JSON 和 MIDI；
- 接入 Tone.js 播放；
- 为映射规则编写单元测试。

验收：四类行情能够生成明显不同的旋律，且所有音符符合调式和音域约束。

### 阶段 G：联调、打磨与交付（5–7 天）

- 完成导出、异常恢复和数据过期提示；
- 优化图表和播放光标性能；
- 完成桌面端、平板和移动端适配；
- 完成视觉回归、端到端、可访问性和性能测试；
- 编写运行、配置和演示文档。

验收：核心流程稳定，播放同步误差目标小于 100ms，浏览器控制台无未处理错误。

## 12. 测试计划

### 12.1 前端

- 组件：参数边界、错误状态、可访问名称；
- 状态：播放器状态机、生成状态、标的切换；
- 图表：空数据、单点数据、长区间；
- E2E：选择标的 → 修改参数 → 生成 → 播放 → 跳转 → 导出；
- 视觉回归：1680×945、1440×900、1024×768；
- 性能：播放时避免每帧触发整页 React 重渲染。

### 12.2 后端

- 股票和指数 Repository；
- 日期范围、代码碰撞、停牌和缺失数据；
- OHLC 合法性和技术指标边界；
- 音阶吸附、音域、力度和时值；
- 相同参数确定性输出；
- API 契约和错误响应。

### 12.3 数据样本

固定以下数据作为回归样本：

- 贵州茅台：`stock:SH:600519`；
- 中证2000：指数代码 `932000`；
- 沪深300：指数代码 `000300`；
- 创业板指：指数代码 `399006`。

## 13. UI 验收清单

- [ ] 1680×945 下主要布局与参考图一致；
- [ ] 所有面板使用统一边框、圆角、间距和标题结构；
- [ ] 正文和数据文本达到最低对比度要求；
- [ ] 涨跌信息不只依赖颜色；
- [ ] 所有可点击元素有指针、悬停、按下和焦点状态；
- [ ] 图标按钮有 Tooltip 和无障碍名称；
- [ ] 交互控件最小点击区域为 44×44px；
- [ ] 加载时预留空间，不出现明显布局跳动；
- [ ] 动效通常为 150–300ms，不使用导致布局变化的悬停缩放；
- [ ] 支持 `prefers-reduced-motion`；
- [ ] 1024px 下无页面级横向滚动；
- [ ] 图表提供可读的数值摘要作为辅助信息；
- [ ] 播放位置在 K 线、钢琴卷帘和小节卡片中一致。

## 14. 风险与应对

| 风险 | 影响 | 应对 |
| --- | --- | --- |
| 视觉稿信息密度过高 | 小屏难以使用 | 桌面优先，右侧栏在中屏改抽屉 |
| 图表与播放器高频更新 | 页面卡顿 | 播放时钟与 React 状态解耦，按需更新活动索引 |
| “像行情”和“好听”冲突 | 音乐体验差 | 提供映射强度，并始终经过音阶与音域约束 |
| 股票代码碰撞 | 查询错误标的 | 全链路使用 `assetId`，禁止仅用 symbol |
| 股票与指数分表 | 接口逻辑分裂 | Repository 统一成 Candle 领域模型 |
| 指数近期数据缺失 | 生成结果误导 | 返回数据质量警告和最后数据日期 |
| 只读账户不能保存结果 | 无法持久化 | MVP 使用 SQLite/文件，正式版使用独立库和写账户 |
| 音色在浏览器中不一致 | 演示听感波动 | 固定授权明确的 SoundFont 和默认音量 |

## 15. 项目完成定义

当以下条件全部满足时，Web MVP 视为完成：

1. 用户可从真实 MySQL 数据中选择股票或指数；
2. K 线、指标、市场摘要与数据质量状态正确显示；
3. 用户可修改音乐参数并生成确定性的音符时间轴；
4. 页面可以稳定播放音乐，并同步高亮 K 线、音符和小节；
5. MIDI 可以成功导出；
6. 四个固定回归标的均通过端到端测试；
7. 主要桌面分辨率完成视觉验收；
8. 空数据、连接失败、生成失败和数据过期均有明确反馈；
9. 所有密钥仅通过环境变量配置，仓库中不存在明文密码；
10. 页面明确标注本项目属于金融数据听觉化实验，不构成投资建议。

## 16. 当前进度与下一迭代

### 16.1 已完成

- [x] 初始化 React、TypeScript、Vite 与 Git 仓库；
- [x] 完成桌面端高保真首页、设计令牌和响应式布局；
- [x] 完成标的选择、日期范围、播放条和参数面板基础交互；
- [x] 移除“策略”和“回测”功能入口；
- [x] 建立统一 `assetId`、行情与指标 TypeScript 类型；
- [x] 建立 FastAPI、SQLAlchemy、PyMySQL 后端骨架；
- [x] 接入个股与指数真实 MySQL 数据；
- [x] 实现 MA、RSI、MACD、ATR、相对成交量、波动率和趋势摘要；
- [x] 将标的搜索、K 线图、指标区和市场摘要切换到真实 API；
- [x] 保留 Mock 开关，并补齐加载、连接失败和数据过期提示；
- [x] 完成后端单元测试、真实数据库集成测试、前端类型检查和生产构建。

### 16.2 音乐引擎 MVP（已完成）

- [x] 冻结 `Composition`、`Track`、`MusicNote`、`Motif` 的前后端契约；
- [x] 实现收益率到音高、相对成交量到力度、ATR 到时值/密度的确定性映射；
- [x] 实现音阶吸附、音域限制、节拍量化和异常值截断；
- [x] 新增 `POST /api/compositions` 与生成结果查询接口；
- [x] 前端接入 Tone.js，以统一播放时钟驱动 K 线、钢琴卷帘和小节卡片；
- [x] 实现 MIDI 生成与下载接口；
- [x] 为映射规则、确定性输出和 MIDI 导出补充测试。
- [x] 根据首轮试听反馈，将单音轨升级为主旋律、自动三和弦与低音三轨编曲；
- [x] 压缩默认时间轴，并通过时值重叠与级进约束改善旋律连贯性；
- [x] 将 MIDI 升级为 Type 1 多轨文件，前端接入采样钢琴和分层音色。
- [x] 扩展轻爵士、史诗影视、国风新民乐、极简氛围和摇滚律动五类行情风格；
- [x] 为新增风格实现独立的节奏密度、和声结构、音色和推荐编制，摇滚风格增加鼓轨。
- [x] 将逐 K 线音符流重构为 16–32 小节的 A–A′–B–A″ 作曲规划；
- [x] 引入节奏型、强弱拍、低活跃休止、关键点重音和乐句末长音；
- [x] 将和声切换对齐小节线，强拍处理为和弦音，并为每段加入 V→I 终止式；
- [x] 实现主题重复、变奏、倒影、B 段音区对比和趋势驱动的大小调选择；
- [x] 为浏览器播放器加入空间混响、延音模拟及更柔和的采样降级音色。
- [x] 为和声加入最近转位、共同音保持、有限声部移动和风格化伴奏节奏；
- [x] 为 Jazz、Ambient、Rock、Cinematic 等风格加入独立低音型，并为 Jazz/Lo-fi 加入 swing；
- [x] 让低活跃小节的旋律、和声、低音及鼓组同步留白；
- [x] 为摇滚鼓组加入段首 crash、段末 tom fill 和活动度变化；
- [x] 将四段终止分为半终止、半终止、伪终止与最终正格终止；
- [x] 让 A″ 直接复现 A 段主题音高，并加入平滑力度曲线、B 段音区对比与弱起。
- [x] 统一 quiet-bar 休止规划，移除逐音静默冲突，并让连奏风格跨小节自然衔接；
- [x] 将 Jazz/Lo-fi swing 扩展到八分与十六分网格，并使用 anticipated syncopation；
- [x] 为 B 段加入同主音大小调转换、加密和声节奏及导音属和弦；
- [x] 增强四声部和弦转位搜索与共同音权重，调整 Jazz walking bass 错位节奏；
- [x] 为钢琴采样加入踏板式长释放，为 Cinematic 加入段首 crash，为国风加入分解和声；
- [x] 将最终小节改为 4 拍主音、持续和弦及踏板低音的完整尾奏。
- [x] 用 A′ 末属和弦到 B 段主和弦的解决引导同主音调式切换，并限制 B 入口跳进；
- [x] 为四声部配器加入音域展开、密集音程与平行五/八度惩罚；
- [x] 建立跨段连续力度曲线，B 前两小节渐强、A″ 前两小节渐弱；
- [x] 统一 Jazz walking bass 为下一根音的下方半音趋近；
- [x] 将 Rock fill 按 A/A′ 与 B/A″ 分级并关联活动度，为 Cinematic 增加定音鼓与 roll；
- [x] 将国风琶音升级为双音织体，并让 Lo-fi 强制使用可 swing 的切分节奏；
- [x] 删除废弃的逐音 quiet 阈值代码，保持单一静默规划来源。

### 16.3 音乐引擎 MVP 验收标准

- 相同标的、日期和参数重复生成的音符完全一致；
- 乐章包含 A–A′–B–A″ 四段结构，和弦起点全部位于小节线上；
- A/A′ 形成半终止，B 形成伪终止，最终 A″ 以 V→I 解决；
- 相邻和弦使用平滑声部进行，伴奏具有风格化节奏，乐句末尾存在分层长音；
- 低活跃行情有 10%–25% 不直接触发旋律音符；
- 所有音符都位于选择的调式与音域内；
- 贵州茅台、中证2000等不同市场样本能生成可辨识的不同旋律；
- 播放时 K 线、当前音符、钢琴键和小节卡片使用同一活动索引；
- 可以下载并在常见 MIDI 播放器中打开生成文件；
- 生成失败、无足够行情、播放初始化失败都有明确的用户提示。
