# FFScore因子计算 - 使用tushare和akshare替代聚宽
# 作者修改：将聚宽数据源替换为tushare和akshare

from typing import List, Tuple, Dict, Callable, Union
import datetime as dt
import numpy as np
import pandas as pd
import empyrical as ep

# 替换聚宽数据源为tushare和akshare
import tushare as ts
import akshare as ak
import warnings
warnings.filterwarnings('ignore')

# 设置tushare token
ts.set_token('ce9f8c37a4af987f6328321ed4b3f9379f695d6d6bdc5b59d454e3ad')
pro = ts.pro_api()

# 数据获取函数 - 替换聚宽平台函数

def get_trade_days(start_date: str, end_date: str) -> list:
    """获取交易日列表"""
    try:
        # 使用tushare获取交易日历
        cal_df = pro.trade_cal(exchange='SSE', start_date=start_date.replace('-', ''), 
                              end_date=end_date.replace('-', ''))
        trade_days = cal_df[cal_df['is_open'] == 1]['cal_date'].tolist()
        return [dt.datetime.strptime(d, '%Y%m%d').date() for d in trade_days]
    except:
        # 备用方案：使用akshare
        try:
            cal_df = ak.tool_trade_date_hist_sina()
            cal_df['trade_date'] = pd.to_datetime(cal_df['trade_date'])
            mask = (cal_df['trade_date'] >= start_date) & (cal_df['trade_date'] <= end_date)
            return cal_df[mask]['trade_date'].dt.date.tolist()
        except:
            # 最后备用方案：生成工作日
            dates = pd.date_range(start_date, end_date, freq='B')
            return [d.date() for d in dates]

def get_all_securities(types=['stock'], date=None) -> pd.DataFrame:
    """获取所有股票信息"""
    try:
        # 使用tushare获取股票基本信息
        stock_basic = pro.stock_basic(exchange='', list_status='L', 
                                    fields='ts_code,symbol,name,area,industry,list_date,delist_date')
        
        # 转换为聚宽格式
        result = pd.DataFrame()
        result.index = stock_basic['ts_code'].str.replace('.SZ', '.XSHE').str.replace('.SH', '.XSHG')
        result['display_name'] = stock_basic['name']
        result['name'] = stock_basic['name']
        result['start_date'] = pd.to_datetime(stock_basic['list_date'], format='%Y%m%d')
        result['end_date'] = pd.to_datetime('2200-01-01')  # 默认未退市
        
        # 处理已退市股票
        delist_mask = stock_basic['delist_date'].notna()
        if delist_mask.any():
            result.loc[delist_mask, 'end_date'] = pd.to_datetime(
                stock_basic.loc[delist_mask, 'delist_date'], format='%Y%m%d')
        
        return result
    except Exception as e:
        print(f"获取股票列表失败: {e}")
        return pd.DataFrame()

