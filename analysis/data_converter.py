# -*- coding: utf-8 -*-
"""
============================================
数据格式转换模块（步骤4）
============================================
功能：
1. 将新爬取数据转换为系统标准格式
2. 字段名映射
3. 年份/行业格式转换
4. 生成merged_all.csv供系统使用
============================================
"""

import pandas as pd
import os
import re
from datetime import datetime

# ============================================
# 配置参数
# ============================================

PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(PROJECT_DIR, 'data')

INPUT_FILE = 'world_cup_news.csv'
OUTPUT_FILE = 'merged_all.csv'


# ============================================
# 字段映射
# ============================================

# 新数据列名 → 系统标准列名
COLUMN_MAPPING = {
    '标题': 'title',
    '原文链接': 'url',
    '媒体来源': 'source',
    '发布时间': 'publish_time',
    '正文摘要': 'summary',
    '所属行业': 'industry',
    '所属年份': 'year_raw'
}


# ============================================
# 转换函数
# ============================================

def convert_year_to_worldcup(row):
    """
    将年份转换为届次名称（增强版：从标题、时间、URL多重推断）

    参数:
        row: 数据行（包含title, publish_time, url, year_raw等字段）

    返回:
        届次名称: '2022卡塔尔' 或 '2026美加墨'
    """
    # 1. 首先检查明确的年份字段
    year_raw = row.get('year_raw', '')
    if pd.notna(year_raw) and str(year_raw).strip() not in ['未知', '', 'nan']:
        year_str = str(year_raw).strip()
        year_match = re.search(r'(\d{4})', year_str)
        if year_match:
            year_num = int(year_match.group(1))
            if year_num == 2022:
                return '2022卡塔尔'
            elif year_num == 2026:
                return '2026美加墨'
            elif year_num < 2022:
                return '2022卡塔尔'
            elif year_num > 2022:
                return '2026美加墨'

    # 2. 从标题推断
    title = str(row.get('title', ''))

    # 2022卡塔尔关键词
    qatar_keywords = ['卡塔尔', '2022', '卡塔尔世界杯', '俄罗斯世界杯', '2018']
    for kw in qatar_keywords:
        if kw in title:
            if kw == '2018' or '俄罗斯' in title:
                return '2022卡塔尔'  # 历史数据归到2022
            return '2022卡塔尔'

    # 2026美加墨关键词
    usmx_keywords = ['美加墨', '2026', '美加墨世界杯', '美国世界杯', '北美世界杯']
    for kw in usmx_keywords:
        if kw in title:
            return '2026美加墨'

    # 3. 从发布时间推断
    publish_time = str(row.get('publish_time', ''))

    # 检查时间中的年份
    time_year_match = re.search(r'202[26]', publish_time)
    if time_year_match:
        year_in_time = time_year_match.group(0)
        if year_in_time == '2022':
            return '2022卡塔尔'
        elif year_in_time == '2026':
            return '2026美加墨'

    # 检查月份日期（2022世界杯在11-12月，2026世界杯在6-7月）
    if '11月' in publish_time or '12月' in publish_time or '2022-11' in publish_time or '2022-12' in publish_time:
        return '2022卡塔尔'
    if '6月' in publish_time or '7月' in publish_time or '2026-06' in publish_time or '2026-07' in publish_time:
        return '2026美加墨'

    # 4. 从URL推断
    url = str(row.get('url', ''))

    # URL中的年份
    url_year_match = re.search(r'202[26]', url)
    if url_year_match:
        year_in_url = url_year_match.group(0)
        if year_in_url == '2022':
            return '2022卡塔尔'
        elif year_in_url == '2026':
            return '2026美加墨'

    # URL中的日期格式
    if '/2022-' in url or '/202211' in url or '/202212' in url:
        return '2022卡塔尔'
    if '/2026-' in url or '/202606' in url or '/202607' in url:
        return '2026美加墨'

    # 5. 默认规则：基于文章ID推断（百家号文章ID包含时间信息）
    # 百家号ID格式：id=1750xxxxx（1750开头的大多是2022年）
    baijiahao_match = re.search(r'id=(\d+)', url)
    if baijiahao_match:
        article_id = baijiahao_match.group(1)
        if article_id.startswith('1750'):  # 1750开头 = 2022年11-12月
            return '2022卡塔尔'
        elif article_id.startswith('177'):  # 177开头 = 2023年（归类到2026）
            return '2026美加墨'

    # 6. 无法推断时，默认归到2026（当前正在举办）
    return '2026美加墨'


