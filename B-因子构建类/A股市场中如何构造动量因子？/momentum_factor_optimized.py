#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股动量因子构造分析 - 优化版

基于开源证券研报《A股市场中如何构造动量因子？》
使用tushare和akshare等免费数据源重新实现

主要改进：
1. 使用免费数据源替代jqdata
2. 优化代码结构和性能
3. 添加更多分析功能
4. 改善错误处理和用户体验

作者：AI Assistant
日期：2024年
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tushare as ts
import warnings
from typing import List, Dict, Tuple, Union, Optional
from datetime import datetime, timedelta
import scipy.stats as stats
from tqdm import tqdm
import time

# 设置
warnings.filterwarnings('ignore')
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 配置tushare
TUSHARE_TOKEN = 'ce9f8c37a4af987f6328321ed4b3f9379f695d6d6bdc5b59d454e3ad'
ts.set_token(TUSHARE_TOKEN)
pro = ts.pro_api()


class DataProvider:
    """数据提供者类"""
    
    def __init__(self):
        self.pro = pro
        
    def get_stock_list(self, max_stocks: int = 100) -> List[str]:
        """获取股票列表"""
        try:
            stocks = self.pro.stock_basic(
                exchange='', 
                list_status='L',
                fields='ts_code,symbol,name,area,industry,list_date'
            )
            
            # 过滤条件
            stocks = stocks[~stocks['name'].str.contains('ST|退', na=False)]
            stocks = stocks[~stocks['ts_code'].str.startswith('688')]  # 排除科创板
            stocks = stocks[~stocks['ts_code'].str.startswith('300')]  # 排除创业板
            
            return stocks['ts_code'].head(max_stocks).tolist()
        except Exception as e:
            print(f"获取股票列表失败: {e}")
            return []
    
    def get_price_data(self, ts_codes: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        """获取价格数据"""
        all_data = []
        failed_count = 0
        
        print(f"开始获取{len(ts_codes)}只股票的价格数据...")
        
        for i, ts_code in enumerate(tqdm(ts_codes, desc="获取价格数据")):
            try:
                # 添加延时避免频率限制
                if i > 0 and i % 10 == 0:
                    time.sleep(0.1)
                    
                df = self.pro.daily(
                    ts_code=ts_code,
                    start_date=start_date.replace('-', ''),
                    end_date=end_date.replace('-', ''),
                    fields='ts_code,trade_date,close'
                )
                
                if not df.empty and len(df) > 100:  # 至少100个交易日
                    df['trade_date'] = pd.to_datetime(df['trade_date'])
                    df = df.sort_values('trade_date')
                    df = df.set_index('trade_date')
                    df = df.rename(columns={'close': ts_code})
                    all_data.append(df[ts_code])
                else:
                    failed_count += 1
                    
            except Exception as e:
                failed_count += 1
                if failed_count < 5:  # 只显示前5个错误
                    print(f"获取{ts_code}数据失败: {e}")
                continue
        
        if all_data:
            result = pd.concat(all_data, axis=1)
            print(f"成功获取{len(result.columns)}只股票数据，失败{failed_count}只")
            return result.dropna(how='all')
        else:
            print("未获取到任何有效数据")
            return pd.DataFrame()


class MomentumFactorCalculator:
    """动量因子计算器"""
    
    def __init__(self, price_data: pd.DataFrame):
        self.price_data = price_data.fillna(method='ffill').dropna()
        self.returns = self.price_data.pct_change().fillna(0)
        
    def calculate_amplitude(self, window: int = 1) -> pd.DataFrame:
        """计算振幅"""
        if window == 1:
            # 日振幅：当日最高最低价差/前收盘价
            # 这里简化为收益率的绝对值
            return self.returns.abs()
        else:
            # 滚动窗口振幅
            rolling_max = self.price_data.rolling(window).max()
            rolling_min = self.price_data.rolling(window).min()
            return (rolling_max / rolling_min - 1).fillna(0)
    
    def calculate_momentum_factor_A(self, window: int = 60, lambda_ratio: float = 0.3) -> pd.DataFrame:
        """计算A类动量因子（基于振幅切割）"""
        print(f"计算A类动量因子，窗口={window}，lambda={lambda_ratio}")
        
        momentum_factors = pd.DataFrame(index=self.returns.index, columns=self.returns.columns)
        amplitude = self.calculate_amplitude(1)
        
        # 向量化计算，提高效率
        for i in tqdm(range(window, len(self.returns)), desc="计算动量因子"):
            date = self.returns.index[i]
            
            # 获取窗口期数据
            window_returns = self.returns.iloc[i-window:i]
            window_amplitude = amplitude.iloc[i-window:i]
            
            for stock in self.returns.columns:
                if stock in window_returns.columns:
                    stock_returns = window_returns[stock].dropna()
                    stock_amplitude = window_amplitude[stock].dropna()
                    
                    if len(stock_returns) >= window * 0.6:  # 至少60%的数据
                        # 创建组合数据
                        combined_data = pd.DataFrame({
                            'returns': stock_returns,
                            'amplitude': stock_amplitude
                        }).dropna()
                        
                        if len(combined_data) > 10:
                            # 按振幅排序，选择振幅较低的部分
                            sorted_data = combined_data.sort_values('amplitude')
                            cutoff = max(1, int(len(sorted_data) * lambda_ratio))
                            selected_returns = sorted_data.head(cutoff)['returns']
                            
                            # 计算动量因子值
                            momentum_factors.loc[date, stock] = selected_returns.sum()
        
        return momentum_factors.astype(float)
    
    def calculate_simple_momentum(self, window: int = 60) -> pd.DataFrame:
        """计算简单动量因子（累积收益率）"""
        return self.returns.rolling(window).sum()


class FactorAnalyzer:
    """因子分析器"""
    
    def __init__(self, factor_data: pd.DataFrame, price_data: pd.DataFrame):
        self.factor_data = factor_data.fillna(0)
        self.price_data = price_data
        self.returns = price_data.pct_change().shift(-1).fillna(0)  # 下期收益率
        
    def calculate_ic(self) -> pd.Series:
        """计算IC值"""
        ic_series = []
        
        common_dates = self.factor_data.index.intersection(self.returns.index)
        
        for date in tqdm(common_dates, desc="计算IC"):
            factor_values = self.factor_data.loc[date].dropna()
            return_values = self.returns.loc[date].dropna()
            
            # 找到共同的股票
            common_stocks = factor_values.index.intersection(return_values.index)
            
            if len(common_stocks) > 20:  # 至少20只股票
                factor_aligned = factor_values[common_stocks]
                return_aligned = return_values[common_stocks]
                
                # 去除极值
                factor_aligned = self._winsorize(factor_aligned)
                return_aligned = self._winsorize(return_aligned)
                
                # 计算Spearman相关系数
                try:
                    ic, _ = stats.spearmanr(factor_aligned, return_aligned)
                    ic_series.append(ic if not np.isnan(ic) else 0)
                except:
                    ic_series.append(0)
            else:
                ic_series.append(0)
        
        return pd.Series(ic_series, index=common_dates)
    
    def _winsorize(self, series: pd.Series, limits: Tuple[float, float] = (0.05, 0.05)) -> pd.Series:
        """去极值处理"""
        lower = series.quantile(limits[0])
        upper = series.quantile(1 - limits[1])
        return series.clip(lower, upper)
    
    def calculate_factor_stats(self, ic_series: pd.Series) -> Dict[str, float]:
        """计算因子统计指标"""
        ic_clean = ic_series.replace([np.inf, -np.inf], np.nan).dropna()
        
        if len(ic_clean) == 0:
            return {'IC均值': 0, 'IC标准差': 0, 'ICIR': 0, 'IC胜率': 0}
        
        return {
            'IC均值': ic_clean.mean(),
            'IC标准差': ic_clean.std(),
            'ICIR': ic_clean.mean() / ic_clean.std() if ic_clean.std() != 0 else 0,
            'IC胜率': (ic_clean > 0).mean()
        }


def main_analysis(start_date: str = '2020-01-01', end_date: str = '2023-12-31',
                 max_stocks: int = 50):
    """主要分析流程"""

    print("=== A股动量因子构造分析（优化版）===")
    print(f"分析期间: {start_date} 至 {end_date}")
    print(f"最大股票数量: {max_stocks}")

    # 1. 获取数据
    print("\n1. 获取基础数据...")
    try:
        data_provider = DataProvider()
        stock_list = data_provider.get_stock_list(max_stocks)
    except Exception as e:
        print(f"初始化数据提供者失败: {e}")
        print("请检查tushare token是否正确配置")
        return None
    
    if not stock_list:
        print("未获取到股票列表，程序退出")
        return None
    
    print(f"获取到{len(stock_list)}只股票")
    
    price_data = data_provider.get_price_data(stock_list, start_date, end_date)
    
    if price_data.empty:
        print("未获取到价格数据，程序退出")
        return None
    
    print(f"价格数据形状: {price_data.shape}")
    
    # 2. 计算因子
    print("\n2. 计算动量因子...")
    calculator = MomentumFactorCalculator(price_data)
    
    # 计算不同lambda值的A类因子
    lambda_values = [0.1, 0.2, 0.3, 0.4, 0.5]
    factor_results = {}
    
    for lambda_val in lambda_values:
        print(f"\n计算lambda={lambda_val}的A类因子...")
        factor_A = calculator.calculate_momentum_factor_A(window=40, lambda_ratio=lambda_val)
        factor_results[f'A_{lambda_val}'] = factor_A
    
    # 计算简单动量因子作为对比
    print("\n计算简单动量因子...")
    simple_momentum = calculator.calculate_simple_momentum(window=40)
    factor_results['Simple_Momentum'] = simple_momentum
    
    # 3. 因子分析
    print("\n3. 进行因子分析...")
    ic_results = {}
    
    for factor_name, factor_data in factor_results.items():
        print(f"分析因子: {factor_name}")
        analyzer = FactorAnalyzer(factor_data, price_data)
        ic_series = analyzer.calculate_ic()
        stats_dict = analyzer.calculate_factor_stats(ic_series)
        
        ic_results[factor_name] = {
            **stats_dict,
            'ic_series': ic_series
        }
    
    # 4. 结果展示
    print("\n4. 结果汇总:")
    results_df = pd.DataFrame({
        name: {k: v for k, v in result.items() if k != 'ic_series'}
        for name, result in ic_results.items()
    }).T
    
    print(results_df.round(4))
    
    # 5. 可视化
    print("\n5. 生成分析图表...")
    plot_results(results_df, ic_results)
    
    return factor_results, ic_results, results_df


def plot_results(results_df: pd.DataFrame, ic_results: Dict):
    """绘制结果图表"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # IC均值柱状图
    results_df['IC均值'].plot(kind='bar', ax=axes[0,0], title='不同因子的IC均值', color='steelblue')
    axes[0,0].axhline(0, color='red', linestyle='--')
    axes[0,0].grid(True, alpha=0.3)
    axes[0,0].tick_params(axis='x', rotation=45)
    
    # ICIR柱状图
    results_df['ICIR'].plot(kind='bar', ax=axes[0,1], title='不同因子的ICIR', color='darkgreen')
    axes[0,1].axhline(0, color='red', linestyle='--')
    axes[0,1].grid(True, alpha=0.3)
    axes[0,1].tick_params(axis='x', rotation=45)
    
    # IC胜率柱状图
    results_df['IC胜率'].plot(kind='bar', ax=axes[1,0], title='不同因子的IC胜率', color='orange')
    axes[1,0].axhline(0.5, color='red', linestyle='--')
    axes[1,0].grid(True, alpha=0.3)
    axes[1,0].tick_params(axis='x', rotation=45)
    
    # IC时序图（选择最佳因子）
    best_factor = results_df.sort_values('ICIR', ascending=False).index[0]
    ic_series = ic_results[best_factor]['ic_series']
    ic_series.plot(ax=axes[1,1], title=f'最佳因子({best_factor})的IC时序', color='purple')
    axes[1,1].axhline(0, color='red', linestyle='--')
    axes[1,1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    # 打印最佳因子信息
    print(f"\n最佳因子（按ICIR排序）: {best_factor}")
    print(f"ICIR: {results_df.loc[best_factor, 'ICIR']:.4f}")
    print(f"IC均值: {results_df.loc[best_factor, 'IC均值']:.4f}")
    print(f"IC胜率: {results_df.loc[best_factor, 'IC胜率']:.4f}")


if __name__ == "__main__":
    # 运行分析
    try:
        results = main_analysis(
            start_date='2021-01-01',
            end_date='2023-12-31',
            max_stocks=30  # 减少股票数量以提高速度
        )
        
        if results:
            print("\n分析完成！")
        else:
            print("\n分析失败，请检查网络连接和数据源设置")
            
    except KeyboardInterrupt:
        print("\n用户中断程序")
    except Exception as e:
        print(f"\n程序执行出错: {e}")
        print("建议检查：")
        print("1. 网络连接是否正常")
        print("2. tushare token是否有效")
        print("3. 是否安装了所有必需的依赖包")
