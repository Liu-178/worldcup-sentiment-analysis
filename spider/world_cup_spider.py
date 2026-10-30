# -*- coding: utf-8 -*-
"""
============================================
世界杯五大行业舆情新闻爬虫 - 步骤3版本
============================================
核心扩展:
1. 五大行业全量覆盖（餐饮、旅游、体彩、零售、股市）
2. 年份自动识别（2022卡塔尔 / 2026美加墨）

数据源: 搜狗新闻、百度资讯、360资讯（主数据源）+ 央视网搜索（补充兜底源）
技术栈: Python + requests + BeautifulSoup
============================================

依赖安装:
pip install requests beautifulsoup4 pandas

运行方式:
python world_cup_spider.py

可配置参数（见下方配置区）:
- SEARCH_PAGES: 每个关键词搜索页数
- DELAY_RANGE: 页间延时范围（秒）
- KEYWORD_DELAY: 关键词切换延时（秒）
- INDUSTRY_DELAY: 行业切换延时（秒）
- OUTPUT_FILE: 输出文件名

注意事项:
- 关闭VPN/代理后运行
- 搜索引擎可能触发验证码，脚本会自动检测并重试
- 本脚本在本地家用网络环境下运行最佳
============================================
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os
import re
import sys
from datetime import datetime, timedelta
from urllib.parse import quote

# ============================================
# 配置区 - 所有可配置参数集中于此
# ============================================

# 五大行业关键词配置（每行业8-10组关键词，覆盖衍生场景）
INDUSTRY_KEYWORDS = {
    '餐饮': [
        '世界杯 啤酒', '世界杯 夜宵', '世界杯 餐饮',
        '世界杯 外卖', '世界杯 烧烤', '世界杯 聚餐',
        '世界杯 美食', '世界杯 餐厅', '世界杯 酒吧', '世界杯 消费'
    ],
    '旅游': [
        '世界杯 旅游', '世界杯 酒店', '世界杯 机票',
        '世界杯 签证', '世界杯 观赛', '世界杯 出境游',
        '世界杯 文旅', '世界杯 旅行', '世界杯 住宿', '世界杯 游客'
    ],
    '体彩': [
        '世界杯 体彩', '世界杯 竞彩', '世界杯 足彩',
        '世界杯 彩票', '世界杯 投注', '世界杯 竞猜',
        '世界杯 赔率', '世界杯 中奖', '世界杯 购彩', '世界杯 开奖'
    ],
    '零售': [
        '世界杯 周边', '世界杯 纪念品', '世界杯 球衣',
        '世界杯 商品', '世界杯 吉祥物', '世界杯 零售',
        '世界杯 热销', '世界杯 球迷用品', '世界杯 文创', '世界杯 销售'
    ],
    '股市': [
        '世界杯 概念股', '世界杯 股市', '世界杯 股票',
        '世界杯 A股', '世界杯 板块', '世界杯 投资',
        '世界杯 赞助商', '世界杯 资本', '世界杯 上市', '世界杯 涨幅'
    ]
}

# 行业识别词库（仅五大行业，不含体育）
INDUSTRY_WORDS = {
    '餐饮': [
        '餐饮', '啤酒', '夜宵', '烧烤', '外卖', '火锅', '餐厅', '聚餐', '美食', '早茶',
        '酒吧', '饮品', '消费', '夜市', '小吃', '美食街', '外卖平台', '订餐', '吃喝',
        '夜经济', '聚餐消费'
    ],
    '旅游': [
        '旅游', '酒店', '机票', '出境游', '观赛', '签证', '文旅', '旅行团', '球迷团',
        '住宿', '航班', '预订', '景区', '景点', '旅行社', '游学', '出行', '游客',
        '观赛团', '旅行'
    ],
    '体彩': [
        '彩票', '竞彩', '足彩', '体彩', '投注', '中奖', '博彩', '赔率', '竞猜',
        '彩票销售', '足彩销售', '体彩销售', '购彩', '彩票站', '开奖', '中奖者'
    ],
    '零售': [
        '零售', '周边', '球迷用品', '纪念品', '吉祥物', '球衣', '围巾', '商超',
        '文创', '商品', '售卖', '销售', '热销', '爆款', '旗舰店', '专卖店',
        '球迷商品', '周边产品', '纪念商品'
    ],
    '股市': [
        '股市', '概念股', 'A股', '股票', '上市', '资本', '投资', '赞助商',
        '体育板块', '股价', '证券', '涨停', '涨幅', '概念', '板块', '基金',
        '上市公司', '股市影响', '股价波动'
    ]
}

# 年份识别关键词配置
YEAR_KEYWORDS = {
    '2022': ['2022', '卡塔尔', '卡塔尔世界杯', 'Qatar', '多哈', '梅西夺冠', '阿根廷夺冠', '决赛2022', '俄罗斯2018'],
    '2026': ['2026', '美加墨', '美加墨世界杯', '北美世界杯', '美国加拿大墨西哥', '扩军', '48支', '2026年', '美加墨世界杯']
}

# 爬虫配置
SEARCH_PAGES = 3                     # 每个关键词搜索页数
DELAY_RANGE = (3, 6)                 # 页间延时范围（秒）
KEYWORD_DELAY = (5, 8)               # 关键词切换延时（秒）
INDUSTRY_DELAY = (8, 12)             # 行业切换延时（秒）
OUTPUT_FILE = 'world_cup_news.csv'   # 输出文件名

# User-Agent池（完整浏览器UA）
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36',
]

# Cookie预热池（模拟已登录状态）
COOKIE_POOL = [
    'BAIDUID=xxx; BIDUPSID=xxx;',
    'SNUID=xxx; SUID=xxx;',
    'QZ=xxx;',
]

# 数据保存目录
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')


# ============================================
# 反爬策略模块
# ============================================

def get_headers(source='sogou'):
    """
    生成完整浏览器请求头（含Cookie预热）

    参数:
        source: 数据源标识

    返回:
        完整请求头字典
    """
    base_headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'Upgrade-Insecure-Requests': '1',
    }

    # 根据数据源添加特定请求头
    if source == 'sogou':
        base_headers['Referer'] = 'https://www.sogou.com/'
        base_headers['Cookie'] = random.choice(COOKIE_POOL)
    elif source == 'baidu':
        base_headers['Referer'] = 'https://www.baidu.com/'
        base_headers['Sec-Fetch-Dest'] = 'document'
        base_headers['Sec-Fetch-Mode'] = 'navigate'
        base_headers['Sec-Fetch-Site'] = 'none'
        base_headers['Sec-Fetch-User'] = '?1'
        base_headers['Cookie'] = random.choice(COOKIE_POOL)
    elif source == '360':
        base_headers['Referer'] = 'https://www.so.com/'
        base_headers['Cookie'] = random.choice(COOKIE_POOL)
    elif source == 'cctv':
        base_headers['Referer'] = 'https://www.cctv.com/'

    return base_headers


def random_delay(delay_range=None):
    """随机延时（页间延时）"""
    if delay_range is None:
        delay_range = DELAY_RANGE
    delay = random.uniform(*delay_range)
    print(f"    ⏳ 延时 {delay:.1f} 秒...")
    time.sleep(delay)


def check_captcha(response_text, response_url):
    """
    检测验证码/反爬页面

    参数:
        response_text: 响应内容
        response_url: 最终URL

    返回:
        True表示触发了验证码，需要重试
    """
    captcha_keywords = [
        '验证码', 'captcha', 'verify', 'wappass',
        '安全验证', '请输入验证码', '人机验证',
        '频繁访问', '访问过于频繁', '暂时无法访问'
    ]

    for kw in captcha_keywords:
        if kw in response_url.lower() or kw in response_text.lower():
            return True
    return False


def make_request(url, source='sogou', max_retries=3):
    """
    发送HTTP请求（带重试机制）

    参数:
        url: 目标URL
        source: 数据源标识
        max_retries: 最大重试次数

    返回:
        Response对象或None
    """
    for attempt in range(max_retries):
        try:
            headers = get_headers(source)
            response = requests.get(
                url,
                headers=headers,
                timeout=15,
                allow_redirects=True
            )

            if response.status_code == 200:
                # 检测验证码页面
                if check_captcha(response.text, response.url):
                    print("    ⚠️ 触发验证码/反爬，等待后重试...")
                    time.sleep(random.uniform(10, 15))
                    continue
                return response
            elif response.status_code == 403:
                print("    ⚠️ 403封禁，等待后重试...")
                time.sleep(random.uniform(8, 12))
            elif response.status_code == 503:
                print("    ⚠️ 503服务不可用，等待后重试...")
                time.sleep(random.uniform(5, 10))
            elif response.status_code == 404:
                return None
            else:
                print(f"    ⚠️ HTTP状态码: {response.status_code}")

        except requests.exceptions.Timeout:
            print(f"    ⚠️ 超时，重试 {attempt+1}/{max_retries}")
        except requests.exceptions.ConnectionError:
            print(f"    ⚠️ 连接错误，重试 {attempt+1}/{max_retries}")
        except Exception as e:
            print(f"    ⚠️ 异常: {e}")

        if attempt < max_retries - 1:
            time.sleep(random.uniform(3, 5))

    return None


# ============================================
# 行业识别模块（修正：移除体育分类）
# ============================================

def identify_industries(title, summary):
    """
    识别新闻所属行业（仅五大行业）

    规则:
    1. 必须包含"世界杯"基础关键词
    2. 命中对应行业的关键词，即标记为该行业新闻
    3. 仅命中世界杯、未命中任何行业关键词的，判定为无效新闻，不入库

    参数:
        title: 新闻标题
        summary: 正文摘要

    返回:
        行业列表（如 ['餐饮', '旅游']）或 ['无效']（不入库）
    """
    matched_industries = []
    combined_text = (title + ' ' + summary).lower()

    # 必须包含世界杯基础关键词
    if '世界杯' not in combined_text:
        return ['无效']

    # 检查各行业词（仅五大行业）
    for industry, words in INDUSTRY_WORDS.items():
        for word in words:
            if word in combined_text:
                matched_industries.append(industry)
                break

    # 未命中任何行业关键词，判定为无效（纯赛事新闻不入库）
    if not matched_industries:
        return ['无效']

    return matched_industries


# ============================================
# 年份识别模块（优化：新增相对时间换算）
# ============================================

def parse_relative_time(time_str):
    """
    解析相对时间并换算为具体日期

    参数:
        time_str: 相对时间字符串（如"3天前"、"2小时前"）

    返回:
        具体日期字符串（YYYY-MM-DD）或原时间字符串
    """
    if not time_str:
        return '未知时间'

    time_str = time_str.strip()
    now = datetime.now()

    # 匹配相对时间模式
    patterns = [
        (r'(\d+)\s*分钟前', 'minutes'),
        (r'(\d+)\s*小时前', 'hours'),
        (r'(\d+)\s*天前', 'days'),
        (r'(\d+)\s*周前', 'weeks'),
        (r'(\d+)\s*个月前', 'months'),
        (r'刚刚', 'just'),
        (r'昨天', 'yesterday'),
        (r'前天', 'two_days'),
    ]

    for pattern, unit in patterns:
        match = re.search(pattern, time_str)
        if match:
            if unit == 'just':
                return now.strftime('%Y-%m-%d')
            elif unit == 'yesterday':
                return (now - timedelta(days=1)).strftime('%Y-%m-%d')
            elif unit == 'two_days':
                return (now - timedelta(days=2)).strftime('%Y-%m-%d')
            else:
                value = int(match.group(1))
                if unit == 'minutes':
                    date = now - timedelta(minutes=value)
                elif unit == 'hours':
                    date = now - timedelta(hours=value)
                elif unit == 'days':
                    date = now - timedelta(days=value)
                elif unit == 'weeks':
                    date = now - timedelta(weeks=value)
                elif unit == 'months':
                    date = now - timedelta(days=value*30)  # 简化处理
                return date.strftime('%Y-%m-%d')

    # 如果是标准日期格式，直接返回
    if re.search(r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}', time_str):
        # 提取年份
        year_match = re.search(r'(\d{4})', time_str)
        if year_match:
            return time_str

    return '未知时间'


def identify_year(title, summary, publish_time, url=''):
    """
    识别新闻所属年份（2022 / 2026 / 未知）

    综合四个维度判定（优先级递减）:
    1. 明确年份关键词（标题/摘要）
    2. 换算后的发布日期
    3. URL链接中的年份
    4. 标记为未知

    参数:
        title: 新闻标题
        summary: 正文摘要
        publish_time: 发布时间（可能为相对时间）
        url: 原文链接（可选）

    返回:
        '2022' 或 '2026' 或 '未知'
    """
    combined_text = title + ' ' + summary

    # 优先级1：检查明确年份关键词
    score_2022 = 0
    score_2026 = 0

    for kw in YEAR_KEYWORDS['2022']:
        if kw in combined_text:
            score_2022 += 1

    for kw in YEAR_KEYWORDS['2026']:
        if kw in combined_text:
            score_2026 += 1

    # 关键词匹配优先级最高
    if score_2026 > score_2022:
        return '2026'
    elif score_2022 > score_2026:
        return '2022'

    # 优先级2：换算后的发布日期
    parsed_time = parse_relative_time(publish_time)
    if parsed_time != '未知时间':
        year_match = re.search(r'(\d{4})', parsed_time)
        if year_match:
            year = year_match.group(1)
            if year == '2022':
                return '2022'
            elif year in ['2025', '2026']:
                return '2026'
            elif year == '2018':
                return '2022'  # 2018俄罗斯世界杯归为2022届次对比
            elif year in ['2014', '2010']:
                return '2022'  # 历史世界杯归为2022届次对比

    # 优先级3：URL链接中的年份
    if url:
        url_year_match = re.search(r'/(\d{4})/', url)
        if url_year_match:
            url_year = url_year_match.group(1)
            if url_year == '2022':
                return '2022'
            elif url_year in ['2025', '2026']:
                return '2026'

    # 优先级4：无法判定，标记为未知
    return '未知'


# ============================================
# 新闻解析模块（多选择器降级容错）
# ============================================

def parse_sogou_news(html):
    """
    解析搜狗新闻搜索结果

    多选择器降级容错机制
    """
    news_list = []

    try:
        soup = BeautifulSoup(html, 'html.parser')

        # 尝试多种选择器（降级容错）
        selectors = [
            # 选择器1：搜狗新版结构（2025+）
            {'container': 'div.vrwrap', 'title': 'h3.vr-title a', 'link': 'h3.vr-title a', 'time': 'span.s2', 'source': 'span.s1', 'summary': 'p.star-wiki'},
            # 选择器2：搜狗经典结构
            {'container': 'div.result', 'title': 'h3 a', 'link': 'h3 a', 'time': 'cite', 'source': 'cite', 'summary': 'p'},
            # 选择器3：新闻列表结构
            {'container': 'div.news-list li', 'title': 'a', 'link': 'a', 'time': 'span.time', 'source': 'span.source', 'summary': 'p'},
            # 选择器4：通用结构
            {'container': 'li[class*="result"]', 'title': 'a[href]', 'link': 'a[href]', 'time': 'span', 'source': 'span', 'summary': 'p'},
        ]

        for selector in selectors:
            containers = soup.select(selector['container'])
            if containers:
                for container in containers:
                    try:
                        # 提取标题
                        title_elem = container.select_one(selector['title'])
                        if not title_elem:
                            continue
                        title = title_elem.get_text(strip=True)

                        # 提取链接
                        link_elem = container.select_one(selector['link'])
                        href = link_elem.get('href', '') if link_elem else ''

                        # 提取时间和来源
                        time_elem = container.select_one(selector.get('time', ''))
                        source_elem = container.select_one(selector.get('source', ''))

                        time_text = time_elem.get_text(strip=True) if time_elem else ''
                        source_text = source_elem.get_text(strip=True) if source_elem else ''

                        # 提取摘要
                        summary_elem = container.select_one(selector.get('summary', '')) if 'summary' in selector else None
                        summary_text = ''
                        if summary_elem:
                            summary_text = summary_elem.get_text(strip=True)[:200]  # 限制长度

                        # 如果来源字段包含时间格式，则从URL提取来源
                        if source_text and re.search(r'\d+天前|\d+小时前|\d+分钟前|刚刚|昨天|\d{4}年\d{1,2}月\d{1,2}日', source_text):
                            time_text = source_text
                            source_text = ''

                        # 从URL提取来源
                        if not source_text or source_text == time_text:
                            if 'baijiahao.baidu.com' in href or 'baidu.com' in href:
                                source_text = '百度资讯'
                            elif 'people.com.cn' in href:
                                source_text = '人民网'
                            elif 'xinhuanet.com' in href:
                                source_text = '新华网'
                            elif 'cctv.com' in href:
                                source_text = '央视网'
                            elif 'sohu.com' in href:
                                source_text = '搜狐网'
                            elif 'sina.com.cn' in href:
                                source_text = '新浪网'
                            elif 'qq.com' in href:
                                source_text = '腾讯网'
                            elif '163.com' in href:
                                source_text = '网易'
                            elif 'ifeng.com' in href:
                                source_text = '凤凰网'
                            elif 'huanqiu.com' in href:
                                source_text = '环球网'
                            elif 'chinanews.com' in href:
                                source_text = '中国新闻网'
                            elif 'zgswcn.com' in href:
                                source_text = '中国商报'
                            elif 'eastmoney.com' in href:
                                source_text = '东方财富'
                            else:
                                source_text = '搜狗新闻'

                        # 解析发布时间（含相对时间换算）
                        publish_time = parse_relative_time(time_text)

                        # 过滤无效标题
                        if len(title) < 10:
                            continue

                        # 过滤导航/广告链接
                        skip_keywords = ['登录', '注册', '更多', '返回', '首页', '下载', '搜索', '广告']
                        if any(kw in title for kw in skip_keywords):
                            continue

                        news_list.append({
                            '标题': title,
                            '原文链接': href,
                            '媒体来源': source_text if source_text else '搜狗新闻',
                            '发布时间': publish_time,
                            '正文摘要': summary_text
                        })

                    except Exception:
                        continue

                if news_list:
                    break  # 已成功提取，退出选择器循环

    except Exception as e:
        print(f"    ❌ 解析错误: {e}")

    return news_list


def parse_baidu_news(html):
    """
    解析百度资讯搜索结果

    多选择器降级容错机制
    """
    news_list = []

    try:
        soup = BeautifulSoup(html, 'html.parser')

        # 尝试多种选择器（降级容错）
        selectors = [
            # 选择器1：百度资讯经典结构
            {'container': 'div.result', 'title': 'h3 a', 'link': 'h3 a', 'time': 'p.g', 'source': 'p.g'},
            # 选择器2：百度新闻列表
            {'container': 'div.news-list div.result', 'title': 'a[href]', 'link': 'a[href]', 'time': 'span.time', 'source': 'span.source'},
            # 选择器3：通用结构
            {'container': 'div[class*="result"]', 'title': 'a[href]', 'link': 'a[href]', 'time': 'span', 'source': 'span'},
        ]

        for selector in selectors:
            containers = soup.select(selector['container'])
            if containers:
                for container in containers:
                    try:
                        # 提取标题
                        title_elem = container.select_one(selector['title'])
                        if not title_elem:
                            continue
                        title = title_elem.get_text(strip=True)

                        # 提取链接
                        link_elem = container.select_one(selector['link'])
                        href = link_elem.get('href', '') if link_elem else ''

                        # 提取时间和来源
                        info_elem = container.select_one(selector['time'])
                        info_text = info_elem.get_text(strip=True) if info_elem else ''

                        # 解析来源和时间（格式: "来源 · 时间" 或 "来源时间"）
                        source_text = ''
                        time_text = ''

                        if '·' in info_text:
                            parts = info_text.split('·')
                            source_text = parts[0].strip()
                            time_text = parts[1].strip() if len(parts) > 1 else ''
                        else:
                            # 尝试从URL提取来源
                            if 'baijiahao.baidu.com' in href:
                                source_text = '百家号'
                            elif 'people.com.cn' in href:
                                source_text = '人民网'
                            elif 'eastmoney.com' in href:
                                source_text = '东方财富'
                            elif 'yicai.com' in href:
                                source_text = '第一财经'
                            elif 'tmtpost.com' in href:
                                source_text = '钛媒体'
                            elif 'cyzone.cn' in href:
                                source_text = '创业邦'
                            elif 'jiemian.com' in href:
                                source_text = '界面新闻'
                            elif 'foodmate.net' in href:
                                source_text = '食品伙伴网'
                            elif 'hunantoday.cn' in href:
                                source_text = '新湖南'
                            elif 'sfccn.com' in href:
                                source_text = '消费财经'
                            else:
                                # 尝试从info_text提取：如果看起来像时间，则来源默认为百度资讯
                                if re.search(r'\d+天前|\d+小时前|\d+分钟前|刚刚|昨天|\d{4}年\d{1,2}月\d{1,2}日|\d{1,2}月\d{1,2}日', info_text):
                                    time_text = info_text
                                    source_text = '百度资讯'
                                else:
                                    # info_text可能是来源
                                    source_text = info_text if info_text else '百度资讯'

                        # 解析发布时间（含相对时间换算）
                        publish_time = parse_relative_time(time_text)

                        # 过滤无效标题
                        if len(title) < 10:
                            continue

                        # 过滤导航/广告链接
                        skip_keywords = ['登录', '注册', '更多', '返回', '首页', '下载', '搜索', '广告']
                        if any(kw in title for kw in skip_keywords):
                            continue

                        news_list.append({
                            '标题': title,
                            '原文链接': href,
                            '媒体来源': source_text if source_text else '百度资讯',
                            '发布时间': publish_time,
                            '正文摘要': ''
                        })

                    except Exception:
                        continue

                if news_list:
                    break

    except Exception as e:
        print(f"    ❌ 解析错误: {e}")

    return news_list


def parse_360_news(html):
    """
    解析360资讯搜索结果

    多选择器降级容错机制
    """
    news_list = []

    try:
        soup = BeautifulSoup(html, 'html.parser')

        # 尝试多种选择器（降级容错）
        selectors = [
            # 选择器1：360资讯经典结构
            {'container': 'li.res-list', 'title': 'h3 a', 'link': 'h3 a', 'time': 'span.time', 'source': 'span.source'},
            # 选择器2：360新闻列表
            {'container': 'div.news-item', 'title': 'a[href]', 'link': 'a[href]', 'time': 'span', 'source': 'span'},
            # 选择器3：通用结构
            {'container': 'li[class*="res"]', 'title': 'a[href]', 'link': 'a[href]', 'time': 'span', 'source': 'span'},
        ]

        for selector in selectors:
            containers = soup.select(selector['container'])
            if containers:
                for container in containers:
                    try:
                        # 提取标题
                        title_elem = container.select_one(selector['title'])
                        if not title_elem:
                            continue
                        title = title_elem.get_text(strip=True)

                        # 提取链接
                        link_elem = container.select_one(selector['link'])
                        href = link_elem.get('href', '') if link_elem else ''

                        # 提取时间和来源
                        time_elem = container.select_one(selector['time'])
                        source_elem = container.select_one(selector['source'])

                        time_text = time_elem.get_text(strip=True) if time_elem else ''
                        source_text = source_elem.get_text(strip=True) if source_elem else ''

                        # 如果来源字段包含时间格式，则从URL提取来源
                        if source_text and re.search(r'\d+天前|\d+小时前|\d+分钟前|刚刚|昨天|\d{4}年\d{1,2}月\d{1,2}日', source_text):
                            time_text = source_text
                            source_text = ''

                        # 从URL提取来源
                        if not source_text or source_text == time_text:
                            if 'baijiahao.baidu.com' in href or 'baidu.com' in href:
                                source_text = '百度资讯'
                            elif 'people.com.cn' in href:
                                source_text = '人民网'
                            elif 'xinhuanet.com' in href:
                                source_text = '新华网'
                            elif 'cctv.com' in href:
                                source_text = '央视网'
                            elif 'sohu.com' in href:
                                source_text = '搜狐网'
                            elif 'sina.com.cn' in href:
                                source_text = '新浪网'
                            elif 'qq.com' in href:
                                source_text = '腾讯网'
                            elif '163.com' in href:
                                source_text = '网易'
                            elif 'ifeng.com' in href:
                                source_text = '凤凰网'
                            elif 'huanqiu.com' in href:
                                source_text = '环球网'
                            elif 'chinanews.com' in href:
                                source_text = '中国新闻网'
                            elif 'eastmoney.com' in href:
                                source_text = '东方财富'
                            elif 'yicai.com' in href:
                                source_text = '第一财经'
                            else:
                                source_text = '360资讯'

                        # 解析发布时间（含相对时间换算）
                        publish_time = parse_relative_time(time_text)

                        # 过滤无效标题
                        if len(title) < 10:
                            continue

                        # 过滤导航/广告链接
                        skip_keywords = ['登录', '注册', '更多', '返回', '首页', '下载', '搜索', '广告']
                        if any(kw in title for kw in skip_keywords):
                            continue

                        news_list.append({
                            '标题': title,
                            '原文链接': href,
                            '媒体来源': source_text if source_text else '360资讯',
                            '发布时间': publish_time,
                            '正文摘要': ''
                        })

                    except Exception:
                        continue

                if news_list:
                    break

    except Exception as e:
        print(f"    ❌ 解析错误: {e}")

    return news_list


def parse_cctv_news(html):
    """
    解析央视网搜索结果（补充兜底源）

    多选择器降级容错机制
    """
    news_list = []

    try:
        soup = BeautifulSoup(html, 'html.parser')

        # 央视网搜索结果是通过link_p.php跳转的链接
        links = soup.find_all('a', href=True)

        for link in links:
            try:
                href = link.get('href', '')
                title = link.get_text(strip=True)

                # 过滤：只保留包含cctv的搜索结果链接
                if 'link_p.php' not in href and 'cctv.com' not in href:
                    continue

                # 过滤无效标题
                if len(title) < 10:
                    continue

                # 过滤导航链接
                skip_keywords = ['登录', '注册', '更多', '返回', '首页', '下载', '搜索']
                if any(kw in title for kw in skip_keywords):
                    continue

                # 解析真实链接（如果是跳转链接）
                if 'link_p.php' in href:
                    import urllib.parse
                    parsed = urllib.parse.urlparse(href)
                    params = urllib.parse.parse_qs(parsed.query)
                    if 'targetpage' in params:
                        href = params['targetpage'][0]

                news_list.append({
                    '标题': title,
                    '原文链接': href,
                    '媒体来源': '央视网',
                    '发布时间': '未知时间',
                    '正文摘要': ''
                })

            except Exception:
                continue

    except Exception as e:
        print(f"    ❌ 解析错误: {e}")

    return news_list


# ============================================
# 数据源爬虫模块
# ============================================

def crawl_sogou_news(keyword, page=0):
    """
    爬取搜狗新闻搜索

    参数:
        keyword: 搜索关键词
        page: 页码（从0开始）

    返回: 新闻列表
    """
    news_list = []

    # 搜狗新闻搜索URL
    encoded_keyword = quote(keyword)
    url = f'https://news.sogou.com/news?query={encoded_keyword}&page={page + 1}'

    print(f"    📄 第 {page+1} 页: {url}")

    response = make_request(url, 'sogou')
    if not response:
        return news_list

    try:
        response.encoding = 'utf-8'
        news_list = parse_sogou_news(response.text)
    except Exception as e:
        print(f"    ❌ 错误: {e}")

    return news_list


def crawl_baidu_news(keyword, page=0):
    """
    爬取百度资讯搜索

    参数:
        keyword: 搜索关键词
        page: 页码（从0开始）

    返回: 新闻列表
    """
    news_list = []

    # 百度资讯搜索URL
    encoded_keyword = quote(keyword)
    url = f'https://www.baidu.com/s?wd={encoded_keyword}&tn=news&rtt=1&bsst=1&cl=2&pn={page * 10}'

    print(f"    📄 第 {page+1} 页: {url}")

    response = make_request(url, 'baidu')
    if not response:
        return news_list

    try:
        response.encoding = 'utf-8'
        news_list = parse_baidu_news(response.text)
    except Exception as e:
        print(f"    ❌ 错误: {e}")

    return news_list


def crawl_360_news(keyword, page=0):
    """
    爬取360资讯搜索

    参数:
        keyword: 搜索关键词
        page: 页码（从0开始）

    返回: 新闻列表
    """
    news_list = []

    # 360资讯搜索URL
    encoded_keyword = quote(keyword)
    url = f'https://news.so.com/ns?q={encoded_keyword}&pn={page + 1}'

    print(f"    📄 第 {page+1} 页: {url}")

    response = make_request(url, '360')
    if not response:
        return news_list

    try:
        response.encoding = 'utf-8'
        news_list = parse_360_news(response.text)
    except Exception as e:
        print(f"    ❌ 错误: {e}")

    return news_list


def crawl_cctv_news(keyword, page=0):
    """
    爬取央视网搜索（补充兜底源）

    参数:
        keyword: 搜索关键词
        page: 页码（从0开始）

    返回: 新闻列表
    """
    news_list = []

    # 央视网搜索URL
    encoded_keyword = quote(keyword)
    url = f'https://search.cctv.com/search.php?qtext={encoded_keyword}&type=web&page={page + 1}'

    print(f"    📄 第 {page+1} 页: {url}")

    response = make_request(url, 'cctv')
    if not response:
        return news_list

    try:
        response.encoding = 'utf-8'
        news_list = parse_cctv_news(response.text)
    except Exception as e:
        print(f"    ❌ 错误: {e}")

    return news_list


def crawl_by_keyword(keyword):
    """
    按关键词爬取所有数据源

    参数:
        keyword: 搜索关键词

    返回: 新闻列表
    """
    all_news = []

    # 主数据源：搜狗新闻
    print(f"\n    📰 搜狗新闻")
    for page in range(SEARCH_PAGES):
        news = crawl_sogou_news(keyword, page)
        if not news:
            print(f"        无结果，停止翻页")
            break
        all_news.extend(news)
        print(f"        ✅ 本页获取 {len(news)} 条")
        if page < SEARCH_PAGES - 1:
            random_delay()

    # 主数据源：百度资讯
    print(f"\n    📰 百度资讯")
    for page in range(SEARCH_PAGES):
        news = crawl_baidu_news(keyword, page)
        if not news:
            print(f"        无结果，停止翻页")
            break
        all_news.extend(news)
        print(f"        ✅ 本页获取 {len(news)} 条")
        if page < SEARCH_PAGES - 1:
            random_delay()

    # 主数据源：360资讯（最稳定，反爬宽松）
    print(f"\n    📰 360资讯")
    for page in range(SEARCH_PAGES):
        news = crawl_360_news(keyword, page)
        if not news:
            print(f"        无结果，停止翻页")
            break
        all_news.extend(news)
        print(f"        ✅ 本页获取 {len(news)} 条")
        if page < SEARCH_PAGES - 1:
            random_delay()

    # 补充兜底源：央视网搜索
    print(f"\n    📰 央视网（补充兜底）")
    for page in range(SEARCH_PAGES):
        news = crawl_cctv_news(keyword, page)
        if not news:
            print(f"        无结果，停止翻页")
            break
        all_news.extend(news)
        print(f"        ✅ 本页获取 {len(news)} 条")
        if page < SEARCH_PAGES - 1:
            random_delay()

    return all_news


def crawl_industry(industry, keywords):
    """
    爬取单个行业的所有新闻

    参数:
        industry: 行业名称
        keywords: 关键词列表

    返回: 新闻列表
    """
    all_news = []

    print(f"\n{'─'*50}")
    print(f"📊 行业: {industry}")
    print(f"🔑 关键词数: {len(keywords)}")
    print(f"{'─'*50}")

    for idx, keyword in enumerate(keywords):
        print(f"\n  🔍 关键词 [{idx+1}/{len(keywords)}]: {keyword}")

        news = crawl_by_keyword(keyword)
        all_news.extend(news)

        # 关键词切换延时
        if idx < len(keywords) - 1:
            random_delay(KEYWORD_DELAY)

    return all_news


# ============================================
# 数据处理模块
# ============================================

def deduplicate_news(news_list):
    """
    按URL去重（所有数据源合并去重）

    参数:
        news_list: 新闻列表

    返回: 去重后的新闻列表
    """
    if not news_list:
        return []

    seen_urls = set()
    unique_news = []

    for news in news_list:
        url = news.get('原文链接', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_news.append(news)

    return unique_news


def filter_valid_news(news_list):
    """
    过滤有效新闻（仅五大行业，不含体育）

    规则:
    1. 不包含"世界杯"的，不入库
    2. 仅命中世界杯、未命中任何行业关键词的，不入库
    3. 命中五大行业关键词的，保留并标记所属行业

    参数:
        news_list: 新闻列表

    返回: 有效新闻列表
    """
    valid_news = []

    for news in news_list:
        title = news.get('标题', '')
        summary = news.get('正文摘要', '')
        publish_time = news.get('发布时间', '')
        url = news.get('原文链接', '')

        # 识别行业（仅五大行业）
        industries = identify_industries(title, summary)

        # 过滤无效新闻（不命中行业关键词）
        if industries == ['无效']:
            continue

        # 识别年份
        year = identify_year(title, summary, publish_time, url)

        # 添加识别结果
        news['所属行业'] = ','.join(industries)
        news['所属年份'] = year

        valid_news.append(news)

    return valid_news


def save_to_csv(news_list, filename):
    """
    导出CSV（累积模式：读取旧数据 + 合并新数据 + 去重）

    参数:
        news_list: 新闻列表
        filename: 文件名
    """
    if not news_list:
        print("\n⚠️ 无有效新闻可导出")
        return False

    # 确保目录存在
    os.makedirs(DATA_DIR, exist_ok=True)

    # 转换为DataFrame
    df_new = pd.DataFrame(news_list)

    # 按指定字段顺序导出
    columns = ['标题', '原文链接', '媒体来源', '发布时间', '正文摘要', '所属行业', '所属年份']
    df_new = df_new[[col for col in columns if col in df_new.columns]]

    # 读取旧数据（如果存在）
    filepath = os.path.join(DATA_DIR, filename)
    old_count = 0
    new_count = len(df_new)

    if os.path.exists(filepath):
        try:
            df_old = pd.read_csv(filepath, encoding='utf-8-sig')
            old_count = len(df_old)
            print(f"\n📂 读取旧数据: {old_count} 条")

            # 合新旧数据
            df_combined = pd.concat([df_old, df_new], ignore_index=True)

            # 按标题去重（保留最新的）
            df_combined = df_combined.drop_duplicates(subset=['标题'], keep='last')

            combined_count = len(df_combined)
            added_count = combined_count - old_count
            duplicate_count = new_count - added_count

            print(f"📥 本次爬取: {new_count} 条")
            print(f"🔄 重复跳过: {duplicate_count} 条")
            print(f"✨ 新增入库: {added_count} 条")
            print(f"📊 累积总数: {combined_count} 条")

            df_new = df_combined
        except Exception as e:
            print(f"\n⚠️ 读取旧数据失败: {e}")
            print(f"📥 本次爬取: {new_count} 条（直接保存）")

    # 保存文件
    df_new.to_csv(filepath, index=False, encoding='utf-8-sig')

    print(f"\n✅ 数据已保存: {filepath}")
    return True


def print_statistics(news_list):
    """
    打印统计信息（仅五大行业）
    """
    if not news_list:
        print("\n📊 无有效新闻")
        return

    df = pd.DataFrame(news_list)

    print(f"\n{'='*60}")
    print("📊 爬取统计")
    print(f"{'='*60}")

    # 总数统计
    print(f"\n📈 总体统计:")
    print(f"   去重后总数: {len(df)} 条")

    # 行业分布（仅五大行业）
    print(f"\n📈 行业分布:")
    industry_counts = {}
    for industries in df['所属行业']:
        for ind in industries.split(','):
            industry_counts[ind] = industry_counts.get(ind, 0) + 1

    total = len(df)
    for industry, count in sorted(industry_counts.items(), key=lambda x: -x[1]):
        pct = count / total * 100
        print(f"   {industry}: {count} 条 ({pct:.1f}%)")

    # 年份分布
    print(f"\n📈 年份分布:")
    for year, count in df['所属年份'].value_counts().items():
        pct = count / total * 100
        print(f"   {year}年: {count} 条 ({pct:.1f}%)")

    # 来源分布
    print(f"\n📈 来源分布:")
    for source, count in df['媒体来源'].value_counts().head(10).items():
        print(f"   {source}: {count} 条")

    print(f"\n{'='*60}")


# ============================================
# 主程序
# ============================================

def main():
    """主函数"""
    # 修复Windows控制台中文乱码
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    print("="*60)
    print("🏆 世界杯五大行业舆情新闻爬虫 - 步骤3版本")
    print("="*60)
    print(f"📋 行业范围: {', '.join(INDUSTRY_KEYWORDS.keys())}（五大行业，不含体育）")
    print(f"📋 数据源: 搜狗新闻 + 百度资讯 + 360资讯（主）+ 央视网（补充）")
    print(f"📋 每关键词页数: {SEARCH_PAGES}")
    print(f"📋 输出文件: {OUTPUT_FILE}")
    print("="*60)
    print("\n⚠️ 注意事项:")
    print("  - 请在本地家用网络环境下运行")
    print("  - 关闭VPN/代理后运行")
    print("  - 纯赛事新闻不入库（仅保留五大行业舆情新闻）")
    print("="*60)

    # 开始爬取
    print("\n🚀 开始爬取...")
    all_news = []

    for industry, keywords in INDUSTRY_KEYWORDS.items():
        news = crawl_industry(industry, keywords)
        all_news.extend(news)

        # 行业间休眠
        if industry != list(INDUSTRY_KEYWORDS.keys())[-1]:
            delay = random.uniform(INDUSTRY_DELAY[0], INDUSTRY_DELAY[1])
            print(f"\n😴 行业间休眠 {delay:.1f} 秒...")
            time.sleep(delay)

    # 去重（所有数据源合并去重）
    print(f"\n{'='*60}")
    print("📋 数据处理")
    print(f"{'='*60}")
    print(f"\n原始爬取: {len(all_news)} 条")
    all_news = deduplicate_news(all_news)
    print(f"URL去重后: {len(all_news)} 条")

    # 过滤有效新闻（仅五大行业）
    print("\n🔍 识别行业与年份...")
    valid_news = filter_valid_news(all_news)
    print(f"有效行业新闻: {len(valid_news)} 条")
    print(f"无效新闻（不入库）: {len(all_news) - len(valid_news)} 条")

    # 打印统计
    print_statistics(valid_news)

    # 导出CSV
    save_to_csv(valid_news, OUTPUT_FILE)

    print("\n🎉 爬取任务完成！")


if __name__ == '__main__':
    main()