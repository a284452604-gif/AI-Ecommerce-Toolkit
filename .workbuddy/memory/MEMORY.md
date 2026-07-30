# 项目记忆 - AI电商工具箱

## 项目信息
- **名称**: AI-Ecommerce-Toolkit (AI电商工具箱)
- **GitHub**: https://github.com/a284452604-gif/AI-Ecommerce-Toolkit
- **技术栈**: Python 3.13 + PySide6 6.11.1
- **目标平台**: Windows 桌面应用
- **当前版本**: V0.1.0 (基础框架)

## 技术决策
- GUI 框架: PySide6 (Qt for Python)
- AI 服务: 暂不确定，已预留接口和配置项
- 数据来源: 手动输入/粘贴
- 配置格式: JSON (default_config.json + app_config.json 深度合并)
- 日志: Python logging + RotatingFileHandler

## 架构要点
- 三层架构: launcher → framework → apps/components
- SignalBus 信号总线: 组件间零直接依赖
- BasePage 抽象基类: 新增页面继承+注册即可
- AppContext 单例: 管理全局配置、日志、服务
- QSS 外部样式表: resources/styles/main.qss

## 开发环境
- Python: C:\Users\ZHANG\.workbuddy\binaries\python\versions\3.13.12\python.exe
- venv: 项目目录下 .venv/
- 运行: `.venv\Scripts\python.exe -m launcher` 或 `run.bat`

## 版本路线
- V0.1 ✅ 基础框架 (主窗口、导航、首页、设置、关于、配置、日志)
- V0.2 商品链接分析
- V0.3 AI 标题优化
- V1.0 完整电商工具箱
