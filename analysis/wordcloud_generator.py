# -*- coding: utf-8 -*-
"""
============================================
词频分析与词云生成模块
============================================
功能：
1. jieba中文分词
2. 停用词过滤
3. 词频统计TOP50
4. 生成词云图片
============================================
"""

import pandas as pd
import jieba
import jieba.analyse
from wordcloud import WordCloud
import os
from collections import Counter
import matplotlib.pyplot as plt

# ============================================
# 配置参数
# ============================================

PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(PROJECT_DIR, 'data')
OUTPUT_DIR = os.path.join(PROJECT_DIR, 'web', 'static', 'images')

# 停用词列表（世界杯相关常见无意义词）
STOPWORDS = set([
    # 标点符号
    '，', '。', '！', '？', '、', '；', '：', '"', '"', ''', ''',
    '（', '）', '【', '】', '《', '》', '…', '—', '·',

    # 常见虚词
    '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这',
    '他', '她', '它', '们', '这个', '那个', '什么', '怎么', '为什么', '哪', '哪里', '哪个',

    # 时间词
    '年', '月', '日', '时', '分', '秒', '今天', '昨天', '明天', '前天', '后天',

    # 数量词
    '一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
    '百', '千', '万', '亿', '个', '只', '些', '每', '各',

    # 网络常用词
    '据悉', '报道', '记者', '消息', '显示', '表示', '认为', '可能', '已经', '可以', '但是', '因为', '所以', '如果', '或者', '以及', '还是', '就是', '这样',

    # 体育新闻常见无意义词
    '比赛', '进行', '将于', '本次', '本届', '上届', '下届', '首次', '再次',

    # 单字（过滤掉大多数单字）
    '能', '把', '被', '让', '给', '从', '向', '对', '与', '及', '等', '之', '其', '为', '以',

    # 其他
    '责任编辑', '编辑', '来源', '作者', '发布', '转载', '标签',
])

# 需要保留的关键词（避免被误过滤）
KEEP_WORDS = [
    '世界杯', '足球', '球迷', '球队', '球员', '教练', '裁判',
    '冠军', '决赛', '半决赛', '小组赛', '淘汰赛', '进球',
    '卡塔尔', '美加墨', '阿根廷', '巴西', '德国', '法国', '英格兰', '西班牙',
    '彩票', '足彩', '竞彩', '投注', '赔率',
    '酒店', '旅游', '机票', '签证',
    '夜宵', '聚餐', '外卖', '烧烤', '啤酒',
    '周边', '纪念品', '吉祥物', '球衣',
    '概念股', '赞助商', '体育经济',
]


# ============================================
# 数据加载
# ============================================

def load_data(filename):
    """
    加载CSV数据
    """
    filepath = os.path.join(DATA_DIR, filename)

    if not os.path.exists(filepath):
        print(f"❌ 文件不存在: {filepath}")
        return None

    try:
        df = pd.read_csv(filepath, encoding='utf-8-sig')
        print(f"✅ 加载成功: {filename} ({len(df)} 条)")
        return df
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        return None


# ============================================
# 分词处理
# ============================================

def extract_text_from_df(df):
    """
    从DataFrame中提取所有文本内容

    参数:
        df: 数据DataFrame

    返回:
        合并后的文本字符串
    """
    text_parts = []

    # 提取标题
    if 'title' in df.columns:
        titles = df['title'].dropna().tolist()
        text_parts.extend(titles)

    # 提取摘要
    if 'summary' in df.columns:
        summaries = df['summary'].dropna().tolist()
        text_parts.extend(summaries)

    # 合并为一个字符串
    full_text = ' '.join(text_parts)

    print(f"📝 提取文本: {len(full_text)} 字符")

    return full_text


def segment_text(text):
    """
    使用jieba进行中文分词

    参数:
        text: 文本字符串

    返回:
        词列表
    """
    print(f"🔍 进行分词...")

    # 使用jieba精确模式分词
    words = jieba.lcut(text)

    # 过滤停用词和短词
    filtered_words = []
    for word in words:
        word = word.strip()

        # 过滤条件
        if len(word) < 2:  # 过滤单字
            continue
        if word in STOPWORDS:  # 过滤停用词
            continue
        if word.isdigit():  # 过滤纯数字
            continue
        if all(c in '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ' for c in word):
            continue  # 过滤纯英文数字

        filtered_words.append(word)

    print(f"✅ 分词完成: {len(filtered_words)} 个有效词")

    return filtered_words


