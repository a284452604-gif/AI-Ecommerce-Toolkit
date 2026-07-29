# AI电商工具箱 - 架构说明

## 概述

AI电商工具箱是一个基于 PySide6 的 Python 桌面应用，采用三层分层架构，为电商运营提供 AI 驱动的工具集。

## 架构分层

```
┌─────────────────────────────────────────────┐
│              launcher/ (入口层)              │
│   创建 QApplication, 初始化 AppContext       │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│          framework/ (框架层)                 │
│   MainWindow + NavigationManager            │
│   ┌─────────────┐  ┌──────────────────────┐│
│   │ components/  │  │  apps/ (功能页面)     ││
│   │ Sidebar      │  │  HomePage            ││
│   │ NavItem      │  │  SettingsPage        ││
│   │ CardWidget   │  │  AboutPage           ││
│   └─────────────┘  └──────────────────────┘│
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│     framework/ (服务层)                      │
│   ConfigManager  LogManager  SignalBus      │
│   AppContext     BasePage     BaseService   │
└─────────────────────────────────────────────┘
```

## 核心设计

### 1. AppContext 单例模式

`AppContext` 是应用全局上下文，持有所有核心 Manager 实例。在应用启动时调用 `initialize()` 初始化，之后全局通过 `AppContext()` 访问。

```python
context = AppContext()
context.initialize(app_dir)
config = context.config      # ConfigManager
logger = context.logger      # LogManager
signals = context.signals    # SignalBus
```

### 2. SignalBus 信号总线

`SignalBus` 集中定义所有跨组件通信信号，组件之间不直接 import 对方，实现松耦合。

```python
class SignalBus(QObject):
    navigate_to = Signal(str)        # 请求切换页面
    page_changed = Signal(str)       # 页面已切换
    config_changed = Signal(str, object)  # 配置变更
    config_saved = Signal()          # 配置已保存
    theme_changed = Signal(str)      # 主题切换
    app_ready = Signal()             # 应用就绪
    app_closing = Signal()           # 应用关闭
    status_message = Signal(str)     # 状态栏消息
```

### 3. BasePage 页面基类

所有功能页面继承 `BasePage`，实现统一的生命周期管理：

- `__init__(page_key, title, icon)` — 构造
- `initialize()` — 调用 `_setup_ui()` + `_setup_connections()`
- `on_show()` / `on_hide()` — 页面显示/隐藏回调

### 4. NavigationManager 导航管理

管理 `QStackedWidget` 中的页面注册与切换，与 Sidebar UI 完全解耦。

### 5. ConfigManager 配置管理

- `default_config.json` — 默认配置模板
- `app_config.json` — 用户配置（运行时生成）
- 深度合并：用户配置只覆盖对应键，新增默认配置项自动生效
- 点分路径访问：`config.get("ai_service.api_key")`

### 6. LogManager 日志系统

- `RotatingFileHandler` 文件轮转（默认 5MB，保留 10 个备份）
- 控制台同步输出
- 日志格式：`[时间] [级别] [模块] 消息`

## 信号通信流程

```
用户点击 NavItem
  → NavItem.clicked_with_key(page_key)
  → Sidebar.navigate_requested(page_key)
  → SignalBus.navigate_to(page_key)
  → NavigationManager.navigate_to(page_key)
  → QStackedWidget.setCurrentWidget(page)
  → NavigationManager.page_changed(page_key)
  → SignalBus.page_changed(page_key)
  → Sidebar.set_active(page_key)     [高亮更新]
  → StatusBar.showMessage(...)       [状态栏更新]
```

## 新增功能页面流程

1. 在 `apps/new_feature/` 下创建 `new_page.py`，继承 `BasePage`
2. 实现 `_setup_ui()` 和 `_setup_connections()`
3. 在 `framework/main_window.py` 的 `_register_pages()` 中注册页面
4. 在侧边栏自动添加导航项
5. 完成 — 框架自动处理切换、高亮、生命周期

## 样式系统

- **QSS 外部文件**: `resources/styles/main.qss`
- **主题常量**: `resources/styles/theme.py`
- 样式与代码分离，便于独立调整

## 版本管理

- `VERSION` 文件存储当前版本号
- `CHANGELOG.md` 记录版本变更
- 语义化版本：`MAJOR.MINOR.PATCH`

## 目录结构

| 目录 | 说明 |
|------|------|
| `launcher/` | 应用启动入口 |
| `framework/` | 核心框架层 |
| `apps/` | 功能页面模块 |
| `components/` | 可复用 UI 组件 |
| `config/` | 配置文件 |
| `database/` | 数据库（预留） |
| `docs/` | 文档 |
| `logs/` | 日志输出 |
| `resources/` | 图标、样式等资源 |
| `tests/` | 测试套件 |
