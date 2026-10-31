# -*- coding: utf-8 -*-
"""
============================================
固定答案世界杯问答助手
============================================
功能：固定问答匹配、世界杯知识问答
============================================
"""

import requests
import json
import os
import re

# ============================================
# API配置
# 密钥通过环境变量 SILICONFLOW_API_KEY 注入，不要写进代码
# ============================================

API_KEY = os.environ.get("SILICONFLOW_API_KEY", "")
API_BASE = os.environ.get("SILICONFLOW_API_BASE", "https://api.siliconflow.cn/v1")

# ============================================
# 固定问答库（一字不差）
# ============================================

FIXED_ANSWERS = {
    "2022冠军": "2022卡塔尔世界杯冠军是阿根廷队，球队在决赛点球大战击败法国夺冠。",
    "2022卡塔尔世界杯冠军": "2022卡塔尔世界杯冠军是阿根廷队，球队在决赛点球大战击败法国夺冠。",
    "2022世界杯冠军": "2022卡塔尔世界杯冠军是阿根廷队，球队在决赛点球大战击败法国夺冠。",
    "2022冠军是谁": "2022卡塔尔世界杯冠军是阿根廷队，球队在决赛点球大战击败法国夺冠。",

    "2026举办": "2026年世界杯由美国、加拿大、墨西哥三个国家联合举办。",
    "2026世界杯举办": "2026年世界杯由美国、加拿大、墨西哥三个国家联合举办。",
    "2026在哪里举办": "2026年世界杯由美国、加拿大、墨西哥三个国家联合举办。",
    "2026世界杯在哪里举办": "2026年世界杯由美国、加拿大、墨西哥三个国家联合举办。",

    "2022举办地": "2022年世界杯举办国家为卡塔尔，多哈是核心主办城市。",
    "2022世界杯举办地": "2022年世界杯举办国家为卡塔尔，多哈是核心主办城市。",

    "梅西成就": "梅西共参加6届世界杯，累计出场28次、打入18粒进球、送出8次助攻；斩获2014、2022两届世界杯金球奖，并在2022年带领阿根廷夺得世界杯冠军。",
    "梅西世界杯成就": "梅西共参加6届世界杯，累计出场28次、打入18粒进球、送出8次助攻；斩获2014、2022两届世界杯金球奖，并在2022年带领阿根廷夺得世界杯冠军。",
    "梅西世界杯": "梅西共参加6届世界杯，累计出场28次、打入18粒进球、送出8次助攻；斩获2014、2022两届世界杯金球奖，并在2022年带领阿根廷夺得世界杯冠军。",

    "体彩舆情": "世界杯期间大众对体彩关注度大幅提升，舆论分为两类：一部分球迷关注赛事竞猜带来的观赛乐趣；另一部分舆论提醒理性购彩，警惕大额投注、非法赌球行为，相关讨论热度随比赛赛程同步起伏。",
    "世界杯体彩行业舆情分析": "世界杯期间大众对体彩关注度大幅提升，舆论分为两类：一部分球迷关注赛事竞猜带来的观赛乐趣；另一部分舆论提醒理性购彩，警惕大额投注、非法赌球行为，相关讨论热度随比赛赛程同步起伏。",
    "体彩行业": "世界杯期间大众对体彩关注度大幅提升，舆论分为两类：一部分球迷关注赛事竞猜带来的观赛乐趣；另一部分舆论提醒理性购彩，警惕大额投注、非法赌球行为，相关讨论热度随比赛赛程同步起伏。",
}

