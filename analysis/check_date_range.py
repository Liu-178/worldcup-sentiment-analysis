# -*- coding: utf-8 -*-
"""
检查数据的实际时间范围
"""

import pandas as pd
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_csv('C:/Users/是我无事种芭蕉/PycharmProjects/PythonProject2/worldcup_news_project/data/merged_all.csv', encoding='utf-8-sig')

print("="*60)
print("📊 数据时间范围分析")
print("="*60)

# 2026年数据
df_2026 = df[df['worldcup'] == '2026美加墨']
print(f"\n2026美加墨世界杯数据: {len(df_2026)} 条")

# 查看发布时间分布
print(f"\n2026年发布时间分布:")
time_counts = df_2026['publish_time'].value_counts()
for t, c in time_counts.head(20).items():
    print(f"   {t}: {c} 条")

# 过滤有效时间
df_2026_valid = df_2026[df_2026['publish_time'] != '未知时间']
if len(df_2026_valid) > 0:
    # 按日期排序
    dates = pd.to_datetime(df_2026_valid['publish_time'], errors='coerce')
    valid_dates = dates.dropna()
    if len(valid_dates) > 0:
        print(f"\n2026年有效时间范围:")
        print(f"   最早: {valid_dates.min().strftime('%Y-%m-%d')}")
        print(f"   最晚: {valid_dates.max().strftime('%Y-%m-%d')}")

# 2022年数据
df_2022 = df[df['worldcup'] == '2022卡塔尔']
print(f"\n2022卡塔尔世界杯数据: {len(df_2022)} 条")

# 查看发布时间分布
print(f"\n2022年发布时间分布:")
time_counts_2022 = df_2022['publish_time'].value_counts()
for t, c in time_counts_2022.head(10).items():
    print(f"   {t}: {c} 条")

# 过滤有效时间
df_2022_valid = df_2022[df_2022['publish_time'] != '未知时间']
if len(df_2022_valid) > 0:
    dates_2022 = pd.to_datetime(df_2022_valid['publish_time'], errors='coerce')
    valid_dates_2022 = dates_2022.dropna()
    if len(valid_dates_2022) > 0:
        print(f"\n2022年有效时间范围:")
        print(f"   最早: {valid_dates_2022.min().strftime('%Y-%m-%d')}")
        print(f"   最晚: {valid_dates_2022.max().strftime('%Y-%m-%d')}")

print("\n" + "="*60)
