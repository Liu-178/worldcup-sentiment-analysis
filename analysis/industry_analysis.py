# -*- coding: utf-8 -*-
"""
============================================
行业热度统计分析模块
============================================
功能：
1. 统计各行业新闻数量
2. 计算热度占比
3. 生成两届世界杯对比数据
4. 按时间序列统计热度趋势（含模拟数据）
============================================
"""

import pandas as pd
import os
import random
import sys
from datetime import datetime, timedelta

# 设置输出编码为UTF-8（解决Windows控制台编码问题）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ============================================
# 配置参数
# ============================================

PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(PROJECT_DIR, 'data')

# 五大行业
INDUSTRIES = ['餐饮', '旅游', '体彩', '零售', '股市']

# 两届世界杯信息及时间区间
WORLDCUPS = {
    '2022卡塔尔': {
        'key': '2022_qatar',
        'year': 2022,
        'start': '2022-11-20',
        'end': '2022-12-18'
    },
    '2026美加墨': {
        'key': '2026_usmx',
        'year': 2026,
        'start': '2026-06-11',
        'end': '2026-07-06'
    }
}


# ============================================
# 数据加载
# ============================================

def load_merged_data():
    """
    加载合并后的数据

    返回:
        DataFrame 或 None
    """
    filepath = os.path.join(DATA_DIR, 'merged_all.csv')

    if not os.path.exists(filepath):
        print(f"❌ 文件不存在: {filepath}")
        print(f"   请先运行数据清洗模块生成 merged_all.csv")
        return None

    try:
        df = pd.read_csv(filepath, encoding='utf-8-sig')
        print(f"✅ 加载合并数据: {len(df)} 条")
        return df
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        return None


# ============================================
# 行业热度统计
# ============================================

def calculate_industry_stats(df):
    """
    统计各行业新闻数量及热度占比

    参数:
        df: 合并后的数据DataFrame

    返回:
        统计结果DataFrame
    """
    print(f"\n📊 计算各行业热度统计...")

    # 按届次和行业分组统计
    stats_list = []

    for worldcup in df['worldcup'].unique():
        df_worldcup = df[df['worldcup'] == worldcup]
        total_count = len(df_worldcup)

        for industry in INDUSTRIES:
            industry_count = len(df_worldcup[df_worldcup['industry'] == industry])
            percentage = (industry_count / total_count * 100) if total_count > 0 else 0

            stats_list.append({
                'worldcup': worldcup,
                'industry': industry,
                'count': industry_count,
                'total': total_count,
                'percentage': round(percentage, 2)
            })

    stats_df = pd.DataFrame(stats_list)

    # 打印统计结果
    print(f"\n{'='*60}")
    print(f"📈 行业热度对比统计")
    print(f"{'='*60}")

    for worldcup in stats_df['worldcup'].unique():
        wc_data = stats_df[stats_df['worldcup'] == worldcup]
        print(f"\n【{worldcup}】")
        print(f"{'─'*40}")

        for _, row in wc_data.sort_values('count', ascending=False).iterrows():
            print(f"  {row['industry']}: {row['count']} 条 ({row['percentage']}%)")

    return stats_df


def generate_comparison_table(stats_df):
    """
    生成两届世界杯行业热度对比表

    参数:
        stats_df: 统计结果DataFrame

    返回:
        对比表DataFrame
    """
    print(f"\n📊 生成对比表...")

    # 提取两届数据
    df_2022 = stats_df[stats_df['worldcup'] == '2022卡塔尔'].copy()
    df_2026 = stats_df[stats_df['worldcup'] == '2026美加墨'].copy()

    # 重命名列
    df_2022 = df_2022[['industry', 'count', 'percentage']].rename(columns={
        'count': 'count_2022',
        'percentage': 'percent_2022'
    })

    df_2026 = df_2026[['industry', 'count', 'percentage']].rename(columns={
        'count': 'count_2026',
        'percentage': 'percent_2026'
    })

    # 合并对比表
    comparison_df = pd.merge(df_2022, df_2026, on='industry')

    # 计算变化
    comparison_df['count_change'] = comparison_df['count_2026'] - comparison_df['count_2022']
    comparison_df['percent_change'] = comparison_df['percent_2026'] - comparison_df['percent_2022']

    # 打印对比表
    print(f"\n{'='*80}")
    print(f"📊 两届世界杯行业热度对比表")
    print(f"{'='*80}")
    print(f"\n{'行业':<8} {'2022数量':>10} {'2022占比':>10} {'2026数量':>10} {'2026占比':>10} {'数量变化':>10}")
    print(f"{'─'*80}")

    for _, row in comparison_df.iterrows():
        change_symbol = '↑' if row['count_change'] > 0 else ('↓' if row['count_change'] < 0 else '-')
        print(f"{row['industry']:<8} {row['count_2022']:>10} {row['percent_2022']:>10}% {row['count_2026']:>10} {row['percent_2026']:>10}% {row['count_change']:>9}{change_symbol}")

    return comparison_df


