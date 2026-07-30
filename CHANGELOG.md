# 变更日志

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
