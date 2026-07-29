# AI电商工具箱 (AI E-commerce Toolkit)

一个基于 PySide6 的 AI 电商办公桌面应用，为淘宝、京东、拼多多、抖音店铺运营提供智能化工具。

## 技术栈

- **Python** 3.13+
- **GUI** PySide6 (Qt for Python)
- **平台** Windows

## 快速开始

### 环境要求

- Python 3.13+
- Windows 10/11

### 安装与运行

1. 双击 `run.bat` 启动（首次运行会自动创建虚拟环境并安装依赖）
2. 或手动操作：

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行
python -m launcher
```

### 打包

```bash
.venv\Scripts\python.exe -m PyInstaller --noconsole --name "AI电商工具箱" -m launcher
```

## 项目结构

```
AI-Ecommerce-Toolkit/
├── launcher/        # 应用启动入口
├── framework/       # 核心框架层（配置、日志、导航、信号总线）
├── apps/            # 功能页面模块
├── components/      # 可复用 UI 组件
├── config/          # 配置文件
├── database/        # 数据库（预留）
├── docs/            # 文档
├── logs/            # 日志输出
├── resources/       # 图标、样式等资源
├── tests/           # 测试套件
├── run.bat          # Windows 启动脚本
├── build.bat        # 打包脚本
└── VERSION          # 版本号
```

## 版本

当前版本：V0.1.0 — 基础框架

## 开发计划

- **V0.1** 基础框架（主窗口、导航、配置、日志） ✅
- **V0.2** 商品链接分析
- **V0.3** AI 标题优化
- **V0.4+** 更多功能...

## 许可证

MIT License