def normalize_industry(industry_value):
    """
    标准化行业标签

    参数:
        industry_value: 行业值（可能是单个行业或多个行业逗号分隔）

    返回:
        单个主要行业
    """
    if pd.isna(industry_value):
        return '餐饮'  # 默认归类

    industry_str = str(industry_value).strip()

    # 如果包含多个行业，取第一个
    if ',' in industry_str:
        industries = [i.strip() for i in industry_str.split(',')]
        return industries[0] if industries else '餐饮'

    # 统一行业名称
    if '股市' in industry_str or '财经' in industry_str:
        return '股市'

    return industry_str


def convert_data():
    """
    转换数据格式并生成merged_all.csv
    """
    print("="*60)
    print("📊 数据格式转换（步骤4）")
    print("="*60)

    # 1. 加载新数据
    input_path = os.path.join(DATA_DIR, INPUT_FILE)
    if not os.path.exists(input_path):
        print(f"❌ 输入文件不存在: {input_path}")
        return False

    df = pd.read_csv(input_path, encoding='utf-8-sig')
    print(f"✅ 加载新数据: {len(df)} 条")
    print(f"   列名: {list(df.columns)}")

    # 2. 重命名列
    df = df.rename(columns=COLUMN_MAPPING)
    print(f"✅ 列名重命名完成")

    # 3. 转换年份 → 届次（使用增强版函数，传入整行数据）
    df['worldcup'] = df.apply(convert_year_to_worldcup, axis=1)
    print(f"✅ 年份转换完成（增强推断）")

    # 4. 标准化行业
    df['industry'] = df['industry'].apply(normalize_industry)
    print(f"✅ 行业标准化完成")

    # 5. 处理空摘要
    if 'summary' in df.columns:
        df['summary'] = df.apply(
            lambda row: row['title'][:50] + '...' if pd.isna(row['summary']) or row['summary'] == '' else row['summary'],
            axis=1
        )
    else:
        df['summary'] = df['title'].apply(lambda x: x[:50] + '...' if len(x) > 50 else x)

    print(f"✅ 摘要填充完成")

    # 6. 标准化时间
    def parse_time(time_str):
        if pd.isna(time_str) or time_str == '未知时间':
            return '未知时间'

        time_str = str(time_str).strip()

        # 处理相对时间
        if re.search(r'\d+小时前|\d+分钟前|刚刚', time_str):
            return datetime.now().strftime('%Y-%m-%d')
        if '昨天' in time_str:
            return (datetime.now() - pd.Timedelta(days=1)).strftime('%Y-%m-%d')
        if re.search(r'\d+天前', time_str):
            days_match = re.search(r'(\d+)天前', time_str)
            if days_match:
                days = int(days_match.group(1))
                return (datetime.now() - pd.Timedelta(days=days)).strftime('%Y-%m-%d')

        # 处理标准时间格式
        patterns = [
            (r'(\d{4})-(\d{1,2})-(\d{1,2})', '%Y-%m-%d'),
            (r'(\d{4})年(\d{1,2})月(\d{1,2})日', '%Y年%m月%d日'),
            (r'(\d{4})/(\d{1,2})/(\d{1,2})', '%Y/%m/%d'),
        ]

        for pattern, fmt in patterns:
            match = re.search(pattern, time_str)
            if match:
                try:
                    date_part = match.group(0)
                    date_obj = datetime.strptime(date_part, fmt)
                    return date_obj.strftime('%Y-%m-%d')
                except:
                    continue

        return '未知时间'

    df['publish_time'] = df['publish_time'].apply(parse_time)
    print(f"✅ 时间标准化完成")

    # 7. 添加keywords列（空列，系统需要）
    df['keywords'] = ''

    # 8. 去重
    original_count = len(df)
    df = df.drop_duplicates(subset=['title'], keep='first')
    removed_count = original_count - len(df)
    print(f"✅ 去重: 移除 {removed_count} 条重复数据")

    # 9. 保存
    output_path = os.path.join(DATA_DIR, OUTPUT_FILE)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"✅ 保存成功: {output_path}")

    # 10. 统计
    print(f"\n{'='*60}")
    print(f"📊 转换后数据统计")
    print(f"{'='*60}")
    print(f"总数据量: {len(df)} 条")

    print(f"\n【届次分布】")
    for worldcup, count in df['worldcup'].value_counts().items():
        print(f"  {worldcup}: {count} 条 ({count/len(df)*100:.1f}%)")

    print(f"\n【行业分布】")
    for industry, count in df['industry'].value_counts().items():
        print(f"  {industry}: {count} 条 ({count/len(df)*100:.1f}%)")

    print(f"\n【时间分布】")
    for time_val, count in df['publish_time'].value_counts().head(10).items():
        print(f"  {time_val}: {count} 条")

    print(f"\n✅ 步骤4.2 完成！")
    return True


if __name__ == '__main__':
    convert_data()