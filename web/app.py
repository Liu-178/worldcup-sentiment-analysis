# -*- coding: utf-8 -*-
"""
============================================
Flask Web应用 - 世界杯舆情分析平台
============================================
功能：
1. 提供数据接口API
2. 页面路由渲染
3. ECharts数据支持
============================================
"""

from flask import Flask, render_template, jsonify, request
import pandas as pd
import os

# ============================================
# Flask应用配置
# ============================================

app = Flask(__name__)

# 项目目录
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')


# ============================================
# 数据加载函数
# ============================================

def load_csv(filename):
    """
    加载CSV数据文件

    参数:
        filename: 文件名

    返回:
        DataFrame 或 None
    """
    filepath = os.path.join(DATA_DIR, filename)

    if not os.path.exists(filepath):
        print(f"文件不存在: {filepath}")
        return None

    try:
        df = pd.read_csv(filepath, encoding='utf-8-sig')
        return df
    except Exception as e:
        print(f"加载失败: {e}")
        return None


# ============================================
# 页面路由
# ============================================

@app.route('/')
def index():
    """
    首页 - 项目概览
    """
    return render_template('index.html')


@app.route('/compare')
def compare():
    """
    对比分析页 - 行业热度对比
    """
    return render_template('compare.html')


@app.route('/wordcloud')
def wordcloud():
    """
    词云展示页 - 高频词可视化
    """
    return render_template('wordcloud.html')


@app.route('/chat')
def chat():
    """
    AI对话页 - 智能问答助手
    """
    return render_template('chat.html')


# ============================================
# 数据接口API
# ============================================

@app.route('/api/overview')
def api_overview():
    """
    概览数据API - 首页统计卡片数据
    """
    # 加载合并数据
    df = load_csv('merged_all.csv')

    if df is None or df.empty:
        return jsonify({'error': '无数据'})

    # 统计数据
    total_count = len(df)

    # 2022数据
    df_2022 = df[df['worldcup'] == '2022卡塔尔']
    count_2022 = len(df_2022)

    # 2026数据
    df_2026 = df[df['worldcup'] == '2026美加墨']
    count_2026 = len(df_2026)

    # 行业数量
    industry_count = df['industry'].nunique()

    # 来源数量
    source_count = df['source'].nunique() if 'source' in df.columns else 0

    # 各行业数量
    industry_stats = df['industry'].value_counts().to_dict()

    # 数据时间范围
    # 2022卡塔尔世界杯：写死赛程时间
    time_range_2022 = {'start': '2022-11-20', 'end': '2022-12-18'}

    # 2026美加墨世界杯：开始时间写死，结束时间为今天
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    time_range_2026 = {'start': '2026-06-11', 'end': today}

    return jsonify({
        'total_count': total_count,
        'count_2022': count_2022,
        'count_2026': count_2026,
        'industry_count': industry_count,
        'source_count': source_count,
        'industry_stats': industry_stats,
        'time_range_2022': time_range_2022,
        'time_range_2026': time_range_2026
    })


@app.route('/api/industry_stats')
def api_industry_stats():
    """
    行业热度统计API
    """
    df = load_csv('industry_stats.csv')

    if df is None:
        return jsonify({'error': '无数据'})

    # 转换为字典列表
    data = df.to_dict('records')

    return jsonify(data)


@app.route('/api/industry_comparison')
def api_industry_comparison():
    """
    两届世界杯行业对比API
    """
    df = load_csv('industry_comparison.csv')

    if df is None:
        return jsonify({'error': '无数据'})

    data = df.to_dict('records')

    return jsonify(data)


@app.route('/api/timeline_stats')
def api_timeline_stats():
    """
    时间序列统计API
    """
    df = load_csv('timeline_stats.csv')

    if df is None:
        return jsonify({'error': '无数据'})

    data = df.to_dict('records')

    return jsonify(data)


@app.route('/api/daily_total')
def api_daily_total():
    """
    每日总热度API
    """
    df = load_csv('daily_total.csv')

    if df is None:
        return jsonify({'error': '无数据'})

    data = df.to_dict('records')

    return jsonify(data)


@app.route('/api/word_freq/<year>')
def api_word_freq(year):
    """
    词频统计API - 固定返回TOP30关键词数据，不截断

    参数:
        year: 2022 或 2026 或 all

    返回:
        前30条高频词数据（完整输出）
    """
    if year == '2022':
        filename = 'word_freq_2022.csv'
    elif year == '2026':
        filename = 'word_freq_2026.csv'
    else:
        filename = 'word_freq_all.csv'

    df = load_csv(filename)

    if df is None:
        return jsonify({'error': '无数据'})

    # ⚠️ 固定返回TOP30高频词，完整输出前30行数据，不截断
    data = df.head(30).to_dict('records')

    return jsonify(data)


# ============================================
# 数据接口API - 情感分析统计
# ============================================

