# APM因子模型 - 重构版

## 概述

本项目是对原始APM因子模型的重构版本，主要改进包括：

1. **数据源替换**：从jqdata替换为tushare，使用免费可获得的数据源
2. **代码优化**：重构代码结构，提高可读性和可维护性
3. **功能增强**：添加完整的因子分析和可视化功能
4. **性能提升**：优化数据获取和计算流程

## 主要特性

- ✅ 使用tushare免费数据源
- ✅ 面向对象的代码设计
- ✅ 完整的错误处理和重试机制
- ✅ 支持多种APM因子变体
- ✅ 内置因子分析和可视化工具
- ✅ 详细的文档和示例

## 安装依赖

```bash
pip install tushare pandas numpy scipy statsmodels matplotlib seaborn tqdm empyrical alphalens
```

## 快速开始

### 1. 配置tushare token

在代码中设置你的tushare token：

```python
TS_TOKEN = 'your_tushare_token_here'
```

### 2. 运行简单测试

```python
python apm_factor_refactored.py
```

### 3. 使用Jupyter Notebook

打开 `APM因子模型_重构版.ipynb` 文件，按照示例逐步运行。

## 代码结构

### 核心类

1. **TuShareDataProvider**: 数据提供器
   - 封装tushare API调用
   - 提供重试机制和错误处理
   - 支持股票列表、日线数据、分钟数据获取

2. **StockScreener**: 股票筛选器
   - 获取指数成分股
   - 过滤停牌股票、ST股票、次新股
   - 构建符合条件的股票池

3. **APMFactorCalculator**: APM因子计算器
   - 实现APM因子计算逻辑
   - 支持多种时段组合
   - 包含回归分析和统计量计算

4. **FactorAnalyzer**: 因子分析器
   - IC分析和统计
   - 分位数收益率分析
   - 可视化工具

### 因子类型

| 因子名称 | 时段1 | 时段2 | 说明 |
|---------|-------|-------|------|
| APM_RAW | 上午(9:30-11:30) | 下午(13:00-15:00) | 原始APM因子 |
| APM_NEW | 隔夜 | 下午(13:00-15:00) | 隔夜vs下午 |
| APM_1 | 隔夜 | 14:00-15:00 | 隔夜vs尾盘 |
| APM_2 | 9:30-10:30 | 14:00-15:00 | 早盘vs尾盘 |
| APM_3 | 10:30-11:30 | 13:00-14:00 | 上午后段vs下午前段 |

## 使用示例

### 单次因子计算

```python
from apm_factor_refactored import *

# 初始化组件
data_provider = TuShareDataProvider()
screener = StockScreener(data_provider)
calculator = APMFactorCalculator(data_provider)

# 获取股票池
stocks = screener.get_filtered_stock_pool('000905.XSHG', '20231201')

# 计算APM因子
factor = calculator.calculate_apm_factor(stocks[:50], '000905.SH', '20231201', 'apm_raw')

print(f"因子计算完成，有效股票数: {len(factor)}")
print(factor.describe())
```

### 因子分析

```python
# 初始化分析器
analyzer = FactorAnalyzer(data_provider)

# 获取前瞻收益率
forward_returns = analyzer.get_forward_returns(stocks, '20231201', 5)

# 计算IC
ic_result = analyzer.calculate_ic(factor, forward_returns)
print(f"IC: {ic_result['IC']:.4f}")
print(f"Rank IC: {ic_result['Rank_IC']:.4f}")

# 分位数分析
quantile_df = analyzer.factor_quantile_analysis(factor, forward_returns, 5)
analyzer.plot_quantile_returns(quantile_df, 'APM因子分位数收益率')
```

### 批量分析

```python
# 批量计算多个时期的因子
results = batch_factor_analysis(
    index_code='000905.XSHG',
    start_date='20230101',
    end_date='20231201',
    freq='M',
    max_stocks=100
)

# 分析IC表现
ic_summary = analyze_ic_performance(results['ic_results'])
print(ic_summary)
```

## 性能优化建议

1. **限制股票数量**：对于测试，建议限制在50-100只股票
2. **调整时间频率**：使用月度或周度频率而非日度
3. **缓存数据**：对于重复计算，可以缓存中间结果
4. **并行处理**：可以使用多进程处理不同股票的计算

## 注意事项

1. **API限制**：tushare有调用频率限制，代码中已添加延时
2. **数据质量**：分钟级数据可能存在缺失，已做简化处理
3. **内存使用**：大量股票和长时间序列会占用较多内存
4. **网络稳定性**：确保网络连接稳定，避免数据获取中断

## 扩展功能

### 可以添加的功能

1. **更多数据源**：集成akshare、wind等数据源
2. **因子存储**：实现因子数据的持久化存储
3. **实时计算**：支持实时因子计算和更新
4. **风险模型**：集成多因子风险模型
5. **回测框架**：完整的因子回测和组合构建

### 自定义扩展

```python
# 自定义时间段
custom_periods = {
    'custom1': ('09:30:00', '10:00:00'),
    'custom2': ('14:30:00', '15:00:00')
}

# 添加到计算器
calculator.TIME_PERIODS.update(custom_periods)

# 计算自定义因子
factor = calculator.calculate_apm_factor(stocks, benchmark, date, 'custom')
```

## 常见问题

### Q: 如何获取tushare token？
A: 访问 https://tushare.pro/ 注册账号并获取token

### Q: 计算速度很慢怎么办？
A: 减少股票数量，使用更长的时间间隔，或者缓存中间结果

### Q: 数据获取失败怎么办？
A: 检查网络连接，确认token有效，查看是否超出API调用限制

### Q: 如何验证因子有效性？
A: 使用IC分析、分位数收益率分析、回测等方法验证

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 许可证

本项目遵循原项目的许可证。

## 更新日志

- v1.0: 初始重构版本，替换数据源为tushare
- v1.1: 添加完整的因子分析功能
- v1.2: 优化性能和错误处理
