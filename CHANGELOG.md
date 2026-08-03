# 变更日志

## [1.2.2] - 2026-08-03

### 修复
- **优化历史加载报错（数据库列顺序错位）**
  - 旧版数据库经 `ALTER TABLE` 迁移后，`keyword_layout` 字段被追加到末尾（index 12），而 `_row_to_dict` 按固定位置读取（假设在 index 7），导致 `product_info` 被错误指向 `created_at` 日期串，`json.loads` 解析失败并抛出 `Extra data`，整段历史无法加载
  - 改用 `sqlite3.Row` 行工厂，所有字段按**列名**访问，彻底消除迁移带来的列顺序错位问题
  - JSON 字段解析增加容错：单条脏数据降级为默认值（`[]` / `{}`），不再拖垮整个历史列表
  - 新增 2 个回归测试（迁移后列顺序、脏 JSON 健壮性）

## [1.2.0] - 2026-08-01

### 新增
- **标题优化支持平台数据截图 + 搜索词榜单数据**
  - AI 服务接口扩展：支持传入本地图片路径，自动转 base64 随 prompt 发送
  - 新增「数据驱动优化」风格，结合搜索人气/搜索增速/搜索增量等榜单数据生成标题
  - 标题优化页新增「平台市场数据」区域：
    - 上传平台数据截图（JPG/PNG 等），AI 结合图片与表格数据优化
    - 可编辑的搜索词榜单表格：榜单类型、搜索词、搜索人气、趋势词、搜索增速、核心词、搜索增量、修饰词
  - 优化结果新增「关键词布局」展示，并持久化到数据库
  - 数据导出（Excel/CSV/预览）同步增加「关键词布局」列

## [1.1.0] - 2026-07-30

### 新增
- **Playwright 浏览器抓取（V1.1 核心）**
  - 新增 `apps/product_analyzer/browser_scraper.py`：基于真实 Chromium 渲染 JS 页面
  - 自动降级：httpx 拿不到核心数据时，自动改用浏览器抓取
  - 浏览器实例懒加载单例复用，降低每条链接启动开销
  - 登录页/验证页识别，避免把登录页误判为成功
  - 按平台注入登录 Cookie（淘宝/天猫/京东/拼多多/抖音），绕过登录限制获取价格、店铺
  - `settings` 页新增「商品抓取设置」分组：浏览器抓取开关 + 各平台 Cookie 输入
- 依赖新增：`playwright`（Python 包）+ 下载 Chromium 浏览器二进制

### 改进
- 商品抓取失败提示更明确（区分反爬/登录/空页面等场景）
- 默认配置 `scraper.browser_enabled = true`

### 测试
- 新增 `tests/test_browser_scraper.py`：Cookie 解析、平台域名映射、可用性检查
- 全部测试 30/30 通过

## [1.0.0] - 2026-07-30

### 新增
- **SQLite 数据持久化**（database/db_manager.py）
  - DatabaseManager 单例，线程安全
  - 分析记录表 (analysis_history)：平台、商品ID、标题、价格、店铺等
  - 优化记录表 (optimization_history)：原标题、优化标题、风格、SEO关键词等
  - WAL 模式、索引优化、CRUD 完整接口
- **数据导出模块**（apps/data_export）
  - 支持导出分析记录和优化记录
  - Excel (.xlsx) 格式导出（openpyxl，带样式）
  - CSV (.csv) 格式导出（UTF-8 BOM 编码）
  - 日期范围、平台/风格筛选
  - 数据预览表格
- **批量链接分析**（apps/product_analyzer/batch_scrape_worker.py）
  - BatchScrapeWorker：多 URL 队列式异步分析
  - 进度追踪、逐个结果实时更新
  - 批量结果汇总表格
- **多标题批量优化**（apps/title_optimizer/multi_title_worker.py）
  - MultiTitleOptimizeWorker：多标题队列式 AI 优化
  - 进度追踪、Token 用量统计
  - 批量结果汇总表格
- **历史记录管理页面**（apps/history）
  - 统一管理分析/优化历史
  - 标签页切换（分析记录 / 优化记录）
  - 搜索、平台/风格筛选
  - 批量删除、清空全部
- **首页仪表盘升级**
  - 实时统计数据条：分析次数、优化次数、今日分析、今日优化
  - 功能卡片更新：历史记录、数据导出 → "可用"

### 变更
- 版本号升级至 1.0.0
- AppContext 新增 `db` 属性，自动管理 DatabaseManager 生命周期
- ProductAnalyzerPage：分析结果自动保存到 SQLite，on_show 时从 DB 加载历史
- TitleOptimizerPage：优化结果自动保存到 SQLite，on_show 时从 DB 加载历史
- requirements.txt 新增 openpyxl>=3.1.0
- 导航栏新增「历史记录」「数据导出」两个入口

## [0.3.0] - 2026-07-30

### 新增
- AI 标题优化模块（apps/title_optimizer）
- AI 服务层：BaseAIService 抽象基类 + DeepSeek 适配器（OpenAI SDK 兼容）
- AI 服务管理器：工厂模式创建 AI 服务实例
- 标题优化器：三种优化风格（搜索优化、促销转化、品牌调性）
- 标题优化页面：标题输入、风格选择、单次/批量优化、结果对比展示
- QThread 异步 AI 调用：避免 UI 阻塞
- 优化结果展示卡片：前后对比 + SEO 关键词 + 优化理由
- 商品分析页面联动：一键将商品标题发送到 AI 优化
- SignalBus 新增 title_optimize_request 信号实现跨页面通信

### 变更
- 版本号升级至 0.3.0
- requirements.txt 新增 openai 依赖（DeepSeek 兼容 OpenAI SDK）
- 默认配置新增 DeepSeek API 默认值
- 首页"AI标题优化"卡片状态更新为"可用"

## [0.2.0] - 2026-07-30

### 新增
- 商品链接分析模块（apps/product_analyzer）
- 链接解析器：支持淘宝、天猫、京东、拼多多、抖音五大平台链接识别与商品ID提取
- 商品数据抓取器：httpx + BeautifulSoup4 异步抓取商品页面信息（标题、价格、图片、店铺）
- 商品分析页面：链接输入、分析按钮、结果展示卡片、历史记录表格
- QThread 异步抓取：避免网络请求阻塞 UI
- 分析历史记录：本地缓存已分析的商品链接

### 变更
- 版本号升级至 0.2.0
- requirements.txt 新增 httpx、beautifulsoup4、lxml 依赖
- 首页"AI商品分析"卡片状态更新为"已上线"

## [0.1.0] - 2026-07-30

### 新增
- 应用框架基础架构（launcher, framework, apps, components）
- 主窗口与现代侧边栏导航
- 首页仪表盘（占位功能卡片）
- 系统设置页面（AI服务配置占位、外观、日志设置）
- 关于页面（版本信息、技术栈）
- 配置管理系统（JSON，默认配置 + 用户配置合并）
- 日志系统（RotatingFileHandler，文件轮转）
- QSS 现代样式表
- 版本管理（VERSION 文件）
- Windows 启动脚本（run.bat）与打包脚本（build.bat）
- 基础测试套件（ConfigManager, LogManager）