@app.route('/api/sentiment_analysis')
def api_sentiment_analysis():
    """
    情感分析API - 基于新闻标题进行情感分类统计
    """
    import jieba

    df = load_csv('merged_all.csv')

    if df is None or df.empty:
        return jsonify({'error': '无数据'})

    # 正面情感关键词
    positive_words = set([
        '增长', '暴涨', '飙升', '热销', '火爆', '翻倍', '大涨', '畅销',
        '创新', '突破', '夺冠', '冠军', '胜利', '成功', '成就', '荣誉',
        '利好', '收益', '盈利', '增收', '提效', '机遇', '前景',
        '热情', '激情', '狂欢', '盛宴', '精彩', '震撼', '惊艳',
        '受欢迎', '追捧', '青睐', '认可', '赞', '好评',
        '复苏', '回暖', '反弹', '振兴', '繁荣',
        '提升', '进步', '发展', '壮大', '扩张',
        '惊喜', '意外', '超出', '突破', '新高'
    ])

    # 负面情感关键词
    negative_words = set([
        '下降', '暴跌', '亏损', '亏', '跌', '大跌',
        '争议', '质疑', '批评', '指责', '不满', '投诉', '抱怨',
        '担忧', '担心', '忧虑', '风险', '危机', '隐患', '困境',
        '失败', '失利', '出局', '淘汰', '遗憾', '错失',
        '遇冷', '冷清', '低迷', '萧条', '疲软', '萎缩',
        '断货', '缺货', '短缺', '供应不足',
        '限制', '禁止', '管制', '收紧',
        '涨价', '昂贵', '负担',
        '问题', '困难', '挑战', '压力', '冲击'
    ])

    # 停用词
    stopwords = set([
        '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这',
        '世界杯', '赛事', '比赛', '球迷', '球队', '球员', '足球', '卡塔尔', '美加墨'
    ])

    def analyze_sentiment(text):
        if not text or len(text.strip()) == 0:
            return 'neutral'

        words = jieba.lcut(text)
        filtered_words = [w.strip() for w in words if len(w.strip()) >= 2 and w.strip() not in stopwords and not w.strip().isdigit()]

        positive_count = sum(1 for w in filtered_words if w in positive_words)
        negative_count = sum(1 for w in filtered_words if w in negative_words)

        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'

    result = {
        '2022': {'positive': 0, 'neutral': 0, 'negative': 0, 'total': 0},
        '2026': {'positive': 0, 'neutral': 0, 'negative': 0, 'total': 0}
    }

    # 过滤两届世界杯的数据
    df_2022 = df[df['worldcup'] == '2022卡塔尔']
    df_2026 = df[df['worldcup'] == '2026美加墨']

    for _, row in df_2022.iterrows():
        title = row.get('title', '')
        sentiment = analyze_sentiment(str(title))
        result['2022'][sentiment] += 1
        result['2022']['total'] += 1

    for _, row in df_2026.iterrows():
        title = row.get('title', '')
        sentiment = analyze_sentiment(str(title))
        result['2026'][sentiment] += 1
        result['2026']['total'] += 1

    # 计算百分比
    for year in ['2022', '2026']:
        total = result[year]['total']
        if total > 0:
            result[year]['positive_percent'] = round(result[year]['positive'] / total * 100, 1)
            result[year]['neutral_percent'] = round(result[year]['neutral'] / total * 100, 1)
            result[year]['negative_percent'] = round(result[year]['negative'] / total * 100, 1)
        else:
            result[year]['positive_percent'] = 0
            result[year]['neutral_percent'] = 0
            result[year]['negative_percent'] = 0

    return jsonify(result)


@app.route('/api/radar_data')
def api_radar_data():
    """
    雷达图数据API - 返回五大行业综合热度对比数据
    """
    import json

    radar_file = os.path.join(DATA_DIR, 'radar_data.json')

    if not os.path.exists(radar_file):
        return jsonify({'error': '无雷达图数据'})

    try:
        with open(radar_file, 'r', encoding='utf-8') as f:
            radar_data = json.load(f)
        return jsonify(radar_data)
    except Exception as e:
        return jsonify({'error': f'读取失败: {str(e)}'})


@app.route('/api/industry_sentiment')
def api_industry_sentiment():
    """
    分行业情感分析API - 返回五大行业的正面/中性/负面情感占比
    """
    import json

    sentiment_file = os.path.join(DATA_DIR, 'industry_sentiment.json')

    if not os.path.exists(sentiment_file):
        return jsonify({'error': '无分行业情感数据'})

    try:
        with open(sentiment_file, 'r', encoding='utf-8') as f:
            sentiment_data = json.load(f)
        return jsonify(sentiment_data)
    except Exception as e:
        return jsonify({'error': f'读取失败: {str(e)}'})


