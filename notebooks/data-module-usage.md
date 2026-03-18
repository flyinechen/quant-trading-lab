# 数据模块使用示例

**量化交易实验室 - 数据模块**  
**版本**: 0.1.0  
**更新时间**: 2026-03-18

---

## 📋 目录

1. [快速开始](#1-快速开始)
2. [数据源使用](#2-数据源使用)
3. [数据清洗](#3-数据清洗)
4. [数据存储](#4-数据存储)
5. [完整示例](#5-完整示例)

---

## 1. 快速开始

### 1.1 安装依赖

```bash
# 安装数据源依赖
pip install akshare tushare pandas numpy scipy

# 安装数据库依赖
pip install influxdb-client sqlalchemy psycopg2-binary
```

### 1.2 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入你的 API Token
# TUSHARE_TOKEN=your_tushare_token_here
```

### 1.3 基本使用

```python
from src.data import TushareSource, AKShareSource, DataCleaner

# 创建数据源
tushare = TushareSource(token="your_token")
akshare = AKShareSource()

# 连接
tushare.connect()
akshare.connect()

# 获取数据
df = tushare.get_kline(
    symbol="000001.SZ",
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 12, 31),
    interval="1d"
)

# 清洗数据
cleaner = DataCleaner()
clean_df, report = cleaner.clean(df, symbol="000001.SZ")

# 查看质量报告
print(report)
```

---

## 2. 数据源使用

### 2.1 Tushare 数据源

```python
from datetime import datetime
from src.data import TushareSource

# 初始化
tushare = TushareSource(token="your_tushare_token")

# 连接
if not tushare.connect():
    raise Exception("Tushare connection failed")

# 获取日线数据
df_daily = tushare.get_kline(
    symbol="000001.SZ",  # 平安银行
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 12, 31),
    interval="1d"
)

# 获取周线数据
df_weekly = tushare.get_kline(
    symbol="000001.SZ",
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 12, 31),
    interval="1w"
)

# 获取分钟线数据
df_1min = tushare.get_kline(
    symbol="000001.SZ",
    start_date=datetime(2025, 12, 1),
    end_date=datetime(2025, 12, 31),
    interval="1m"
)

# 获取股票列表
symbols = tushare.get_symbols(market="SSE")  # 上交所
print(f"Found {len(symbols)} symbols")

# 断开连接
tushare.disconnect()
```

### 2.2 AKShare 数据源

```python
from datetime import datetime
from src.data import AKShareSource

# 初始化
akshare = AKShareSource()

# 连接 (AKShare 不需要 Token)
if not akshare.connect():
    raise Exception("AKShare connection failed")

# 获取日线数据
df = akshare.get_kline(
    symbol="000001",  # 平安银行 (不需要 .SZ 后缀)
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 12, 31),
    interval="1d"
)

# 获取分钟线数据
df_5min = akshare.get_kline(
    symbol="000001",
    start_date=datetime(2025, 12, 1),
    end_date=datetime(2025, 12, 31),
    interval="5m"
)

# 获取 A 股列表
symbols = akshare.get_symbols()
print(f"Found {len(symbols)} A-share symbols")

# 断开连接
akshare.disconnect()
```

### 2.3 数据源注册表

```python
from src.data import DataSourceRegistry

# 查看所有已注册的数据源
print(DataSourceRegistry.list_sources())
# 输出：['tushare', 'akshare']

# 获取数据源实例
source = DataSourceRegistry.get("tushare", token="your_token")
source.connect()

# 使用数据源
df = source.get_kline(
    symbol="000001.SZ",
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 12, 31),
)
```

---

## 3. 数据清洗

### 3.1 基本清洗

```python
from src.data import DataCleaner
import pandas as pd

# 创建清洗器
cleaner = DataCleaner()

# 执行清洗
clean_df, report = cleaner.clean(
    df=raw_df,
    symbol="000001.SZ",
    fill_method="forward",  # 缺失值向前填充
    max_consecutive=3,      # 最大连续缺失 3 个周期
    price_change_limit=0.10, # 涨跌幅限制 10%
)

# 查看质量报告
print(f"原始行数：{report['original_rows']}")
print(f"清洗后行数：{report['final_rows']}")
print(f"删除行数：{report['removed_rows']}")
print(f"数据完整性：{report['completeness']}%")
print(f"数据准确性：{report['accuracy']}%")
print(f"发现的问题：{len(report['issues'])}")

# 查看详细问题
for issue in report['issues']:
    print(f"问题类型：{issue['type']}")
    print(f"详情：{issue}")
```

### 3.2 缺失值处理

```python
# 向前填充
clean_df, _ = cleaner.clean(df, fill_method="forward")

# 向后填充
clean_df, _ = cleaner.clean(df, fill_method="backward")

# 均值填充
clean_df, _ = cleaner.clean(df, fill_method="mean")

# 直接删除
clean_df, _ = cleaner.clean(df, fill_method="drop")
```

### 3.3 异常值检测

```python
# Z-Score 检测 (默认阈值 3)
clean_df, _ = cleaner.clean(df, method="zscore", threshold=3.0)

# IQR 检测
clean_df, _ = cleaner.clean(df, method="iqr")

# 自定义涨跌幅限制
clean_df, _ = cleaner.clean(df, price_change_limit=0.20)  # 20% 涨跌幅
```

### 3.4 便捷函数

```python
from src.data import clean_data