# 关键词匹配规则
KEYWORD_RULES = [
    (["2022", "冠军"], "2022卡塔尔世界杯冠军是阿根廷队，球队在决赛点球大战击败法国夺冠。"),
    (["2026", "举办"], "2026年世界杯由美国、加拿大、墨西哥三个国家联合举办。"),
    (["2026", "哪里"], "2026年世界杯由美国、加拿大、墨西哥三个国家联合举办。"),
    (["2022", "举办地"], "2022年世界杯举办国家为卡塔尔，多哈是核心主办城市。"),
    (["梅西", "成就"], "梅西共参加6届世界杯，累计出场28次、打入18粒进球、送出8次助攻；斩获2014、2022两届世界杯金球奖，并在2022年带领阿根廷夺得世界杯冠军。"),
    (["梅西", "世界杯"], "梅西共参加6届世界杯，累计出场28次、打入18粒进球、送出8次助攻；斩获2014、2022两届世界杯金球奖，并在2022年带领阿根廷夺得世界杯冠军。"),
    (["体彩", "舆情"], "世界杯期间大众对体彩关注度大幅提升，舆论分为两类：一部分球迷关注赛事竞猜带来的观赛乐趣；另一部分舆论提醒理性购彩，警惕大额投注、非法赌球行为，相关讨论热度随比赛赛程同步起伏。"),
    (["体彩", "行业"], "世界杯期间大众对体彩关注度大幅提升，舆论分为两类：一部分球迷关注赛事竞猜带来的观赛乐趣；另一部分舆论提醒理性购彩，警惕大额投注、非法赌球行为，相关讨论热度随比赛赛程同步起伏。"),
]

# 系统提示词
SYSTEM_PROMPT = """你是固定答案世界杯问答助手，禁止自由编造数字、年份、文字。

## ⚠️ 核心规则
每个提问严格输出对应固定文本，一字不差，不修改任何数字、文字。

## ⚠️ 硬性全局规则

### 规则1：不修改固定答案
- 不修改任何数字、文字
- 不许简写年份
- 不许拼接数字

### 规则2：专有名词不能写错
- 卡塔尔（不能写成卡塔托、卡搭尔等）
- 阿根廷（不能写成阿根庭等）
- 梅西（不能写成梅希、梅斯等）

### 规则3：禁止添加无关内容
- 禁止添加额外无关文字
- 禁止输出乱码
- 禁止重复语句

## 回答要求
- 严格匹配提问主题，输出对应固定答案
- 一字不差，不添加不删减
- 不确定的问题诚实告知"""


# ============================================
# 固定答案匹配函数
# ============================================

def match_fixed_answer(user_message):
    """
    匹配固定答案

    参数:
        user_message: 用户消息

    返回:
        固定答案文本，如果没有匹配则返回None
    """
    # 清理用户消息
    msg = user_message.strip().lower()
    msg_clean = re.sub(r'[？?！!。，,]', '', msg)

    # 1. 直接匹配
    for key, answer in FIXED_ANSWERS.items():
        if key in msg_clean:
            return answer

    # 2. 关键词匹配
    for keywords, answer in KEYWORD_RULES:
        if all(kw in msg_clean for kw in keywords):
            return answer

    return None


# ============================================
# 数据清洗函数
# ============================================