# ============================================
# 时间序列统计（含模拟数据生成）
# ============================================

def calculate_timeline_stats(df):
    """
    按日期统计热度趋势
    如果无有效时间数据，则生成模拟的时间序列

    参数:
        df: 数据DataFrame

    返回:
        时间序列统计DataFrame
    """
    print(f"\n📊 计算时间序列热度...")

    # 尝试使用真实时间数据
    df_valid = df[df['publish_time'] != '未知时间'].copy() if 'publish_time' in df.columns else df.copy()

    if len(df_valid) == 0 or 'publish_time' not in df.columns:
        print(f"⚠️ 无有效时间数据，将生成模拟时间序列数据")
        return generate_simulated_timeline(df)

    # 使用真实时间数据
    timeline_list = []

    for worldcup in df_valid['worldcup'].unique():
        df_wc = df_valid[df_valid['worldcup'] == worldcup]

        for date in df_wc['publish_time'].unique():
            df_date = df_wc[df_wc['publish_time'] == date]

            for industry in INDUSTRIES:
                count = len(df_date[df_date['industry'] == industry])
                if count > 0:
                    timeline_list.append({
                        'worldcup': worldcup,
                        'date': date,
                        'industry': industry,
                        'count': count
                    })

    if timeline_list:
        timeline_df = pd.DataFrame(timeline_list)
        timeline_df = timeline_df.sort_values(['worldcup', 'date', 'industry'])
        timeline_df = timeline_df.reset_index(drop=True)

        print(f"✅ 使用真实时间数据生成时间序列")
        return timeline_df

    # 无真实数据，生成模拟数据
    return generate_simulated_timeline(df)


def generate_simulated_timeline(df):
    """
    生成模拟的时间序列数据（基于世界杯实际日期区间）

    参数:
        df: 数据DataFrame（用于获取各行业数量比例）

    返回:
        模拟时间序列DataFrame
    """
    print(f"🔧 正在生成模拟时间序列数据...")

    timeline_list = []

    for worldcup, info in WORLDCUPS.items():
        # 获取该届世界杯数据
        df_wc = df[df['worldcup'] == worldcup] if 'worldcup' in df.columns else df
        total_count = len(df_wc)

        # 解析日期范围
        start_date = datetime.strptime(info['start'], '%Y-%m-%d')
        end_date = datetime.strptime(info['end'], '%Y-%m-%d')

        # 计算日期范围天数
        days = (end_date - start_date).days + 1

        print(f"\n【{worldcup}】")
        print(f"  生成日期范围: {info['start']} ~ {info['end']} ({days} 天)")

        # 为每个行业生成每日数据
        for industry in INDUSTRIES:
            # 获取该行业的总数
            industry_count = len(df_wc[df_wc['industry'] == industry]) if 'industry' in df_wc.columns else total_count // 5
            daily_avg = industry_count / days

            for day_offset in range(days):
                date = start_date + timedelta(days=day_offset)
                date_str = date.strftime('%Y-%m-%d')

                # 模拟每日波动（随机增减）
                variance = random.uniform(0.5, 1.5)
                count = int(daily_avg * variance)

                # 确保至少有1条（模拟数据）
                count = max(1, count)

                timeline_list.append({
                    'worldcup': worldcup,
                    'date': date_str,
                    'industry': industry,
                    'count': count
                })

    timeline_df = pd.DataFrame(timeline_list)
    timeline_df = timeline_df.sort_values(['worldcup', 'date', 'industry'])
    timeline_df = timeline_df.reset_index(drop=True)

    print(f"\n✅ 模拟时间序列生成完成: {len(timeline_df)} 条记录")

    # 打印概览
    print(f"\n{'='*60}")
    print(f"📈 时间序列统计概览")
    print(f"{'='*60}")

    for worldcup in timeline_df['worldcup'].unique():
        wc_data = timeline_df[timeline_df['worldcup'] == worldcup]
        unique_dates = wc_data['date'].unique()

        print(f"\n【{worldcup}】")
        print(f"  统计天数: {len(unique_dates)} 天")
        print(f"  日期范围: {min(unique_dates)} ~ {max(unique_dates)}")
        print(f"  总记录数: {len(wc_data)} 条")

    return timeline_df


def calculate_daily_total(timeline_df):
    """
    计算每日总热度（所有行业合计）

    参数:
        timeline_df: 时间序列DataFrame

    返回:
        每日总热度DataFrame
    """
    if timeline_df is None or timeline_df.empty:
        print(f"⚠️ 无时间序列数据")
        return None

    # 按届次和日期汇总
    daily_total = timeline_df.groupby(['worldcup', 'date'])['count'].sum().reset_index()
    daily_total = daily_total.rename(columns={'count': 'total_count'})
    daily_total = daily_total.sort_values(['worldcup', 'date'])

    print(f"\n✅ 每日热度汇总完成: {len(daily_total)} 条记录")

    return daily_total


# ============================================
# 数据保存
# ============================================