def calculate_word_frequency(words, top_n=100):
    """
    计算词频

    参数:
        words: 词列表
        top_n: 返回前N个高频词

    返回:
        词频字典
    """
    # 统计词频
    word_counts = Counter(words)

    # 获取前N个高频词
    top_words = word_counts.most_common(top_n)

    # 转换为字典
    freq_dict = dict(top_words)

    print(f"📊 词频统计: 前{top_n}个高频词")
    print(f"{'─'*40}")

    for i, (word, count) in enumerate(top_words[:20], 1):
        print(f"  {i:2}. {word}: {count}")

    return freq_dict


def save_word_frequency(freq_dict, filename):
    """
    保存词频统计到CSV - 至少保存TOP30数据

    ⚠️ 确保CSV文件包含至少30条数据，不截断
    """
    if not freq_dict:
        print(f"⚠️ 无词频数据")
        return

    # ⚠️ 保存全部数据（确保至少30条），不截断
    df = pd.DataFrame([
        {'rank': i+1, 'word': word, 'count': count}
        for i, (word, count) in enumerate(sorted(freq_dict.items(), key=lambda x: x[1], reverse=True))
    ])

    # 确保至少有30条数据
    if len(df) < 30:
        print(f"⚠️ 词频数据不足30条，当前仅有{len(df)}条")

    filepath = os.path.join(DATA_DIR, filename)
    df.to_csv(filepath, index=False, encoding='utf-8-sig')

    print(f"✅ 词频保存: {filepath} ({len(df)} 条数据)")


# ============================================
# 词云生成
# ============================================

def generate_wordcloud(freq_dict, output_filename, title='词云图'):
    """
    生成词云图片

    参数:
        freq_dict: 词频字典
        output_filename: 输出文件名
        title: 词云标题
    """
    if not freq_dict:
        print(f"⚠️ 无数据，无法生成词云")
        return

    print(f"\n🎨 生成词云: {output_filename}")

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    try:
        # 创建词云对象
        # 使用系统中文字体（Windows）
        font_path = 'C:/Windows/Fonts/simhei.ttf'  # 黑体

        if not os.path.exists(font_path):
            font_path = 'C:/Windows/Fonts/msyh.ttc'  # 微软雅黑

        if not os.path.exists(font_path):
            font_path = None  # 使用默认字体

        wordcloud = WordCloud(
            width=800,
            height=600,
            background_color='white',
            font_path=font_path,
            max_words=100,
            max_font_size=150,
            min_font_size=10,
            colormap='viridis',  # 配色方案
            prefer_horizontal=0.7,
            margin=10
        )

        # 从词频生成词云
        wordcloud.generate_from_frequencies(freq_dict)

        # 保存图片
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        wordcloud.to_file(output_path)

        print(f"✅ 词云保存: {output_path}")

        # 显示词云（可选）
        try:
            plt.figure(figsize=(10, 8))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.title(title, fontsize=16, fontproperties='SimHei')
            plt.tight_layout()
            plt.show()
        except Exception:
            pass  # 无法显示则跳过

    except Exception as e:
        print(f"❌ 词云生成失败: {e}")


# ============================================
# 按届次生成词云
# ============================================

def process_worldcup_data(worldcup_name, df_worldcup):
    """
    处理单届世界杯数据

    参数:
        worldcup_name: 届次名称
        df_worldcup: 数据DataFrame
    """
    print(f"\n{'='*50}")
    print(f"📊 处理: {worldcup_name}")
    print(f"{'='*50}")

    # 提取文本
    text = extract_text_from_df(df_worldcup)

    # 分词
    words = segment_text(text)

    # 计算词频
    freq_dict = calculate_word_frequency(words, top_n=100)

    # 保存词频
    if '2022' in worldcup_name:
        save_word_frequency(freq_dict, 'word_freq_2022.csv')
        generate_wordcloud(freq_dict, 'wordcloud_2022.png', '2022卡塔尔世界杯词云')
    else:
        save_word_frequency(freq_dict, 'word_freq_2026.csv')
        generate_wordcloud(freq_dict, 'wordcloud_2026.png', '2026美加墨世界杯词云')

    return freq_dict


