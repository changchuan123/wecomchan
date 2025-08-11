#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
周报格式测试脚本
用于验证周报Web页面格式修改
"""

import os
import sys
import time
import subprocess

def test_weekly_generation():
    """测试周报生成"""
    print("🧪 测试周报格式修改...")
    
    try:
        # 运行周报脚本
        print("🚀 运行周报脚本...")
        result = subprocess.run(["python3", "整体周报数据.py"], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ 周报脚本运行成功")
            
            # 检查生成的HTML文件
            reports_dir = "reports"
            if os.path.exists(reports_dir):
                weekly_files = [f for f in os.listdir(reports_dir) if f.startswith("overall_weekly_")]
                if weekly_files:
                    latest_weekly = sorted(weekly_files)[-1]
                    file_path = os.path.join(reports_dir, latest_weekly)
                    
                    print(f"📄 最新周报文件: {latest_weekly}")
                    
                    # 检查文件内容中的格式
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 检查格式是否正确
                    format_checks = [
                        ("渠道销售分析中的店铺格式", "销售额: ¥", "（", "件）| 单价: ¥", "，对比期: ¥", "（", "件），环比"),
                        ("TOP店铺排行中的单品格式", "本期: ¥", "（", "件），对比期: ¥", "（", "件），环比"),
                        ("品类销售中的单品格式", "本期: ¥", "（", "件），对比期: ¥", "（", "件），环比")
                    ]
                    
                    all_passed = True
                    for check_name, *patterns in format_checks:
                        # 检查是否包含所有必要的格式元素
                        if all(pattern in content for pattern in patterns):
                            print(f"✅ {check_name}: 格式正确")
                        else:
                            print(f"❌ {check_name}: 格式不正确")
                            all_passed = False
                    
                    if all_passed:
                        print("\n🎉 所有格式检查通过！")
                        print(f"📊 周报文件: {file_path}")
                        return True
                    else:
                        print("\n⚠️ 部分格式检查未通过")
                        return False
                else:
                    print("❌ 未找到周报文件")
                    return False
            else:
                print("❌ reports目录不存在")
                return False
        else:
            print(f"❌ 周报脚本运行失败: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 周报脚本运行超时")
        return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def main():
    """主函数"""
    print("🔧 周报格式测试脚本")
    print("=" * 50)
    
    success = test_weekly_generation()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 格式测试完成 - 所有修改已生效")
    else:
        print("❌ 格式测试失败 - 需要进一步检查")
    
    print("🔧 测试完成")

if __name__ == "__main__":
    main() 