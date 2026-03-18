# 回测引擎使用示例

**量化交易实验室 - 回测引擎**  
**版本**: 0.1.0  
**更新时间**: 2026-03-18

---

## 📋 目录

1. [快速开始](#1-快速开始)
2. [策略开发](#2-策略开发)
3. [回测配置](#3-回测配置)
4. [绩效分析](#4-绩效分析)
5. [完整示例](#5-完整示例)

---

## 1. 快速开始

### 1.1 基本使用

```python
from datetime import datetime
from src.engine import BacktestEngine
from src.strategy import BaseStrategy

# 创建回测引擎
engine = BacktestEngine(
    initial_capital=1000000,  # 初始资金 100 万
    commission_rate=0.0003,   # 手续费率万分之三
    slippage_rate=0.001,      # 滑点率 0.1%
)

# 加载数据
engine.load_data("000001.SZ", kline_data)

# 添加策略
strategy = MyStrategy()
engine.add_strategy(strategy, symbols=["000001.SZ"])

# 运行回测
results = engine.run()

# 查看结果
print(results)
```

### 1.2 安装依赖

```bash
# 回测引擎依赖
pip install pandas numpy scipy
```

---

## 2. 策略开发

### 2.1 策略基类

```python
from src.strategy import BaseStrategy, Signal
import pandas as pd

class MyStrategy(BaseStrategy):
    """自定义策略"""
    
    def initialize(self):
        """策略初始化"""
        # 设置参数
        self.short_window = 5
        self.long_window = 20
    
    def on_bar(self, symbol: str, bar: pd.Series) -> Signal:
        """
        K 线数据回调
        
        Args:
            symbol: 标的代码
            bar: K 线数据 (open/high/low/close/volume)
            
        Returns:
            Signal: 交易信号 (BUY/SELL/HOLD)
        """
        # 实现策略逻辑
        if bar['close'] > bar['open']:
            return Signal.BUY
        return Signal.HOLD
```

### 2.2 双均线策略示例

```python
from src.strategy import BaseStrategy, Signal
import pandas as pd

class DualMAStrategy(BaseStrategy):
    """双均线策略"""
    
    def initialize(self):
        """初始化"""
        self.short_window = 5   # 短期均线
        self.long_window = 20   # 长期均线
        self.prices = []
    
    def on_bar(self, symbol: str, bar: pd.Series) -> Signal:
        """K 线回调"""
        # 更新价格序列
        self.prices.append(bar['close'])
        
        # 确保有足够的数据
        if len(self.prices) < self.long_window:
            return Signal.HOLD
        
        # 计算均线
        prices = pd.Series(self.prices[-self.long_window:])
        sma_short = prices.tail(self.short_window).mean()
        sma_long = prices.mean()
        
        # 金叉买入
        if sma_short > sma_long and self.prices[-2] <= self.prices[-self.short_window-1]:
            return Signal.BUY
        
        # 死叉卖出
        elif sma_short < sma_long and self.prices[-2] >= self.prices[-self.short_window-1]:
            return Signal.SELL
        
        return Signal.HOLD
```

### 2.3 RSI 策略示例

```python
from src.strategy import BaseStrategy, Signal

class RSIStrategy(BaseStrategy):
    """RSI 超买超卖策略"""
    
    def initialize(self):
        """初始化"""
        self.rsi_period = 14
        self.overbought = 70    # 超买线
        self.oversold = 30      # 超卖线
        self.prices = []
    
    def on_bar(self, symbol: str, bar: pd.Series) -> Signal:
        """K 线回调"""
        self.prices.append(bar['close'])
        
        if len(self.prices) < self.rsi_period + 1:
            return Signal.HOLD
        
        # 计算 RSI
        prices = pd.Series(self.prices[-self.rsi_period-1:])
        delta = prices.diff()
        
        gain = (delta.where(delta > 0, 0)).mean()
        loss = (-delta.where(delta < 0, 0)).mean()
        
        if loss == 0:
            rsi = 100
        else:
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
        
        # RSI 超卖买入
        if rsi < self.oversold:
            return Signal.BUY
        
        # RSI 超买卖出
        elif rsi > self.overbought:
            return Signal.SELL
        
        return Signal.HOLD
```

---

## 3. 回测配置

### 3.1 引擎参数

```python
engine = BacktestEngine(
    # 资金参数
    initial_capital=1000000.0,    # 初始资金
    
    # 交易成本
    commission_rate=0.0003,       # 手续费率 (万分之三)
    slippage_rate=0.001,          # 滑点率 (0.1%)
    
    # 无风险利率 (用于夏普比率计算)
    risk_free_rate=0.03,          # 年化 3%
)
```

### 3.2 数据加载

```python
from src.data import TushareSource

# 从 Tushare 获取数据
tushare = TushareSource(token="your_token")
tushare.connect()

data = tushare.get_kline(
    symbol="000001.SZ",
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 12, 31),
    interval="1d"
)

# 加载到回测引擎
engine.load_data("000001.SZ", data)
```

### 3.3 多策略回测

```python
# 添加多个策略
engine.add_strategy(
    DualMAStrategy(),
    symbols=["000001.SZ"],
    strategy_id="dual_ma"
)

engine.add_strategy(
    RSIStrategy(),
    symbols=["000001.SZ"],
    strategy_id="rsi"
)

# 运行回测
results = engine.run()

# 查看各策略结果
for strategy_id, metrics in results.items():
    print(f"\n{strategy_id}:")
    print(f"  总收益率：{metrics['total_return']:.2%}")
    print(f"  夏普比率：{metrics['sharpe_ratio']:.3f}")
```

---

## 4. 绩效分析

### 4.1 绩效指标

```python
from src.engine import PerformanceAnalyzer

analyzer = PerformanceAnalyzer(risk_free_rate=0.03)

# 获取权益曲线
equity_curve = engine.get_equity_curve()

# 获取交易记录
trades = engine.get_trades()

# 计算绩效
metrics = analyzer.analyze(equity_curve, trades)

# 查看指标
print(f"总收益率：{metrics['total_return']:.2%}")
print(f"年化收益率：{metrics['annual_return']:.2%}")
print(f"夏普比率：{metrics['sharpe_ratio']:.3f}")
print(f"最大回撤：{metrics['max_drawdown']:.2%}")
print(f"胜率：{metrics['win_rate']:.2%}")
print(f"盈亏比：{metrics['profit_loss_ratio']:.2f}")
```

### 4.2 完整绩效指标

| 指标类别 | 指标名称 | 说明 |
|----------|----------|------|
| **收益指标** | total_return | 总收益率 |
| | annual_return | 年化收益率 |
| | daily_return | 日均收益率 |
| | win_month_ratio | 盈利月份占比 |
| **风险指标** | volatility | 波动率 (年化) |
| | max_drawdown | 最大回撤 |
| | var_95 | VaR(95% 置信水平) |
| | downside_volatility | 下行波动率 |
| **风险调整收益** | sharpe_ratio | 夏普比率 |
| | sortino_ratio | 索提诺比率 |
| **交易指标** | total_trades | 总交易次数 |
| | win_rate | 胜率 |
| | profit_loss_ratio | 盈亏比 |
| | profit_factor | 盈利因子 |
| | max_consecutive_losses | 最大连续亏损次数 |

### 4.3 生成报告

```python
# 生成文本报告
report = analyzer.generate_report(metrics, format="text")
print(report)

# 生成 Markdown 报告
md_report = analyzer.generate_report(metrics, format="markdown")
print(md_report)
```

---

## 5. 完整示例

### 5.1 完整回测流程

```python
from datetime import datetime
from src.engine import BacktestEngine
from src.data import TushareSource
from src.strategy import BaseStrategy, Signal

# ============ 1. 创建策略 ============
class DualMAStrategy(BaseStrategy):
    """双均线策略"""
    
    def initialize(self):
        self.short_window = 5
        self.long_window = 20
    
    def on_bar(self, symbol: str, bar: pd.Series) -> Signal:
        if not hasattr(self, 'prices'):
            self.prices = []
        
        self.prices.append(bar['close'])
        
        if len(self.prices) < self.long_window:
            return Signal.HOLD
        
        prices = pd.Series(self.prices[-self.long_window:])
        sma_short = prices.tail(self.short_window).mean()
        sma_long = prices.mean()
        
        if sma_short > sma_long:
            return Signal.BUY
        elif sma_short < sma_long:
            return Signal.SELL
        
        return Signal.HOLD

# ============ 2. 获取数据 ============
tushare = TushareSource(token="your_tushare_token")
tushare.connect()

data = tushare.get_kline(
    symbol="000001.SZ",
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 12, 31),
    interval="1d"
)

# ============ 3. 创建回测引擎 ============
engine = BacktestEngine(
    initial_capital=1000000,
    commission_rate=0.0003,
    slippage_rate=0.001,
)

# ============ 4. 加载数据 ============
engine.load_data("000001.SZ", data)

# ============ 5. 添加策略 ============
strategy = DualMAStrategy()
engine.add_strategy(strategy, symbols=["000001.SZ"])

# ============ 6. 运行回测 ============
results = engine.run()

# ============ 7. 查看结果 ============
for strategy_id, metrics in results.items():
    print(f"\n{'='*60}")
    print(f"策略：{strategy_id}")
    print(f"{'='*60}")
    print(f"总收益率：    {metrics.get('total_return', 0):>10.2%}")
    print(f"年化收益率：  {metrics.get('annual_return', 0):>10.2%}")
    print(f"夏普比率：    {metrics.get('sharpe_ratio', 0):>10.3f}")
    print(f"最大回撤：    {metrics.get('max_drawdown', 0):>10.2%}")
    print(f"胜率：        {metrics.get('win_rate', 0):>10.2%}")
    print(f"盈亏比：      {metrics.get('profit_loss_ratio', 0):>10.2f}")

# ============ 8. 获取权益曲线 ============
equity_curve = engine.get_equity_curve()

# ============ 9. 获取交易记录 ============
trades = engine.get_trades()
print(f"\n总交易次数：{len(trades)}")

# ============ 10. 可视化 ============
import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 1, figsize=(14, 10))

# 权益曲线
axes[0].plot(equity_curve.index, equity_curve.values)
axes[0].set_title('Equity Curve')
axes[0].set_xlabel('Date')
axes[0].set_ylabel('Equity')
axes[0].grid(True)

# 回撤曲线
rolling_max = equity_curve.expanding().max()
drawdown = (equity_curve - rolling_max) / rolling_max
axes[1].fill_between(drawdown.index, drawdown.values, 0, alpha=0.5)
axes[1].set_title('Drawdown')
axes[1].set_xlabel('Date')
axes[1].set_ylabel('Drawdown')
axes[1].grid(True)

plt.tight_layout()
plt.savefig('backtest_result.png')
plt.show()
```

### 5.2 参数优化示例

```python
from itertools import product

# 参数范围
short_windows = [5, 10, 15, 20]
long_windows = [20, 30, 50, 60]

best_result = None
best_params = None
best_sharpe = -float('inf')

# 参数遍历
for short_win, long_win in product(short_windows, long_windows):
    # 跳过无效参数
    if short_win >= long_win:
        continue
    
    # 创建策略
    strategy = DualMAStrategy()
    strategy.short_window = short_win
    strategy.long_window = long_win
    
    # 创建引擎
    engine = BacktestEngine(initial_capital=1000000)
    engine.load_data("000001.SZ", data)
    engine.add_strategy(strategy, symbols=["000001.SZ"])
    
    # 运行回测
    results = engine.run()
    metrics = results[list(results.keys())[0]]
    
    # 记录最佳结果
    sharpe = metrics.get('sharpe_ratio', 0)
    if sharpe > best_sharpe:
        best_sharpe = sharpe
        best_params = (short_win, long_win)
        best_result = metrics

print(f"最佳参数：短期={best_params[0]}, 长期={best_params[1]}")
print(f"最佳夏普比率：{best_sharpe:.3f}")
```

---

## 📝 注意事项

1. **数据质量**
   - 确保数据完整性和准确性
   - 检查缺失值和异常值
   - 使用复权价格

2. **过拟合风险**
   - 避免过度优化参数
   - 使用样本外数据验证
   - 考虑市场状态变化

3. **交易成本**
   - 设置合理的手续费率
   - 考虑滑点影响
   - 包含印花税等费用

4. **回测陷阱**
   - 避免未来函数
   - 考虑流动性限制
   - 注意幸存者偏差

---

## 🔗 相关文档

- [数据模块使用](./data-module-usage.md)
- [策略开发指南](../dev-guide/strategy-development.md)
- [绩效分析详解](../dev-guide/performance-analysis.md)

---

*Last Updated: 2026-03-18*
