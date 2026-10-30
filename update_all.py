# -*- coding: utf-8 -*-
"""
============================================
世界杯舆情数据一键更新脚本
============================================
功能：
1. 运行爬虫 → CSV累积（自动标题去重）
2. 运行转换 → 生成merged_all.csv
3. 导入SQL Server → 自动跳过重复URL

运行方式：
python update_all.py
============================================
"""

import os
import sys
import subprocess

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 项目路径（脚本在项目根目录）
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# 脚本路径
SPIDER_SCRIPT = os.path.join(PROJECT_DIR, 'spider', 'world_cup_spider.py')
CONVERTER_SCRIPT = os.path.join(PROJECT_DIR, 'analysis', 'data_converter.py')
IMPORT_SCRIPT = os.path.join(PROJECT_DIR, 'analysis', 'import_to_sqlserver.py')

# 数据文件路径
DATA_DIR = os.path.join(PROJECT_DIR, 'data')
WORLD_CUP_NEWS_CSV = os.path.join(DATA_DIR, 'world_cup_news.csv')
MERGED_ALL_CSV = os.path.join(DATA_DIR, 'merged_all.csv')


def run_script(script_path, step_name):
    """
    运行Python脚本

    参数:
        script_path: 脚本路径
        step_name: 步骤名称

    返回:
        True/False
    """
    print(f"\n{'='*70}")
    print(f"🔄 步骤: {step_name}")
    print(f"{'='*70}")
    print(f"📄 脚本: {os.path.basename(script_path)}")

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=PROJECT_DIR,
            capture_output=False,
            text=True
        )

        if result.returncode == 0:
            print(f"✅ {step_name} 完成")
            return True
        else:
            print(f"❌ {step_name} 失败 (退出码: {result.returncode})")
            return False
    except Exception as e:
        print(f"❌ 执行出错: {e}")
        return False


def show_file_stats():
    """
    显示CSV文件统计信息
    """
    import pandas as pd

    print(f"\n{'='*70}")
    print(f"📊 数据文件状态")
    print(f"{'='*70}")

    # world_cup_news.csv
    if os.path.exists(WORLD_CUP_NEWS_CSV):
        df1 = pd.read_csv(WORLD_CUP_NEWS_CSV, encoding='utf-8-sig')
        print(f"\n📄 world_cup_news.csv:")
        print(f"   数据量: {len(df1)} 条")
    else:
        print(f"\n📄 world_cup_news.csv: 不存在")

    # merged_all.csv
    if os.path.exists(MERGED_ALL_CSV):
        df2 = pd.read_csv(MERGED_ALL_CSV, encoding='utf-8-sig')
        print(f"\n📄 merged_all.csv:")
        print(f"   数据量: {len(df2)} 条")

        # 显示分布
        if 'worldcup' in df2.columns:
            print(f"\n   届次分布:")
            for wc, count in df2['worldcup'].value_counts().items():
                print(f"      {wc}: {count} 条")

        if 'industry' in df2.columns:
            print(f"\n   行业分布:")
            for ind, count in df2['industry'].value_counts().items():
                print(f"      {ind}: {count} 条")
    else:
        print(f"\n📄 merged_all.csv: 不存在")


def main():
    """主函数"""
    print("="*70)
    print("🔄 世界杯舆情数据一键更新")
    print("="*70)
    print("\n📋 更新流程:")
    print("   1️⃣ 运行爬虫 → CSV累积（自动标题去重）")
    print("   2️⃣ 运行转换 → 生成merged_all.csv")
    print("   3️⃣ 导入SQL Server → 自动跳过重复URL")
    print("="*70)

    # 显示当前状态
    show_file_stats()

    # 询问是否继续
    print("\n" + "="*70)
    confirm = input("❓ 是否开始更新？(y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ 已取消")
        return

    # 步骤1：运行爬虫
    print("\n" + "─"*70)
    print("📌 步骤1/3：运行爬虫")
    print("─"*70)
    print("⚠️ 注意：爬虫运行时间较长，请耐心等待...")

    if not run_script(SPIDER_SCRIPT, "爬虫"):
        print("\n❌ 爬虫执行失败，停止更新")
        return

    # 步骤2：运行转换
    print("\n" + "─"*70)
    print("📌 步骤2/3：数据格式转换")
    print("─"*70)

    if not run_script(CONVERTER_SCRIPT, "数据转换"):
        print("\n❌ 数据转换失败，停止更新")
        return

    # 步骤3：导入SQL Server
    print("\n" + "─"*70)
    print("📌 步骤3/3：导入SQL Server")
    print("─"*70)

    if not run_script(IMPORT_SCRIPT, "SQL导入"):
        print("\n❌ SQL导入失败")
        return

    # 完成
    print("\n" + "="*70)
    print("✅ 数据更新完成！")
    print("="*70)

    # 显示最终状态
    show_file_stats()

    print("\n📌 数据存储位置:")
    print(f"   CSV文件: {DATA_DIR}")
    print(f"   SQL Server: 见环境变量 DB_SERVER（默认 localhost\\SQLEXPRESS）")
    print(f"   数据库: worldcup_db")
    print(f"   表名: worldcup_news")
    print("="*70)


if __name__ == '__main__':
    main()
