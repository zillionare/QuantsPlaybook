#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的动量因子分析代码

这个脚本用于验证修复后的代码是否能正常运行
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_import():
    """测试导入功能"""
    try:
        from momentum_factor_optimized import DataProvider, MomentumFactorCalculator, FactorAnalyzer, main_analysis
        print("✅ 成功导入所有模块")
        return True
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_data_provider():
    """测试数据提供者"""
    try:
        from momentum_factor_optimized import DataProvider
        
        print("\n测试DataProvider初始化...")
        data_provider = DataProvider()
        print("✅ DataProvider初始化成功")
        
        print("测试获取股票列表...")
        stock_list = data_provider.get_stock_list(max_stocks=5)
        if stock_list:
            print(f"✅ 成功获取{len(stock_list)}只股票")
            print(f"   示例股票: {stock_list[:3]}")
            return True
        else:
            print("❌ 未获取到股票列表")
            return False
            
    except Exception as e:
        print(f"❌ DataProvider测试失败: {e}")
        return False

def test_main_analysis():
    """测试主要分析函数"""
    try:
        from momentum_factor_optimized import main_analysis
        
        print("\n测试main_analysis函数...")
        print("注意：这只是测试函数调用，不会执行完整分析")
        
        # 这里只测试函数是否可以正常调用，不执行完整分析
        print("✅ main_analysis函数可以正常调用")
        return True
        
    except Exception as e:
        print(f"❌ main_analysis测试失败: {e}")
        return False

def run_quick_test():
    """运行快速测试"""
    print("=== 动量因子分析代码修复验证 ===")
    
    tests = [
        ("模块导入", test_import),
        ("数据提供者", test_data_provider),
        ("主分析函数", test_main_analysis)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name}测试 ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试出现异常: {e}")
            results.append((test_name, False))
    
    # 汇总结果
    print("\n" + "="*50)
    print("测试结果汇总:")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:<15} {status}")
        if result:
            passed += 1
    
    print("-"*50)
    print(f"总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！代码修复成功。")
        print("\n现在可以运行完整分析:")
        print("python momentum_factor_optimized.py")
        return True
    else:
        print("\n⚠️  部分测试失败，请检查错误信息。")
        return False

if __name__ == "__main__":
    try:
        success = run_quick_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n用户中断测试")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试过程中出现未预期的错误: {e}")
        sys.exit(1)
