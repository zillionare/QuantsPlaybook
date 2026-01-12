#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FFScore因子计算示例 - 使用tushare和akshare
演示如何使用新的数据源实现FFScore因子计算

作者: 修改自原聚宽版本
日期: 2024年
"""

import pandas as pd
import numpy as np
import datetime as dt
from FFScore_tushare import FScore, get_trade_period, get_all_securities, get_price, get_valuation
import time

def demo_basic_usage():
    """基本使用示例"""
    print("=== FFScore因子计算基本使用示例 ===")
    
    # 1. 获取交易日
    print("\n1. 获取交易日...")
    try:
        trade_days = get_trade_period('2023-01-01', '2023-03-31', 'M')
        print(f"获取到{len(trade_days)}个月末交易日: {trade_days}")
    except Exception as e:
        print(f"获取交易日失败: {e}")
        return
    
    # 2. 获取股票池
    print("\n2. 获取股票基本信息...")
    try:
        all_stocks = get_all_securities()
        print(f"获取到{len(all_stocks)}只股票")
        # 选择前10只股票作为示例
        sample_stocks = all_stocks.index[:10].tolist()
        print(f"示例股票: {sample_stocks}")
    except Exception as e:
        print(f"获取股票信息失败: {e}")
        return
    
    # 3. 创建FScore实例并计算
    print("\n3. 计算FScore因子...")
    fscore = FScore()
    
    results = []
    for i, trade_date in enumerate(trade_days):
        print(f"\n计算日期: {trade_date} ({i+1}/{len(trade_days)})")
        
        try:
            # 计算FScore
            fscore.calc(sample_stocks, trade_date)
            
            if not fscore.fscore.empty:
                print(f"成功计算{len(fscore.fscore)}只股票的FScore")
                print(f"FScore分布: {fscore.fscore.describe()}")
                
                # 保存结果
                result_df = pd.DataFrame({
                    'date': trade_date,
                    'code': fscore.fscore.index,
                    'fscore': fscore.fscore.values
                })
                results.append(result_df)
            else:
                print("未获取到有效数据")
                
        except Exception as e:
            print(f"计算失败: {e}")
        
        # 添加延时避免API限制
        time.sleep(1)
    
    # 4. 汇总结果
    if results:
        print("\n4. 汇总结果...")
        final_results = pd.concat(results, ignore_index=True)
        print(f"总计算结果: {len(final_results)}条记录")
        print("\n结果预览:")
        print(final_results.head(10))
        
        # 保存到文件
        final_results.to_csv('fscore_results.csv', index=False)
        print("\n结果已保存到 fscore_results.csv")
    else:
        print("\n未获取到任何有效结果")

def demo_price_data():
    """价格数据获取示例"""
    print("\n=== 价格数据获取示例 ===")
    
    # 示例股票
    stocks = ['000001.XSHE', '000002.XSHE', '600000.XSHG']
    end_date = dt.date(2023, 12, 29)
    
    try:
        # 获取单日价格数据
        print("获取单日价格数据...")
        price_data = get_price(stocks, end_date=end_date, count=1, fields='close')
        print(price_data)
        
        # 获取时间段价格数据
        print("\n获取时间段价格数据...")
        start_date = dt.date(2023, 12, 1)
        price_series = get_price(stocks, start_date=start_date, end_date=end_date, fields=['open', 'close'])
        print(f"获取到{len(price_series)}条价格记录")
        print(price_series.head())
        
    except Exception as e:
        print(f"获取价格数据失败: {e}")

def demo_valuation_data():
    """估值数据获取示例"""
    print("\n=== 估值数据获取示例 ===")
    
    stocks = ['000001.XSHE', '000002.XSHE']
    end_date = dt.date(2023, 12, 29)
    
    try:
        valuation_data = get_valuation(stocks, end_date=end_date, fields=['pb_ratio'])
        print("估值数据:")
        print(valuation_data)
        
    except Exception as e:
        print(f"获取估值数据失败: {e}")

def demo_fscore_analysis():
    """FScore因子分析示例"""
    print("\n=== FScore因子分析示例 ===")
    
    # 读取之前保存的结果
    try:
        results = pd.read_csv('fscore_results.csv')
        results['date'] = pd.to_datetime(results['date'])
        
        print("FScore统计分析:")
        print(f"数据期间: {results['date'].min()} 到 {results['date'].max()}")
        print(f"股票数量: {results['code'].nunique()}")
        print(f"总记录数: {len(results)}")
        
        print("\nFScore分布:")
        print(results['fscore'].value_counts().sort_index())
        
        print("\nFScore描述性统计:")
        print(results['fscore'].describe())
        
        # 按日期分组分析
        print("\n各期FScore平均值:")
        date_analysis = results.groupby('date')['fscore'].agg(['mean', 'std', 'count'])
        print(date_analysis)
        
        # 高分股票分析
        high_score_stocks = results[results['fscore'] >= 3]
        if not high_score_stocks.empty:
            print(f"\n高分股票(FScore>=3): {len(high_score_stocks)}只")
            print("高分股票列表:")
            print(high_score_stocks.groupby('code')['fscore'].agg(['mean', 'count']).sort_values('mean', ascending=False))
        
    except FileNotFoundError:
        print("未找到结果文件，请先运行基本使用示例")
    except Exception as e:
        print(f"分析失败: {e}")

def main():
    """主函数"""
    print("FFScore因子计算示例程序")
    print("=" * 50)
    
    # 检查tushare token设置
    try:
        import tushare as ts
        pro = ts.pro_api()
        # 测试API连接
        test_data = pro.trade_cal(exchange='SSE', start_date='20231201', end_date='20231201')
        if test_data.empty:
            print("警告: tushare API可能未正确配置")
        else:
            print("tushare API连接正常")
    except Exception as e:
        print(f"tushare配置检查失败: {e}")
        print("请确保已正确设置tushare token")
        return
    
    # 运行示例
    try:
        # 基本使用示例
        demo_basic_usage()
        
        # 价格数据示例
        demo_price_data()
        
        # 估值数据示例
        demo_valuation_data()
        
        # 因子分析示例
        demo_fscore_analysis()
        
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"\n程序执行出错: {e}")
    
    print("\n示例程序执行完成")

if __name__ == "__main__":
    main()
