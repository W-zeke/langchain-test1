"""
工具1：情绪识别
识别用户输入中的情绪状态
"""

import json
import re


def analyze_emotion(user_text: str) -> str:
    """
    识别用户输入中的情绪状态。
    输入用户的文本内容，返回识别的情绪类型、置信度和强度。
    支持识别的情绪：开心、悲伤、愤怒、焦虑、沮丧、疲惫、困惑、恐惧、惊讶、平静、中性
    """
    text = user_text.lower()

    # 情绪关键词词典
    emotion_patterns = {
        "开心": ["开心", "高兴", "快乐", "哈哈", "太好了", "棒极了", "喜悦", "兴奋",
                 "愉快", "幸福", "满足", "欣慰", "哈哈哈", "嘻嘻", "耶", "超开心", "好开心"],
        "悲伤": ["悲伤", "难过", "伤心", "哭了", "流泪", "痛苦", "失落", "心碎",
                 "忧郁", "消沉", "苦闷", "悲哀", "哀伤", "痛心", "泣", "泪流", "悲伤欲绝"],
        "愤怒": ["愤怒", "生气", "气死了", "恼火", "可恨", "讨厌", "烦死", "暴躁",
                 "发火", "火大", "不爽", "气愤", "抓狂", "怒", "恨", "受够了"],
        "焦虑": ["焦虑", "担心", "害怕", "紧张", "不安", "恐慌", "慌乱", "着急",
                 "忐忑", "心惊", "惶恐", "坐立不安", "心神不宁"],
        "沮丧": ["沮丧", "失败", "放弃", "没意义", "无力", "绝望", "灰心", "泄气",
                 "挫败", "失望", "颓废", "完蛋", "没希望", "算了", "无所谓", "没劲"],
        "疲惫": ["累死了", "疲惫", "好困", "疲倦", "疲劳", "精疲力尽", "没精神",
                 "乏力", "虚脱", "好累", "撑不住", "太累了"],
        "困惑": ["困惑", "不懂", "不明白", "迷茫", "糊涂", "费解", "疑惑", "困扰",
                 "不解", "混乱", "纠结", "搞不清", "想不通"],
        "恐惧": ["害怕", "恐惧", "可怕", "吓人", "惊恐", "畏惧", "胆怯", "恐慌",
                 "心惊胆战", "毛骨悚然", "恐怖", "吓坏了"],
        "惊讶": ["惊讶", "吃惊", "震惊", "意外", "没想到", "竟然", "居然", "难以置信",
                 "不可思议", "惊叹", "哇塞", "天哪", "真的吗"],
        "平静": ["平静", "还好", "还行", "可以", "没事", "随意", "随便", "坦然",
                 "淡定", "平和", "平常心"],
    }

    # 计算每个情绪类别的匹配得分
    scores = {}
    for emotion, keywords in emotion_patterns.items():
        score = 0
        for kw in keywords:
            count = text.count(kw)
            if count > 0:
                score += count
        if score > 0:
            scores[emotion] = score

    # 否定检测：如"不难过""不伤心"降低对应情绪权重
    negation = re.findall(r"不(开心|高兴|快乐|难过|伤心|生气|愤怒|害怕|焦虑|紧张)", text)
    for neg_word in negation:
        for emotion in list(scores.keys()):
            if any(neg_word in kw for kw in emotion_patterns.get(emotion, [])):
                scores[emotion] = scores.get(emotion, 0) * 0.3

    # 无匹配 -> 中性
    if not scores:
        return json.dumps({
            "primary_emotion": "中性",
            "confidence": 0.5,
            "intensity": "低",
            "details": "未检测到明显情绪倾向，状态偏中性",
        }, ensure_ascii=False)

    # 按得分排序并取主要情绪
    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    primary_name, primary_score = sorted_items[0]

    # 置信度
    confidence = round(
        min(primary_score / (primary_score + (sorted_items[1][1] if len(sorted_items) > 1 else 0)) * 0.95, 0.95),
        2,
    )

    # 强度
    if primary_score >= 5:
        intensity = "高"
    elif primary_score >= 2:
        intensity = "中"
    else:
        intensity = "低"

    return json.dumps({
        "primary_emotion": primary_name,
        "confidence": confidence,
        "intensity": intensity,
    }, ensure_ascii=False)