def process_all_data(df):
    """
    处理全部数据生成总词云
    """
    print(f"\n{'='*50}")
    print(f"📊 处理: 全部数据")
    print(f"{'='*50}")

    # 提取文本
    text = extract_text_from_df(df)

    # 分词
    words = segment_text(text)

    # 计算词频
    freq_dict = calculate_word_frequency(words, top_n=100)

    # 保存词频
    save_word_frequency(freq_dict, 'word_freq_all.csv')

    # 生成总词云
    generate_wordcloud(freq_dict, 'wordcloud_all.png', '世界杯词云总览')

    return freq_dict


# ============================================
# 按行业生成词云（可选）
# ============================================

def process_industry_data(df):
    """
    按行业生成词云
    """
    print(f"\n{'='*50}")
    print(f"📊 按行业生成词云")
    print(f"{'='*50}")

    industries = df['industry'].unique()

    for industry in industries:
        df_industry = df[df['industry'] == industry]

        if len(df_industry) < 10:
            print(f"  ⚠️ {industry}: 数据量不足，跳过")
            continue

        print(f"\n  📈 行业: {industry}")

        # 提取文本
        text = extract_text_from_df(df_industry)

        # 分词
        words = segment_text(text)

        # 计算词频
        freq_dict = calculate_word_frequency(words, top_n=50)

        # 生成词云
        safe_name = industry.replace('/', '_')
        generate_wordcloud(freq_dict, f'wordcloud_{safe_name}.png', f'{industry}行业词云')


# ============================================
# 主函数
# ============================================

def main():
    """
    主函数 - 执行词频分析与词云生成
    """
    print("="*60)
    print("📊 词频分析与词云生成模块")
    print("="*60)

    # 加载合并数据
    print(f"\n📌 步骤1: 加载数据")
    df = load_data('merged_all.csv')

    if df is None or df.empty:
        print(f"\n⚠️ 请先运行数据清洗模块")
        return

    # 选择处理模式
    print(f"\n请选择处理模式：")
    print(f"1. 仅处理2022卡塔尔世界杯")
    print(f"2. 仅处理2026美加墨世界杯")
    print(f"3. 处理两届世界杯（分别生成词云）")
    print(f"4. 处理全部数据（生成总词云）")
    print(f"5. 完整处理（两届+总词云+行业词云）")

    choice = input(f"\n请输入选项 (1/2/3/4/5，默认5): ").strip() or '5'

    if choice == '1':
        # 仅2022
        df_2022 = df[df['worldcup'] == '2022卡塔尔']
        if not df_2022.empty:
            process_worldcup_data('2022卡塔尔世界杯', df_2022)

    elif choice == '2':
        # 仅2026
        df_2026 = df[df['worldcup'] == '2026美加墨']
        if not df_2026.empty:
            process_worldcup_data('2026美加墨世界杯', df_2026)

    elif choice == '3':
        # 两届分别处理
        df_2022 = df[df['worldcup'] == '2022卡塔尔']
        df_2026 = df[df['worldcup'] == '2026美加墨']

        if not df_2022.empty:
            process_worldcup_data('2022卡塔尔世界杯', df_2022)

        if not df_2026.empty:
            process_worldcup_data('2026美加墨世界杯', df_2026)

    elif choice == '4':
        # 总词云
        process_all_data(df)

    else:
        # 完整处理
        # 1. 两届分别处理
        df_2022 = df[df['worldcup'] == '2022卡塔尔']
        df_2026 = df[df['worldcup'] == '2026美加墨']

        if not df_2022.empty:
            process_worldcup_data('2022卡塔尔世界杯', df_2022)

        if not df_2026.empty:
            process_worldcup_data('2026美加墨世界杯', df_2026)

        # 2. 总词云
        process_all_data(df)

        # 3. 行业词云
        process_industry_data(df)

    # 完成提示
    print(f"\n{'='*60}")
    print(f"🎉 词频分析与词云生成完成！")
    print(f"{'='*60}")
    print(f"\n📁 生成的文件:")
    print(f"   数据目录 (data/):")
    print(f"   • word_freq_2022.csv - 2022词频统计")
    print(f"   • word_freq_2026.csv - 2026词频统计")
    print(f"   • word_freq_all.csv  - 总词频统计")
    print(f"\n   图片目录 (web/static/images/):")
    print(f"   • wordcloud_2022.png - 2022词云")
    print(f"   • wordcloud_2026.png - 2026词云")
    print(f"   • wordcloud_all.png  - 总词云")
    print(f"\n💡 下一步: 运行Flask Web应用")


if __name__ == '__main__':
    main()