def save_stats_to_csv(stats_df, filename):
    """
    保存统计结果到CSV

    参数:
        stats_df: 统计DataFrame
        filename: 文件名
    """
    if stats_df is None or (hasattr(stats_df, 'empty') and stats_df.empty):
        print(f"⚠️ 无数据可保存: {filename}")
        return

    filepath = os.path.join(DATA_DIR, filename)
    stats_df.to_csv(filepath, index=False, encoding='utf-8-sig')
    print(f"✅ 保存成功: {filepath}")


# ============================================
# 统计报告生成
# ============================================

def generate_summary_report(stats_df, comparison_df, timeline_df):
    """
    生成统计摘要报告

    参数:
        stats_df: 行业统计
        comparison_df: 对比表
        timeline_df: 时间序列
    """
    print(f"\n{'='*80}")
    print(f"📊 行业热度分析报告摘要")
    print(f"{'='*80}")

    # 1. 整体数据量
    print(f"\n【数据量统计】")
    for worldcup in stats_df['worldcup'].unique():
        wc_data = stats_df[stats_df['worldcup'] == worldcup]
        total = wc_data['total'].iloc[0]
        print(f"  {worldcup}: {total} 条新闻")

    # 2. 热门行业排名
    print(f"\n【热门行业排名】")
    for worldcup in stats_df['worldcup'].unique():
        wc_data = stats_df[stats_df['worldcup'] == worldcup]
        top_industry = wc_data.loc[wc_data['count'].idxmax()]
        print(f"  {worldcup} 热门行业: {top_industry['industry']} ({top_industry['count']}条, {top_industry['percentage']}%)")

    # 3. 变化趋势分析
    if comparison_df is not None and not comparison_df.empty:
        print(f"\n【热度变化分析】")

        # 上升最多的行业
        top_increase = comparison_df.loc[comparison_df['count_change'].idxmax()]
        print(f"  热度上升最多: {top_increase['industry']} (增加 {int(top_increase['count_change'])} 条)")

        # 下降最多的行业
        top_decrease = comparison_df.loc[comparison_df['count_change'].idxmin()]
        print(f"  度下降最多: {top_decrease['industry']} (减少 {abs(int(top_decrease['count_change']))} 条)")

    # 4. 时间分布特征
    if timeline_df is not None and not timeline_df.empty:
        print(f"\n【时间分布特征】")

        for worldcup in timeline_df['worldcup'].unique():
            wc_data = timeline_df[timeline_df['worldcup'] == worldcup]

            # 找出热度最高的日期
            daily_sum = wc_data.groupby('date')['count'].sum()
            peak_date = daily_sum.idxmax()
            peak_count = int(daily_sum.max())

            print(f"  {worldcup} 热度高峰: {peak_date} ({peak_count} 条)")


# ============================================
# 主函数
# ============================================

def main():
    """
    主函数 - 执行行业热度统计分析
    """
    print("="*80)
    print("📊 行业热度统计分析模块")
    print("="*80)

    # 1. 加载合并数据
    print(f"\n📌 步骤1: 加载数据")
    df = load_merged_data()

    if df is None or df.empty:
        print(f"\n⚠️ 请先运行数据清洗模块")
        return

    # 检查必要字段
    required_cols = ['worldcup', 'industry']
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        print(f"❌ 缺少必要字段: {missing_cols}")
        return

    # 2. 计算行业热度统计
    print(f"\n📌 步骤2: 计算行业热度统计")
    stats_df = calculate_industry_stats(df)
    save_stats_to_csv(stats_df, 'industry_stats.csv')

    # 3. 生成对比表
    print(f"\n📌 步骤3: 生成对比表")
    comparison_df = generate_comparison_table(stats_df)
    save_stats_to_csv(comparison_df, 'industry_comparison.csv')

    # 4. 计算时间序列统计
    print(f"\n📌 步骤4: 计算时间序列统计")
    timeline_df = calculate_timeline_stats(df)
    save_stats_to_csv(timeline_df, 'timeline_stats.csv')

    # 5. 计算每日总热度
    print(f"\n📌 步骤5: 计算每日总热度")
    daily_total = calculate_daily_total(timeline_df)
    save_stats_to_csv(daily_total, 'daily_total.csv')

    # 6. 生成摘要报告
    print(f"\n📌 步骤6: 生成统计摘要")
    generate_summary_report(stats_df, comparison_df, timeline_df)

    # 完成提示
    print(f"\n{'='*80}")
    print(f"🎉 行业热度统计分析完成！")
    print(f"{'='*80}")
    print(f"\n📁 生成的文件:")
    print(f"   • industry_stats.csv      - 行业热度统计")
    print(f"   • industry_comparison.csv - 两届对比表")
    print(f"   • timeline_stats.csv      - 时间序列统计")
    print(f"   • daily_total.csv         - 每日总热度")
    print(f"\n💡 下一步: 运行词云生成模块 (wordcloud_generator.py)")


if __name__ == '__main__':
    # 设置随机种子以获得可重复的结果
    random.seed(42)
    main()