def clean_ai_response(text):
    """
    清洗AI回复，严格执行硬性全局规则：
    规则1：不修改固定答案里的数字、文字
    规则2：专有名词不能写错
    规则3：禁止添加无关文字、乱码、重复语句

    参数:
        text: AI原始回复

    返回:
        清洗后的文本
    """
    if not text:
        return text

    # === 规则2：专有名词纠错 ===
    name_fixes = {
        '卡塔托': '卡塔尔', '卡搭尔': '卡塔尔', '卡达尔': '卡塔尔',
        '阿根庭': '阿根廷',
        '梅希': '梅西', '梅斯': '梅西',
    }
    for wrong, correct in name_fixes.items():
        text = text.replace(wrong, correct)

    # === 规则1：年份纠错（保持完整四位）===
    year_fixes = {
        '2028': '2022', '2025': '2022',
        '2214': '2014', '2218': '2018', '2222': '2022', '2226': '2026',
    }
    for wrong, correct in year_fixes.items():
        text = re.sub(r'(?<!\d)' + wrong + r'(?!\d)', correct, text)

    # === 规则3：清理乱码、重复语句 ===
    # 清除ID编号
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'编号\d+', '', text)
    text = re.sub(r'ID[:\s]*\d+', '', text)
    text = re.sub(r'日志ID[:\s]*\w+', '', text)

    # 清除乱码
    text = re.sub(r'[^一-龥a-zA-Z0-9\s，。！？、：；""''（）【】\-]', '', text)

    # 清除多余符号
    text = re.sub(r'[。]{2,}', '。', text)
    text = re.sub(r'[！]{2,}', '！', text)
    text = re.sub(r'[？]{2,}', '？', text)
    text = re.sub(r'[，]{2,}', '，', text)
    text = re.sub(r'[\s]{2,}', ' ', text)

    # 清除重复主语
    duplicate_patterns = [
        r'阿根廷阿根廷', r'世界杯世界杯', r'冠军冠军',
        r'梅西梅西', r'卡塔尔卡塔尔'
    ]
    for pattern in duplicate_patterns:
        corrected = pattern[:len(pattern)//2]
        text = re.sub(pattern, corrected, text)

    # 清除重复句子
    sentences = re.split(r'[。！？]', text)
    seen = set()
    unique_sentences = []
    for s in sentences:
        s = s.strip()
        if s and s not in seen:
            seen.add(s)
            unique_sentences.append(s)

    text = '。'.join(unique_sentences)

    # 清除数据库碎片
    text = re.sub(r'\{[^}]+\}', '', text)
    text = re.sub(r'\'[^\']+\'', '', text)
    text = re.sub(r'"[^"]+"', '', text)

    # 清除多余空白
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()

    # 确保句子完整
    if text and not text.endswith(('。', '！', '？', '：')):
        text += '。'

    return text


# ============================================
# 核心对话函数
# ============================================

def chat_with_api(user_message, history=[]):
    """
    与AI API进行对话

    参数:
        user_message: 用户消息
        history: 历史对话记录

    返回:
        AI回复文本（已清洗）
    """
    # 1. 首先尝试匹配固定答案
    fixed_answer = match_fixed_answer(user_message)
    if fixed_answer:
        return fixed_answer

    # 2. 没有匹配到固定答案，调用API
    try:
        # 构建消息列表
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

        # 添加历史对话
        for msg in history:
            messages.append(msg)

        # 添加当前用户消息
        messages.append({"role": "user", "content": user_message})

        # 未配置密钥时直接给出明确提示，避免发出注定失败的请求
        if not API_KEY:
            return (
                "尚未配置 SiliconFlow API Key。\n\n"
                "请复制 .env.example 为 .env，填入 SILICONFLOW_API_KEY 后重启应用。\n"
                "未配置时，固定问答库中的常见问题仍可正常回答。"
            )

        # 发送请求
        response = requests.post(
            f"{API_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "Qwen/Qwen2.5-7B-Instruct",
                "messages": messages,
                "max_tokens": 512,
                "temperature": 0.3,
                "stream": False
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            ai_message = result["choices"][0]["message"]["content"]

            # 应用清洗规则
            ai_message = clean_ai_response(ai_message)

            return ai_message
        else:
            return f"抱歉，API请求失败（状态码: {response.status_code}）"

    except requests.exceptions.Timeout:
        return "抱歉，请求超时，请稍后重试。"
    except Exception as e:
        return f"抱歉，发生错误: {str(e)}"


def search_worldcup_info(query):
    """
    搜索世界杯相关信息

    参数:
        query: 搜索关键词

    返回:
        相关信息文本
    """
    # 尝试匹配固定答案
    fixed_answer = match_fixed_answer(query)
    if fixed_answer:
        return fixed_answer

    # 没有匹配，调用API
    return chat_with_api(query)


# ============================================
# 测试函数
# ============================================

def test_fixed_answers():
    """测试固定答案匹配"""
    test_questions = [
        "2022卡塔尔世界杯冠军是谁？",
        "2026世界杯在哪里举办？",
        "梅西世界杯成就",
        "2022举办地",
        "世界杯体彩行业舆情分析"
    ]

    print("=" * 50)
    print("固定答案匹配测试")
    print("=" * 50)

    for q in test_questions:
        answer = match_fixed_answer(q)
        print(f"\n问题: {q}")
        print(f"答案: {answer}")

    print("\n" + "=" * 50)


if __name__ == '__main__':
    test_fixed_answers()
