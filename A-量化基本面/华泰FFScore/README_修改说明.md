# FFScore因子计算 - 数据源修改说明

## 修改概述

本项目已将原始的聚宽平台数据源替换为tushare和akshare，实现了相同的FFScore因子计算功能，但不再依赖聚宽平台。

## 主要修改内容

### 1. 数据源替换

**原始依赖：**
- `from jqdata import *`
- `from jqfactor import (calc_factors,Factor)`

**新的依赖：**
- `import tushare as ts`
- `import akshare as ak`

### 2. 核心函数替换

| 聚宽函数 | 新实现函数 | 功能说明 |
|---------|-----------|----------|
| `get_trade_days()` | `get_trade_days()` | 获取交易日历 |
| `get_all_securities()` | `get_all_securities()` | 获取股票基本信息 |
| `get_index_stocks()` | `get_index_stocks()` | 获取指数成分股 |
| `get_price()` | `get_price()` | 获取价格数据 |
| `get_extras()` | `get_extras()` | 获取ST状态等额外信息 |
| `get_security_info()` | `get_security_info()` | 获取股票基本信息 |
| `get_industry()` | `get_industry()` | 获取行业分类信息 |
| `get_valuation()` | `get_valuation()` | 获取估值数据 |
| `calc_factors()` | 重新实现 | 因子计算框架 |

### 3. FScore类重新实现

**原始实现：**
```python
class FScore(Factor):
    # 继承聚宽Factor基类
    dependencies = [...]  # 依赖聚宽财务数据字段
    def calc(self, data: Dict) -> None:
        # 使用聚宽预处理的财务数据
```

**新实现：**
```python
class FScore:
    # 独立实现，不依赖聚宽
    def get_financial_data(self, securities, date):
        # 直接从tushare获取财务数据
    def calc(self, securities, date):
        # 完整的FScore计算逻辑
```

## 使用方法

### 1. 环境准备

```bash
pip install tushare akshare pandas numpy empyrical
```

### 2. 设置tushare token

```python
import tushare as ts
ts.set_token('your_tushare_token_here')
```

### 3. 基本使用

```python
from FFScore_tushare import FScore, get_trade_period

# 设置时间范围
start_date, end_date = '2020-01-01', '2020-12-31'
periods = get_trade_period(start_date, end_date, 'M')

# 创建FScore实例
fscore = FScore()

# 计算因子
for period in periods:
    # 获取股票池（这里需要根据实际需求筛选）
    securities = ['000001.XSHE', '000002.XSHE']  # 示例股票
    
    # 计算FScore
    fscore.calc(securities, period)
    
    # 获取结果
    print(f"日期: {period}")
    print(f"FScore结果: {fscore.fscore}")
    print(f"基础数据: {fscore.basic}")
```

## 数据获取说明

### 1. tushare数据（优先使用）

- **交易日历**: `pro.trade_cal()`
- **股票基本信息**: `pro.stock_basic()`
- **价格数据**: `pro.daily()`
- **财务数据**: `pro.balancesheet()`, `pro.income()`, `pro.cashflow()`
- **估值数据**: `pro.daily_basic()`

### 2. akshare数据（备用）

- **交易日历**: `ak.tool_trade_date_hist_sina()`
- **股票数据**: 各种ak接口

### 3. 数据字段映射

| FFScore指标 | tushare字段 | 说明 |
|------------|-------------|------|
| ROA | n_income/total_assets | 资产收益率 |
| CFO | n_cashflow_act | 经营现金流 |
| 杠杆率 | total_ncl/total_nca | 非流动负债/非流动资产 |
| 流动比率 | total_cur_assets/total_cur_liab | 流动资产/流动负债 |
| 毛利率 | gross_margin | 毛利率 |

## 注意事项

### 1. API限制

- tushare有调用频率限制，建议：
  - 使用积分版本获得更高调用频率
  - 在代码中添加适当的延时
  - 批量获取数据以减少API调用次数

### 2. 数据质量

- 财务数据可能存在缺失值，已在代码中添加处理逻辑
- 建议在实际使用前验证数据的完整性和准确性

### 3. 性能优化

- 当前实现为了演示清晰性，未做过多优化
- 实际使用时可以考虑：
  - 数据缓存机制
  - 并行处理
  - 数据库存储

## 文件说明

- `FFScore_tushare.py`: 新的实现文件，包含所有替换后的函数
- `FFScore.ipynb`: 原始notebook文件（已部分修改）
- `README_修改说明.md`: 本说明文档

## 测试验证

建议在使用前进行以下测试：

1. **数据获取测试**：验证各个数据获取函数是否正常工作
2. **因子计算测试**：对比新旧实现的计算结果
3. **性能测试**：评估数据获取和计算的效率

## 后续改进

1. **完善财务数据获取**：补充更多财务指标的获取逻辑
2. **优化API调用**：实现更高效的数据获取策略
3. **添加数据验证**：增强数据质量检查机制
4. **性能优化**：提升大规模数据处理能力

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交Issue到项目仓库
- 发送邮件到项目维护者

---

**注意**: 本修改版本保持了原有的FFScore计算逻辑和功能，只是将数据源从聚宽平台替换为tushare和akshare，确保了功能的一致性。