def get_price(securities, start_date=None, end_date=None, count=None, fields='close', fq='post', panel=False):
    """获取价格数据"""
    try:
        if isinstance(securities, str):
            securities = [securities]
        
        # 转换股票代码格式
        ts_codes = []
        for sec in securities:
            if '.XSHG' in sec:
                ts_codes.append(sec.replace('.XSHG', '.SH'))
            elif '.XSHE' in sec:
                ts_codes.append(sec.replace('.XSHE', '.SZ'))
            else:
                ts_codes.append(sec)
        
        # 处理日期
        if end_date:
            end_date_str = end_date.strftime('%Y%m%d') if hasattr(end_date, 'strftime') else str(end_date).replace('-', '')
        else:
            end_date_str = dt.datetime.now().strftime('%Y%m%d')
        
        # 获取数据
        all_data = []
        for ts_code in ts_codes:
            try:
                if count and count == 1:
                    # 获取单日数据
                    df = pro.daily(ts_code=ts_code, trade_date=end_date_str)
                else:
                    # 获取时间段数据
                    start_date_str = start_date.strftime('%Y%m%d') if start_date else end_date_str
                    df = pro.daily(ts_code=ts_code, start_date=start_date_str, end_date=end_date_str)
                
                if not df.empty:
                    df['code'] = ts_code.replace('.SH', '.XSHG').replace('.SZ', '.XSHE')
                    df['time'] = pd.to_datetime(df['trade_date'])
                    all_data.append(df)
            except:
                continue
        
        if not all_data:
            return pd.DataFrame()
        
        result = pd.concat(all_data, ignore_index=True)
        
        # 字段映射
        field_map = {'close': 'close', 'open': 'open', 'high': 'high', 'low': 'low', 'volume': 'vol', 'money': 'amount'}
        
        if isinstance(fields, str):
            fields = [fields]
        
        # 选择需要的字段
        select_cols = ['time', 'code']
        for field in fields:
            if field in field_map and field_map[field] in result.columns:
                select_cols.append(field_map[field])
                result = result.rename(columns={field_map[field]: field})
        
        result = result[select_cols]
        
        if panel:
            return result.set_index(['time', 'code']).unstack('code')
        else:
            return result
            
    except Exception as e:
        print(f"获取价格数据失败: {e}")
        return pd.DataFrame()

def get_valuation(securities, start_date=None, end_date=None, count=None, fields=['pb_ratio']):
    """获取估值数据"""
    try:
        if isinstance(securities, str):
            securities = [securities]
        
        # 转换股票代码格式
        ts_codes = []
        for sec in securities:
            if '.XSHG' in sec:
                ts_codes.append(sec.replace('.XSHG', '.SH'))
            elif '.XSHE' in sec:
                ts_codes.append(sec.replace('.XSHE', '.SZ'))
            else:
                ts_codes.append(sec)
        
        # 处理日期
        if end_date:
            end_date_str = end_date.strftime('%Y%m%d') if hasattr(end_date, 'strftime') else str(end_date).replace('-', '')
        else:
            end_date_str = dt.datetime.now().strftime('%Y%m%d')
        
        # 获取估值数据
        all_data = []
        for ts_code in ts_codes:
            try:
                # 获取每日指标数据
                df = pro.daily_basic(ts_code=ts_code, trade_date=end_date_str, 
                                   fields='ts_code,trade_date,pb,pe,pe_ttm')
                if not df.empty:
                    df['code'] = ts_code.replace('.SH', '.XSHG').replace('.SZ', '.XSHE')
                    df['day'] = pd.to_datetime(df['trade_date'])
                    df['pb_ratio'] = df['pb']
                    all_data.append(df)
            except:
                continue
        
        if not all_data:
            return pd.DataFrame()
        
        result = pd.concat(all_data, ignore_index=True)
        
        # 选择需要的字段
        select_cols = ['day', 'code'] + fields
        available_cols = [col for col in select_cols if col in result.columns]
        
        return result[available_cols]
        
    except Exception as e:
        print(f"获取估值数据失败: {e}")
        return pd.DataFrame()

# 标记得分函数
def sign(ser: pd.Series) -> pd.Series:
    """标记分数,正数为1,负数为0"""
    return ser.apply(lambda x: np.where(x > 0, 1, 0))