@app.route('/api/news_list')
def api_news_list():
    """
    新闻列表API - 返回最新20条
    """
    df = load_csv('merged_all.csv')

    if df is None:
        return jsonify({'error': '无数据'})

    # 按标题长度排序，取前20条
    df_sample = df.head(20)

    # 选择需要的字段
    columns = ['title', 'industry', 'source', 'publish_time', 'worldcup']
    available_cols = [col for col in columns if col in df_sample.columns]

    data = df_sample[available_cols].to_dict('records')

    return jsonify(data)


@app.route('/api/industry_keywords/<industry>')
def api_industry_keywords(industry):
    """
    行业关键词统计API - 统计指定行业的新闻标题关键词词频

    参数:
        industry: 行业名称（餐饮/旅游/体彩/零售/股市）

    返回:
        关键词词频列表
    """
    import jieba
    from collections import Counter

    # 加载合并数据
    df = load_csv('merged_all.csv')

    if df is None or df.empty:
        return jsonify([])

    # 过滤指定行业的新闻
    if 'industry' not in df.columns:
        return jsonify([])

    df_industry = df[df['industry'] == industry]

    if df_industry.empty:
        return jsonify([])

    # 提取所有标题文本
    titles = df_industry['title'].dropna().tolist() if 'title' in df_industry.columns else []

    if not titles:
        return jsonify([])

    # 合并标题文本
    all_text = ' '.join(titles)

    # 使用jieba分词
    words = jieba.lcut(all_text)

    # 过滤停用词和无效词
    stopwords = set([
        '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这',
        '他', '她', '它', '们', '这个', '那个', '什么', '怎么', '为什么', '哪', '哪里', '哪个',
        '年', '月', '日', '时', '分', '秒', '今天', '昨天', '明天',
        '一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
        '能', '把', '被', '让', '给', '从', '向', '对', '与', '及', '等', '之', '其', '为', '以',
        '据悉', '报道', '记者', '消息', '显示', '表示', '认为', '可能', '已经', '可以', '但是', '因为', '所以', '如果', '或者', '以及', '还是', '就是', '这样',
    ])

    # 过滤并统计词频
    filtered_words = []
    for word in words:
        word = word.strip()
        if len(word) >= 2 and word not in stopwords and not word.isdigit():
            filtered_words.append(word)

    # 统计词频
    word_counts = Counter(filtered_words)

    # 返回前20个高频词
    top_words = word_counts.most_common(20)

    result = [{'word': word, 'count': count} for word, count in top_words]

    return jsonify(result)


# ============================================
# AI对话机器人API
# ============================================

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """
    AI对话接口 - 接收用户消息，返回AI回复
    """
    from chat_api import chat_with_api

    data = request.get_json()

    if not data or 'message' not in data:
        return jsonify({'error': '请提供消息内容'})

    user_message = data['message']
    history = data.get('history', [])

    # 获取AI回复
    ai_reply = chat_with_api(user_message, history)

    return jsonify({
        'reply': ai_reply,
        'success': True
    })


@app.route('/api/search', methods=['GET'])
def api_search():
    """
    搜索接口 - 搜索世界杯相关信息
    """
    from chat_api import search_worldcup_info

    query = request.args.get('q', '')

    if not query:
        return jsonify({'error': '请提供搜索关键词'})

    # 搜索信息
    result = search_worldcup_info(query)

    return jsonify({
        'result': result,
        'query': query,
        'success': True
    })


# ============================================
# 错误处理
# ============================================

@app.errorhandler(404)
def page_not_found(e):
    """
    404错误处理
    """
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    """
    500错误处理
    """
    return render_template('500.html'), 500


# favicon处理 - 避免500错误
@app.route('/favicon.ico')
def favicon():
    return '', 204


# ============================================
# 启动应用
# ============================================

if __name__ == '__main__':
    # 设置输出编码
    import sys
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    print("="*60)
    print("世界杯多行业舆情分析平台")
    print("="*60)
    print("\n启动信息:")
    print(f"   访问地址: http://127.0.0.1:5000")
    print(f"   数据目录: {DATA_DIR}")
    print(f"\n页面路由:")
    print(f"   /          - 首页")
    print(f"   /compare   - 行业对比分析")
    print(f"   /wordcloud - 词云展示")
    print(f"   /chat      - AI对话助手")
    print(f"\nAPI接口:")
    print(f"   /api/overview          - 概览数据")
    print(f"   /api/industry_stats    - 行业统计")
    print(f"   /api/industry_comparison - 对比数据")
    print(f"   /api/timeline_stats    - 时间序列")
    print(f"   /api/chat              - AI对话")
    print(f"   /api/search            - 智能搜索")
    print(f"   /api/word_freq/<year>  - 词频数据")
    print(f"   /api/industry_keywords/<industry> - 行业关键词")
    print("="*60)

    # 启动Flask开发服务器
    app.run(debug=True, host='127.0.0.1', port=5000)