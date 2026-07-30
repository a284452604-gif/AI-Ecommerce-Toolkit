# 变更日志

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