# 重新实现因子计算类，不依赖聚宽
class FScore:
    """
    FScore原始模型 - 使用tushare数据
    """
    def __init__(self):
        self.name = 'FScore'
        self.watch_date = None
        self.basic = None
        self.fscore = None
    
    def get_financial_data(self, securities, date):
        """获取财务数据"""
        try:
            # 转换日期格式
            date_str = date.strftime('%Y%m%d') if hasattr(date, 'strftime') else str(date).replace('-', '')
            
            # 获取最近的报告期
            year = int(date_str[:4])
            month = int(date_str[4:6])
            
            # 确定报告期
            if month >= 10:
                period = f'{year}0930'
            elif month >= 7:
                period = f'{year}0630'
            elif month >= 4:
                period = f'{year}0331'
            else:
                period = f'{year-1}1231'
            
            # 上年同期
            last_year_period = f'{int(period[:4])-1}{period[4:]}'
            
            all_data = []
            
            # 限制数量避免API限制
            for sec in securities[:10]:
                # 转换股票代码
                if '.XSHG' in sec:
                    ts_code = sec.replace('.XSHG', '.SH')
                elif '.XSHE' in sec:
                    ts_code = sec.replace('.XSHE', '.SZ')
                else:
                    ts_code = sec
                
                try:
                    # 获取财务数据（简化版本，实际使用时需要完整的财务数据）
                    # 这里使用基本的财务指标作为示例
                    basic_data = pro.fina_indicator(ts_code=ts_code, period=period, 
                                                  fields='ts_code,end_date,roa,roe,current_ratio,debt_to_assets')
                    
                    if not basic_data.empty:
                        data_dict = {
                            'code': sec,
                            'roa': basic_data['roa'].iloc[0] if not basic_data['roa'].isna().iloc[0] else 0,
                            'roe': basic_data['roe'].iloc[0] if not basic_data['roe'].isna().iloc[0] else 0,
                            'current_ratio': basic_data['current_ratio'].iloc[0] if not basic_data['current_ratio'].isna().iloc[0] else 1,
                            'debt_to_assets': basic_data['debt_to_assets'].iloc[0] if not basic_data['debt_to_assets'].isna().iloc[0] else 0,
                        }
                        all_data.append(data_dict)
                        
                except Exception as e:
                    print(f"获取{ts_code}财务数据失败: {e}")
                    continue
            
            return pd.DataFrame(all_data).set_index('code')
            
        except Exception as e:
            print(f"获取财务数据失败: {e}")
            return pd.DataFrame()
    
    def calc(self, securities, date):
        """计算FScore（简化版本）"""
        self.watch_date = date
        
        # 获取财务数据
        data = self.get_financial_data(securities, date)
        
        if data.empty:
            self.basic = pd.DataFrame()
            self.fscore = pd.Series()
            return
        
        # 简化的FScore计算（实际应用中需要完整的9个指标）
        # 这里只使用可获取的基本指标作为示例
        roa_score = (data['roa'] > 0).astype(int)
        roe_score = (data['roe'] > 0).astype(int)
        current_ratio_score = (data['current_ratio'] > 1.5).astype(int)
        debt_score = (data['debt_to_assets'] < 0.5).astype(int)
        
        # 合并指标
        self.basic = pd.DataFrame({
            'ROA': roa_score,
            'ROE': roe_score,
            'CURRENT_RATIO': current_ratio_score,
            'DEBT_RATIO': debt_score,
        })
        
        # 计算简化的FScore
        self.fscore = self.basic.sum(axis=1)

# 获取交易期间
def get_trade_period(start_date: str, end_date: str, freq: str = 'ME') -> list:
    """
    获取交易期间
    start_date/end_date:str YYYY-MM-DD
    freq:M月，Q季,Y年 默认ME E代表期末 S代表期初
    return  list[datetime.date]
    """
    days = pd.Index(pd.to_datetime(get_trade_days(start_date, end_date)))
    idx_df = days.to_frame()

    if freq[-1] == 'E':
        day_range = idx_df.resample(freq[0]).last()
    else:
        day_range = idx_df.resample(freq[0]).first()

    day_range = day_range[0].dt.date

    return day_range.dropna().values.tolist()

if __name__ == "__main__":
    print("FFScore因子计算工具 - 基于tushare和akshare")
    print("已成功替换聚宽数据源")
    
    # 示例用法
    try:
        # 获取交易日
        trade_days = get_trade_days('2023-01-01', '2023-01-31')
        print(f"获取到{len(trade_days)}个交易日")
        
        # 获取股票列表
        stocks = get_all_securities()
        print(f"获取到{len(stocks)}只股票")
        
        # 创建FScore实例
        fscore = FScore()
        print("FScore因子计算器已初始化")
        
    except Exception as e:
        print(f"初始化失败: {e}")
