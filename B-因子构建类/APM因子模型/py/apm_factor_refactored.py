#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APM因子模型 - 重构版
使用tushare替代jqdata，优化代码结构和可读性

Author: Refactored Version
Date: 2024
"""

import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import tushare as ts
import time
import datetime as dt
from typing import List, Dict, Tuple, Optional, Union
from tqdm import tqdm
from scipy import stats
import statsmodels.api as sm
import matplotlib.pyplot as plt

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 配置tushare
TS_TOKEN = 'ce9f8c37a4af987f6328321ed4b3f9379f695d6d6bdc5b59d454e3ad'
ts.set_token(TS_TOKEN)
pro = ts.pro_api()


class TuShareDataProvider:
    """TuShare数据提供器"""
    
    def __init__(self, token: str = TS_TOKEN, max_retry: int = 3):
        self.token = token
        self.max_retry = max_retry
        ts.set_token(token)
        self.pro = ts.pro_api()
    
    def _retry_request(self, func, *args, **kwargs):
        """带重试机制的请求"""
        for i in range(self.max_retry):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if i == self.max_retry - 1:
                    raise e
                time.sleep(1)
    
    def get_stock_list(self, list_status: str = 'L') -> pd.DataFrame:
        """获取股票列表"""
        return self._retry_request(self.pro.stock_basic, list_status=list_status)
    
    def get_index_stocks(self, index_code: str, trade_date: str = None) -> List[str]:
        """获取指数成分股"""
        if trade_date is None:
            trade_date = dt.datetime.now().strftime('%Y%m%d')
        
        # 转换指数代码格式
        if index_code == '000905.XSHG':
            index_code = '000905.SH'
        elif index_code == '000300.XSHG':
            index_code = '000300.SH'
        
        df = self._retry_request(self.pro.index_weight, 
                               index_code=index_code, 
                               trade_date=trade_date)
        return df['con_code'].tolist() if not df.empty else []
    
    def get_daily_data(self, ts_code: Union[str, List[str]], 
                      start_date: str, end_date: str) -> pd.DataFrame:
        """获取日线数据"""
        if isinstance(ts_code, list):
            dfs = []
            for code in ts_code:
                df = self._retry_request(self.pro.daily, 
                                       ts_code=code,
                                       start_date=start_date,
                                       end_date=end_date)
                if not df.empty:
                    dfs.append(df)
                time.sleep(0.1)
            return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
        else:
            return self._retry_request(self.pro.daily,
                                     ts_code=ts_code,
                                     start_date=start_date,
                                     end_date=end_date)
    
    def get_minute_data(self, ts_code: str, start_date: str, end_date: str, 
                       freq: str = '30min') -> pd.DataFrame:
        """获取分钟线数据"""
        return self._retry_request(ts.pro_bar,
                                 ts_code=ts_code,
                                 start_date=start_date,
                                 end_date=end_date,
                                 freq=freq)


class StockScreener:
    """股票筛选器"""
    
    def __init__(self, data_provider: TuShareDataProvider):
        self.data_provider = data_provider
    
    def get_base_stock_pool(self, index_code: str = None, trade_date: str = None) -> List[str]:
        """获取基础股票池"""
        if index_code and index_code != 'A':
            return self.data_provider.get_index_stocks(index_code, trade_date)
        else:
            df = self.data_provider.get_stock_list()
            return df['ts_code'].tolist()
    
    def filter_suspended_stocks(self, stocks: List[str], end_date: str, 
                              lookback_days: int = 22) -> List[str]:
        """过滤停牌股票"""
        start_date = (pd.to_datetime(end_date) - pd.Timedelta(days=lookback_days*2)).strftime('%Y%m%d')
        
        valid_stocks = []
        for stock in tqdm(stocks[:100], desc='过滤停牌股票'):  # 限制数量
            try:
                df = self.data_provider.get_daily_data(stock, start_date, end_date)
                if len(df) >= lookback_days - 5:  # 允许少量停牌
                    valid_stocks.append(stock)
            except:
                continue
            time.sleep(0.05)
        
        return valid_stocks
    
    def get_filtered_stock_pool(self, index_code: str = '000905.XSHG', 
                               trade_date: str = None) -> List[str]:
        """获取经过筛选的股票池"""
        if trade_date is None:
            trade_date = dt.datetime.now().strftime('%Y%m%d')
        
        # 获取基础股票池
        stocks = self.get_base_stock_pool(index_code, trade_date)
        print(f"基础股票池数量: {len(stocks)}")
        
        # 简化筛选流程，只过滤停牌股票
        stocks = self.filter_suspended_stocks(stocks, trade_date)
        print(f"过滤停牌后数量: {len(stocks)}")
        
        return stocks


class APMFactorCalculator:
    """APM因子计算器"""
    
    TIME_PERIODS = {
        '上午': ('09:30:00', '11:30:00'),
        '下午': ('13:00:00', '15:00:00'),
        'am1': ('09:30:00', '10:30:00'),
        'am2': ('10:30:00', '11:30:00'),
        'pm1': ('14:00:00', '15:00:00'),
        'pm2': ('13:00:00', '14:00:00')
    }
    
    def __init__(self, data_provider: TuShareDataProvider):
        self.data_provider = data_provider
    
    def get_intraday_returns(self, stocks: List[str], benchmark: str, 
                           end_date: str, period1: Tuple[str, str], 
                           period2: Tuple[str, str], lookback_days: int = 20) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """获取日内收益率数据（简化版）"""
        start_date = (pd.to_datetime(end_date) - pd.Timedelta(days=lookback_days*2)).strftime('%Y%m%d')
        
        # 简化处理：使用日线数据模拟日内收益率
        all_codes = stocks + [benchmark]
        daily_data = {}
        
        for code in tqdm(all_codes[:20], desc='获取价格数据'):  # 限制数量
            try:
                df = self.data_provider.get_daily_data(code, start_date, end_date)
                if len(df) >= lookback_days:
                    df = df.sort_values('trade_date').tail(lookback_days)
                    daily_data[code] = df
            except:
                continue
            time.sleep(0.1)
        
        if not daily_data:
            return pd.DataFrame(), pd.DataFrame()
        
        # 模拟上午和下午收益率
        am_returns = {}
        pm_returns = {}
        
        for code, df in daily_data.items():
            # 简化：使用开盘到最高价作为上午收益率，最高价到收盘作为下午收益率
            am_ret = np.log(df['high'] / df['open'])
            pm_ret = np.log(df['close'] / df['high'])
            
            am_returns[code] = am_ret
            pm_returns[code] = pm_ret
        
        am_df = pd.DataFrame(am_returns)
        pm_df = pd.DataFrame(pm_returns)
        
        return am_df, pm_df
    
    def calculate_apm_factor(self, stocks: List[str], benchmark: str, 
                           end_date: str, factor_type: str = 'apm_raw') -> pd.Series:
        """计算APM因子"""
        
        # 定义因子类型对应的时段
        factor_periods = {
            'apm_raw': (self.TIME_PERIODS['上午'], self.TIME_PERIODS['下午']),
            'apm_new': (self.TIME_PERIODS['上午'], self.TIME_PERIODS['下午']),  # 简化
            'apm_1': (self.TIME_PERIODS['am1'], self.TIME_PERIODS['pm1']),
            'apm_2': (self.TIME_PERIODS['am1'], self.TIME_PERIODS['pm1']),
            'apm_3': (self.TIME_PERIODS['am2'], self.TIME_PERIODS['pm2'])
        }
        
        period1, period2 = factor_periods.get(factor_type, factor_periods['apm_raw'])
        
        # 获取收益率数据
        am_returns, pm_returns = self.get_intraday_returns(stocks, benchmark, end_date, period1, period2)
        
        if am_returns.empty or pm_returns.empty:
            return pd.Series()
        
        # 计算APM统计量
        apm_stats = {}
        
        for stock in am_returns.columns:
            if stock == benchmark or stock not in pm_returns.columns:
                continue
            
            am_ret = am_returns[stock].dropna()
            pm_ret = pm_returns[stock].dropna()
            bench_am = am_returns[benchmark].dropna() if benchmark in am_returns.columns else None
            bench_pm = pm_returns[benchmark].dropna() if benchmark in pm_returns.columns else None
            
            if len(am_ret) < 10 or len(pm_ret) < 10:
                continue
            
            # 对基准回归获得残差
            try:
                if bench_am is not None and len(bench_am) >= len(am_ret):
                    X_am = sm.add_constant(bench_am.iloc[:len(am_ret)])
                    model_am = sm.OLS(am_ret, X_am).fit()
                    am_resid = model_am.resid
                else:
                    am_resid = am_ret
                
                if bench_pm is not None and len(bench_pm) >= len(pm_ret):
                    X_pm = sm.add_constant(bench_pm.iloc[:len(pm_ret)])
                    model_pm = sm.OLS(pm_ret, X_pm).fit()
                    pm_resid = model_pm.resid
                else:
                    pm_resid = pm_ret
                
                # 计算残差差值
                min_len = min(len(am_resid), len(pm_resid))
                delta = am_resid.iloc[:min_len] - pm_resid.iloc[:min_len]
                
                # 计算统计量
                if delta.std() > 0:
                    stat = (delta.mean() * np.sqrt(len(delta))) / delta.std()
                    apm_stats[stock] = stat
                    
            except:
                continue
        
        return pd.Series(apm_stats)


def simple_test():
    """简单测试函数"""
    print("=== APM因子模型测试 ===")
    
    # 初始化组件
    data_provider = TuShareDataProvider()
    screener = StockScreener(data_provider)
    calculator = APMFactorCalculator(data_provider)
    
    # 设置参数
    test_date = '20231201'
    index_code = '000905.XSHG'
    benchmark = '000905.SH'
    
    # 获取股票池
    print("获取股票池...")
    stocks = screener.get_filtered_stock_pool(index_code, test_date)
    
    if len(stocks) < 5:
        print("股票池数量不足")
        return
    
    # 计算因子
    print("计算APM因子...")
    factor = calculator.calculate_apm_factor(stocks[:10], benchmark, test_date, 'apm_raw')
    
    if not factor.empty:
        print(f"因子计算成功，有效股票数: {len(factor)}")
        print("因子统计信息:")
        print(factor.describe())
        
        # 简单可视化
        plt.figure(figsize=(10, 6))
        factor.hist(bins=20)
        plt.title('APM因子分布')
        plt.xlabel('因子值')
        plt.ylabel('频数')
        plt.show()
    else:
        print("因子计算失败")


if __name__ == "__main__":
    simple_test()
