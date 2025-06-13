# A股动量因子构造分析 - 优化版

基于开源证券研报《A股市场中如何构造动量因子？》，使用免费数据源重新实现的动量因子分析工具。

## 🚀 主要改进

### 数据源替换
- ✅ 使用 **tushare** 替代 jqdata
- ✅ 支持 **akshare** 作为备用数据源  
- ✅ 完全基于免费、开源的数据接口

### 代码优化
- ✅ 面向对象设计，提高可维护性
- ✅ 向量化计算，显著提升性能
- ✅ 完善的错误处理和用户提示
- ✅ 模块化架构，便于扩展

### 功能增强
- ✅ 多种动量因子构造方法
- ✅ 丰富的分析指标（IC、ICIR、胜率）
- ✅ 可视化分析图表
- ✅ 高级分析功能

## 📦 快速开始

### 环境要求
```bash
Python >= 3.7
pandas >= 1.3.0
numpy >= 1.20.0
matplotlib >= 3.3.0
tushare >= 1.2.0
scipy >= 1.7.0
tqdm >= 4.60.0
```

### 安装依赖
```bash
pip install pandas numpy matplotlib tushare akshare scipy tqdm
```

### 运行分析
```bash
# 方法1：直接运行Python脚本
python momentum_factor_analysis.py

# 方法2：使用Jupyter Notebook
jupyter notebook A股市场动量因子构造_优化版.ipynb
```

## 🔧 核心功能

### 1. 数据获取 (`DataProvider`)
```python
# 获取股票列表和价格数据
data_provider = DataProvider()
stock_list = data_provider.get_stock_list(max_stocks=100)
price_data = data_provider.get_price_data(stock_list, '2020-01-01', '2023-12-31')
```

### 2. 因子计算 (`MomentumFactorCalculator`)
```python
# 计算动量因子
calculator = MomentumFactorCalculator(price_data)
factor_A = calculator.calculate_momentum_factor_A(window=60, lambda_ratio=0.3)
simple_momentum = calculator.calculate_simple_momentum(window=60)
```

### 3. 因子分析 (`FactorAnalyzer`)
```python
# 分析因子效果
analyzer = FactorAnalyzer(factor_data, price_data)
ic_series = analyzer.calculate_ic()
stats = analyzer.calculate_factor_stats(ic_series)
```

## 📊 核心算法

### A类动量因子构造
基于振幅切割的动量因子：

1. **计算振幅**：每日收益率绝对值
2. **振幅排序**：回看窗口内按振幅排序
3. **选择低振幅**：选择振幅最低的λ比例交易日
4. **累积收益**：对选中交易日收益率求和

### 关键参数
- `window`: 回看窗口期（建议30-120天）
- `lambda_ratio`: 振幅切割比例（建议0.1-0.5）

## 📈 使用示例

### 完整分析流程
```python
# 运行完整分析
results = main_analysis(
    start_date='2020-01-01',
    end_date='2023-12-31',
    max_stocks=50
)

if results:
    factor_results, ic_results, summary_df = results
    print("分析完成！")
    print(summary_df)
```

### 输出示例
```
=== A股动量因子构造分析（优化版）===
分析期间: 2020-01-01 至 2023-12-31
最大股票数量: 50

1. 获取基础数据...
获取到50只股票
成功获取45只股票数据，失败5只
价格数据形状: (975, 45)

2. 计算动量因子...
计算lambda=0.1的A类因子...
计算lambda=0.2的A类因子...
...

4. 结果汇总:
                IC均值    IC标准差     ICIR    IC胜率
A_0.1          0.0234    0.1456    0.1608    0.5234
A_0.2          0.0198    0.1389    0.1425    0.5156
A_0.3          0.0167    0.1334    0.1252    0.5089
Simple_Momentum 0.0145   0.1298    0.1117    0.5023

最佳因子（按ICIR排序）: A_0.1
ICIR: 0.1608
IC均值: 0.0234
IC胜率: 0.5234
```

## ⚡ 性能优化

### 数据加载优化
- 分批加载避免内存溢出
- 添加延时避免API限制
- 数据质量检查过滤无效数据

### 计算优化
- 向量化操作替代循环
- 使用pandas高效函数
- 合理设置参数减少计算量

## ⚠️ 注意事项

### 数据限制
- tushare免费版有调用频率限制
- 建议先用小样本测试
- 注意处理停牌、退市等情况

### 因子特性
- A股市场反转特征明显
- 动量效果可能不如海外市场
- 建议结合其他因子使用

### 回测要点
- 避免未来信息泄露
- 考虑交易成本和冲击
- 进行样本外验证

## 🔮 扩展功能

### 高级分析
- 滚动IC分析
- 因子衰减分析
- 行业中性化
- 风险调整收益

### 可视化增强
- 交互式图表
- 因子热力图
- 收益归因分析

### 策略应用
- 多因子模型
- 组合优化
- 风险管理

## ❓ 常见问题

**Q: 如何获取更多股票数据？**
A: 升级tushare账户或使用其他免费数据源。

**Q: 因子效果不显著怎么办？**
A: 调整参数（窗口期、lambda值）或结合其他因子。

**Q: 程序运行很慢怎么办？**
A: 减少股票数量、缩短时间窗口，或使用并行计算。

**Q: 如何处理数据缺失？**
A: 代码已包含数据清洗逻辑，可根据需要调整。

## 📄 文件说明

- `momentum_factor_analysis.py`: 主要分析脚本
- `A股市场动量因子构造_优化版.ipynb`: Jupyter Notebook版本
- `动量因子分析_README.md`: 本说明文档

## 🤝 贡献指南

欢迎提交Issue和Pull Request：
1. Fork项目
2. 创建功能分支
3. 提交更改
4. 发起Pull Request

## 📜 免责声明

本项目仅用于学习研究，不构成投资建议。实际投资风险自担。

## 📧 联系方式

如有问题请提交GitHub Issue或联系项目维护者。

---
**Happy Coding! 📈**
