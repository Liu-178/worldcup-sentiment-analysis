# -*- coding: utf-8 -*-
"""
词频统计简化版（步骤4）
"""

import pandas as pd
import jieba
import os
import sys
from collections import Counter

# 设置输出编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(PROJECT_DIR, 'data')

# 停用词列表
STOPWORDS = set([
    '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这',
    '他', '她', '它', '们', '这个', '那个', '什么', '怎么', '为什么', '哪', '哪里', '哪个',
    '年', '月', '日', '时', '分', '秒', '今天', '昨天', '明天', '前天', '后天',
    '一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
    '百', '千', '万', '亿', '个', '只', '些', '每', '各',
    '据悉', '报道', '记者', '消息', '显示', '表示', '认为', '可能', '已经', '可以', '但是', '因为', '所以', '如果', '或者', '以及', '还是', '就是', '这样',
    '比赛', '进行', '将于', '本次', '本届', '上届', '下届', '首次', '再次',
    '能', '把', '被', '让', '给', '从', '向', '对', '与', '及', '等', '之', '其', '为', '以',
    '责任编辑', '编辑', '来源', '作者', '发布', '转载', '标签',
    # 新增：标点符号和无意义字符
    '...', '……', '。。', '..', '。', '，', '！', '？', '、', '：', '；',
    '"', '"', ''', ''', '（', '）', '【', '】', '《', '》',
    '前', '天', '小时', '分钟', '秒',
])


def extract_text_from_df(df):
    text_parts = []

    if 'title' in df.columns:
        titles = df['title'].dropna().tolist()
        text_parts.extend(titles)

    if 'summary' in df.columns:
        summaries = df['summary'].dropna().tolist()
        text_parts.extend(summaries)

    full_text = ' '.join(text_parts)
    print(f"提取文本: {len(full_text)} 字符")
    return full_text


def segment_text(text):
    print(f"进行分词...")

    words = jieba.lcut(text)

    filtered_words = []
    for word in words:
        word = word.strip()

        if len(word) < 2:
            continue
        if word in STOPWORDS:
            continue
        if word.isdigit():
            continue
        if all(c in '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ' for c in word):
            continue
        # 新增：过滤掉包含省略号、纯标点符号的词
        if '...' in word or '……' in word:
            continue
        if all(c in '.。,，!！?？、：:；;""''()（）【】《》' for c in word):
            continue

        filtered_words.append(word)

    print(f"分词完成: {len(filtered_words)} 个有效词")
    return filtered_words


def calculate_word_frequency(words, top_n=100):
    word_counts = Counter(words)
    top_words = word_counts.most_common(top_n)

    print(f"词频统计: 前{top_n}个高频词")
    print("-" * 40)

    for i, (word, count) in enumerate(top_words[:20], 1):
        print(f"  {i:2}. {word}: {count}")

    return top_words


def save_to_csv(word_freq, filename):
    filepath = os.path.join(DATA_DIR, filename)

    df = pd.DataFrame(word_freq, columns=['word', 'count'])
    df.to_csv(filepath, index=False, encoding='utf-8-sig')

    print(f"保存成功: {filepath}")
    return filepath


def process_dataset(df, label):
    print(f"\n处理数据集: {label}")
    print("-" * 40)

    text = extract_text_from_df(df)
    words = segment_text(text)
    word_freq = calculate_word_frequency(words, top_n=50)

    filename = f'word_freq_{label}.csv'
    save_to_csv(word_freq, filename)

    return word_freq


def main():
    print("=" * 60)
    print("词频统计分析（步骤4.4）")
    print("=" * 60)

    df = pd.read_csv(os.path.join(DATA_DIR, 'merged_all.csv'), encoding='utf-8-sig')
    print(f"加载合并数据: {len(df)} 条")

    # 1. 处理全部数据
    process_dataset(df, 'all')

    # 2. 处理2022数据
    df_2022 = df[df['worldcup'] == '2022卡塔尔']
    if len(df_2022) > 0:
        process_dataset(df_2022, '2022')

    # 3. 处理2026数据
    df_2026 = df[df['worldcup'] == '2026美加墨']
    if len(df_2026) > 0:
        process_dataset(df_2026, '2026')

    print(f"\n{'=' * 60}")
    print(f"词频统计完成！")
    print(f"{'=' * 60}")
    print(f"\n生成的文件:")
    print(f"   word_freq_all.csv  - 全部数据词频")
    print(f"   word_freq_2022.csv - 2022卡塔尔词频")
    print(f"   word_freq_2026.csv - 2026美加墨词频")


if __name__ == '__main__':
    main()