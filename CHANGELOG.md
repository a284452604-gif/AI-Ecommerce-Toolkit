# 变更日志

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
