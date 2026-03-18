# 📈 Quantitative Trading Lab

**量化交易研究实验室** - Quantitative Trading Research Lab

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![GitHub stars](https://img.shields.io/github/stars/flyinechen/quant-trading-lab)](https://github.com/flyinechen/quant-trading-lab/stargazers)

---

## 🎯 项目目标

本项目致力于量化交易策略的研究、回测和实盘交易系统的开发。

### 核心功能

- 📊 **多因子策略** - 基于多因子的选股和择时策略
- 🤖 **机器学习** - 应用 ML/DL 模型进行价格预测
- 📈 **技术分析** - 经典技术指标和自定义指标库
- 🔙 **回测引擎** - 高性能策略回测框架
- 📉 **风险管理** - 仓位管理和风险控制模块
- 🔌 **数据接口** - 对接主流交易 API（聚宽、米筐、IB 等）

---

## 📁 项目结构

```
quant-trading-lab/
├── strategies/          # 交易策略
│   ├── momentum/       # 动量策略
│   ├── mean_reversion/ # 均值回归
│   └── ml_strategies/  # 机器学习策略
├── data/               # 数据文件
│   ├── raw/           # 原始数据
│   └── processed/     # 处理后数据
├── notebooks/          # Jupyter 笔记本
├── docs/              # 文档
├── tests/             # 单元测试
├── requirements.txt   # 依赖
└── README.md         # 项目说明
```

---

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行示例策略

```bash
python strategies/momentum/momentum_strategy.py
```

---

## 📚 策略列表

| 策略名称 | 类型 | 风险等级 | 状态 |
|----------|------|----------|------|
| 双均线策略 | 趋势跟踪 | ⭐⭐ | 🟢 可用 |
| RSI 均值回归 | 均值回归 | ⭐⭐⭐ | 🟡 测试中 |
| LSTM 价格预测 | 深度学习 | ⭐⭐⭐⭐ | 🔴 开发中 |

---

## 📊 回测结果

*待更新*

---

## ⚠️ 风险提示

⚠️ **投资有风险，入市需谨慎**

- 本项目仅供学习和研究使用
- 过往业绩不代表未来表现
- 实盘交易请谨慎评估风险

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📬 联系方式

- GitHub: [@flyinechen](https://github.com/flyinechen)
- 项目地址：https://github.com/flyinechen/quant-trading-lab

---

*Last Updated: 2026-03-18*