# 一行代码完成清洗
clean_df, report = clean_data(raw_df, symbol="000001.SZ")
```

---

## 4. 数据存储

### 4.1 InfluxDB 存储 (时序数据)

```python
from src.data.storage import StorageRegistry

# 创建 InfluxDB 存储实例
influx = StorageRegistry.get("influxdb", **{
    "url": "http://localhost:8086",
    "token": "your_influx_token",
    "org": "quant_lab",
    "bucket": "market_data",
})

# 连接
influx.connect()

# 保存 K 线数据
rows = influx.save_kline(
    symbol="000001.SZ",
    data=clean_df,
    interval="1d"
)
print(f"Saved {rows} rows")

# 加载 K 线数据
df = influx.load_kline(
    symbol="000001.SZ",
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 12, 31),
    interval="1d"
)

# 断开连接
influx.disconnect()
```

### 4.2 PostgreSQL 存储 (交易记录)

```python
from src.data.storage import StorageRegistry

# 创建 PostgreSQL 存储实例
postgres = StorageRegistry.get("postgres", **{
    "host": "localhost",
    "port": 5432,
    "database": "quant_lab",
    "user": "quant_user",
    "password": "quant_password",
})

# 连接
postgres.connect()

# 保存交易记录 (需要实现具体方法)
# rows = postgres.save_trades(trades)

# 断开连接
postgres.disconnect()
```

---

## 5. 完整示例

### 5.1 数据获取 + 清洗 + 存储

```python
from datetime import datetime
from src.data import TushareSource, DataCleaner, StorageRegistry

# 1. 初始化数据源
tushare = TushareSource(token="your_tushare_token")
tushare.connect()

# 2. 获取数据
print("Getting data from Tushare...")
df = tushare.get_kline(
    symbol="000001.SZ",
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 12, 31),
    interval="1d"
)
print(f"Got {len(df)} rows")

# 3. 清洗数据
print("Cleaning data...")
cleaner = DataCleaner()
clean_df, report = cleaner.clean(df, symbol="000001.SZ")
print(f"Cleaned: {report['original_rows']} -> {report['final_rows']} rows")
print(f"Completeness: {report['completeness']}%")

# 4. 存储数据
print("Saving to InfluxDB...")
influx = StorageRegistry.get("influxdb", **{
    "url": "http://localhost:8086",
    "token": "your_token",
    "org": "quant_lab",
    "bucket": "market_data",
})
influx.connect()

rows = influx.save_kline(
    symbol="000001.SZ",
    data=clean_df,
    interval="1d"
)
print(f"Saved {rows} rows")

influx.disconnect()
tushare.disconnect()

print("Done!")
```

### 5.2 多数据源对比

```python
from src.data import TushareSource, AKShareSource

# 同时从两个数据源获取数据
tushare = TushareSource(token="your_token")
akshare = AKShareSource()

tushare.connect()
akshare.connect()

# 获取同一标的
symbol = "000001"
start = datetime(2025, 1, 1)
end = datetime(2025, 12, 31)

df_tushare = tushare.get_kline(symbol + ".SZ", start, end)
df_akshare = akshare.get_kline(symbol, start, end)

# 对比数据
print(f"Tushare: {len(df_tushare)} rows")
print(f"Akshare: {len(df_akshare)} rows")

# 对比收盘价
if not df_tushare.empty and not df_akshare.empty:
    merged = pd.merge(
        df_tushare[['timestamp', 'close']],
        df_akshare[['timestamp', 'close']],
        on='timestamp',
        suffixes=('_tushare', '_akshare')
    )
    
    # 计算差异
    merged['diff'] = (merged['close_tushare'] - merged['close_akshare']).abs()
    print(f"Max price diff: {merged['diff'].max()}")

tushare.disconnect()
akshare.disconnect()
```

### 5.3 批量获取数据

```python
from src.data import TushareSource, DataCleaner
import pandas as pd

# 获取所有股票数据
tushare = TushareSource(token="your_token")
tushare.connect()

# 获取股票列表
symbols = tushare.get_symbols(market="SSE")[:10]  # 前 10 只股票

all_data = {}
for symbol in symbols:
    print(f"Processing {symbol}...")
    
    df = tushare.get_kline(
        symbol=symbol,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 12, 31),
    )
    
    if not df.empty:
        cleaner = DataCleaner()
        clean_df, report = cleaner.clean(df, symbol=symbol)
        all_data[symbol] = clean_df
        print(f"  {symbol}: {len(clean_df)} rows, {report['completeness']}% complete")

tushare.disconnect()

print(f"Processed {len(all_data)} symbols")
```

---

## 📝 注意事项

1. **API Token 安全**
   - 不要将 Token 提交到 Git
   - 使用环境变量或 .env 文件
   - 定期更换 Token

2. **数据质量**
   - 始终进行数据清洗
   - 检查质量报告
   - 对异常数据保持警惕

3. **性能优化**
   - 批量获取数据时添加延迟
   - 使用缓存减少 API 调用
   - 合理设置日期范围

4. **错误处理**
   - 捕获连接异常
   - 处理空数据
   - 记录错误日志

---

## 🔗 相关文档

- [数据源 API 文档](../api/data-sources.md)
- [数据清洗算法](../dev-guide/data-cleaning.md)
- [数据库设计](../architecture/database.md)

---

*Last Updated: 2026-03-18*
