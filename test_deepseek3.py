"""
基于 LangChain 的情绪识别与安慰智能体
功能：识别用户情绪 -> 针对性安慰 -> 引导情绪转向正向
模型：DeepSeek (via langchain_deepseek)
"""

import json
import re
import sys

# ============================================================
# 跨平台输入支持：终端无交互时 fallback 到 GUI 弹窗
# ============================================================
_TK_ROOT = None


def _get_tk_root():
    """惰性获取 tkinter 根窗口（避免重复创建）"""
    global _TK_ROOT
    if _TK_ROOT is None:
        import tkinter as tk
        _TK_ROOT = tk.Tk()
        _TK_ROOT.withdraw()
    return _TK_ROOT


def get_user_input(prompt: str) -> str:
    """
    安全获取用户输入：
    - 终端交互可用 → 标准 input()
    - 否则（如 Code Runner 只读面板）→ tkinter 弹窗
    """
    if sys.stdin.isatty():
        return input(prompt).strip()

    # 非 TTY 环境 → GUI 弹窗
    retries = 0
    while retries < 3:
        try:
            from tkinter import simpledialog
            root = _get_tk_root()
            root.lift()
            root.attributes("-topmost", True)
            result = simpledialog.askstring(
                "暖暖 - 情绪支持助手",
                f"{prompt}\n(输入 quit 或 退出 结束对话)",
                parent=root,
            )
            root.attributes("-topmost", False)
            # 用户取消 / 关闭窗口 → None；提交空字符串 → ""
            if result is None:
                # 取消 → 询问是否退出
                from tkinter import messagebox
                quit_ask = messagebox.askyesno(
                    "暖暖", "要退出暖暖情绪助手吗？", parent=root
                )
                if quit_ask:
                    return "quit"
                retries += 1
                continue  # 重新弹窗
            return result.strip()
        except Exception:
            # 连 GUI 也不行 → 提示用户改用终端运行
            print()
            print("=" * 60)
            print("  检测到当前环境不支持交互输入。")
            print("  请在终端中用以下命令运行：")
            print()
            print("    python test_deepseek3.py")
            print()
            print("  或在 VSCode 设置中开启：")
            print('    "code-runner.runInTerminal": true')
            print("=" * 60)
            print()
            sys.exit(1)
    # 超过重试次数，自动退出
    return "quit"

# ============================================================
# 【Windows 编码兼容】
# 打补丁：OpenAI 客户端在序列化请求时会因孤立代理项（lone
# surrogate）失败，在此提前清洗所有消息文本。
# ============================================================
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import langchain_core.messages as _lcm
_orig_msg_init = _lcm.BaseMessage.__init__


def _patched_msg_init(self, content, **kwargs):
    if isinstance(content, str):
        content = content.encode("utf-8", errors="replace").decode("utf-8")
    _orig_msg_init(self, content, **kwargs)


_lcm.BaseMessage.__init__ = _patched_msg_init

from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain.agents import create_agent
from langchain_core.tools import tool

load_dotenv()

# ============================================================
# Skill 1: 情绪识别工具
# ============================================================
@tool
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


# ============================================================
# Skill 2: 安慰策略工具
# ============================================================
@tool
def comfort_strategy(emotion_type: str) -> str:
    """
    根据情绪类型返回对应的安慰策略和话术方向。
    输入情绪类型（开心/悲伤/愤怒/焦虑/沮丧/疲惫/困惑/恐惧/惊讶/平静/中性），
    返回该情绪对应的安慰策略、语气和关键话术。
    """
    strategies = {
        "悲伤": {
            "approach": "共情陪伴型",
            "tone": "温柔、耐心、包容",
            "key_points": [
                "表达理解「我理解你的感受，我在这里陪你」",
                "肯定情绪的合理性「感到悲伤是很正常的」",
                "传递希望「悲伤是暂时的，一切都会好起来」",
                "引导回忆美好的事物",
            ],
            "avoid": "不要说「别哭了」「不要难过」等否定情绪的话",
        },
        "愤怒": {
            "approach": "情绪疏导型",
            "tone": "平和、理性、包容",
            "key_points": [
                "表达理解「发生这种事确实让人生气」",
                "帮助情绪降温「我们先深呼吸一下」",
                "引导换个角度看问题",
                "提供解决问题的思路",
            ],
            "avoid": "不要直接反驳或否定愤怒，避免说「这有什么好生气的」",
        },
        "焦虑": {
            "approach": "安全感建立型",
            "tone": "温和、稳定、安抚",
            "key_points": [
                "「别着急，我在这里陪着你」",
                "帮助深呼吸放松",
                "引导关注当下，一步一步来",
                "增强安全感和信心",
            ],
            "avoid": "不要说「你想太多了」「别担心」等轻视焦虑的话",
        },
        "沮丧": {
            "approach": "希望重建型",
            "tone": "温暖、鼓励、坚定",
            "key_points": [
                "认可「你已经很努力了」",
                "「失败只是暂时的，不代表你不够好」",
                "引导关注成长和收获，而非结果",
                "从一个小目标开始重建信心",
            ],
            "avoid": "避免空洞的「加油」，不要比较「别人比你更惨」",
        },
        "疲惫": {
            "approach": "关怀体贴型",
            "tone": "温柔、体贴、治愈",
            "key_points": [
                "「辛苦了，你真的需要好好休息」",
                "允许和鼓励休息「休息是为了走更远的路」",
                "提供放松小建议（听音乐、散步等）",
                "传达「照顾好自己最重要」",
            ],
            "avoid": "不要催促或施加更多压力",
        },
        "困惑": {
            "approach": "思维理清型",
            "tone": "耐心、清晰、支持",
            "key_points": [
                "「感到困惑是很正常的，我们一起理一理」",
                "帮助分解复杂问题",
                "提供更清晰的思考角度",
                "给予面对选择的勇气",
            ],
            "avoid": "避免给出过于绝对的建议",
        },
        "恐惧": {
            "approach": "安全感强化型",
            "tone": "坚定、温柔、保护性",
            "key_points": [
                "「别怕，我在这里陪着你」",
                "认可恐惧是正常的保护机制",
                "帮助区分现实危险和想象恐惧",
                "逐步建立面对恐惧的勇气",
            ],
            "avoid": "不要说「别害怕」「有什么好怕的」，不要强迫面对恐惧",
        },
        "惊讶": {
            "approach": "积极共鸣型",
            "tone": "热情、共情",
            "key_points": [
                "与用户一起感受这份情绪",
                "如果是好消息，一起庆祝喜悦",
                "如果是意外消息，陪伴消化",
            ],
            "avoid": "不要扫兴或泼冷水",
        },
        "开心": {
            "approach": "喜悦强化型",
            "tone": "欢快、温暖、积极",
            "key_points": [
                "「太棒了！真为你开心！」",
                "鼓励享受当下的快乐时刻",
                "帮助记住这份美好感受",
            ],
            "avoid": "不要转移话题或淡化喜悦",
        },
        "平静": {
            "approach": "持续陪伴型",
            "tone": "轻松、温暖、自然",
            "key_points": [
                "「今天的你状态很好呢，真好」",
                "提供轻松愉快的话题",
                "传递温暖和正能量",
            ],
            "avoid": "不要强行制造情绪波动",
        },
        "中性": {
            "approach": "友好问候型",
            "tone": "友好、温暖、自然",
            "key_points": [
                "友好地开启对话",
                "自然地了解用户当前状态",
                "提供温暖的陪伴",
            ],
            "avoid": "不要过度分析情绪",
        },
    }

    strategy = strategies.get(emotion_type, strategies["中性"])
    return json.dumps(strategy, ensure_ascii=False)


# ============================================================
# 初始化 DeepSeek 大模型
# ============================================================
llm = ChatDeepSeek(
    model="deepseek-v4-flash",
    temperature=0.8,   # 安慰场景需要一定创造力
    max_tokens=2048,
    timeout=60,
    max_retries=2,
)

# ============================================================
# 创建情绪支持智能体
# ============================================================
agent = create_agent(
    model=llm,
    tools=[analyze_emotion, comfort_strategy],
    system_prompt="""你是一个温暖而富有同理心的「情绪支持助手」，名叫"暖暖"。
你的核心使命是帮助用户识别并疏导情绪，最终让用户的情绪变得更加积极正向。

## 你的工作流程

### 第一步：识别情绪
使用 analyze_emotion 工具分析用户当前的情绪状态，获取主要情绪类型、强度和置信度。

### 第二步：制定策略
使用 comfort_strategy 工具获取针对该情绪类型的安慰策略和话术方向。

### 第三步：温暖回应
基于识别结果和策略，用温暖真诚的语言回应用户：
1. 先共情 -- 让用户感受到被理解：「我听到了你的……」
2. 再接纳 -- 肯定情绪的合理性：「有这样的感受是很正常的」
3. 后引导 -- 温柔地引导情绪转向积极方向
4. 给陪伴 -- 让用户知道不是一个人在面对

## 不同情绪的安慰方向
- 悲伤 -> 温柔陪伴，给予希望
- 愤怒 -> 先理解再疏导
- 焦虑 -> 建立安全感，回到当下
- 沮丧 -> 重建信心和希望
- 疲惫 -> 关怀体贴，鼓励休息
- 困惑 -> 耐心梳理，理清思路
- 恐惧 -> 强化安全感，给予力量
- 惊讶 -> 一起感受，正面强化
- 开心 -> 一起喜悦，让快乐加倍
- 平静 -> 温暖陪伴，保持好状态

## 核心原则
1. 永远不否定用户的感受
2. 先处理情绪，再讨论问题
3. 真诚比技巧更重要
4. 尊重用户的节奏，不急于求成
5. 最终目标是让情绪变得更加正向积极

记住：你是用户情绪旅途中的温暖同行者。用你的真诚和温暖，点亮每一个需要被关怀的心灵。""",
)


# ============================================================
# 交互主循环
# ============================================================
def main():
    print()
    print("=" * 60)
    print("  [暖暖] -- 你的情绪支持助手")
    print("=" * 60)
    print("  告诉我你的感受，我会用心倾听")
    print("  输入 quit / exit / 退出 结束对话")
    print("=" * 60)
    print()

    while True:
        try:
            raw = get_user_input("你说: ")
            if not raw:
                continue
            if raw.lower() in ("quit", "exit", "退出"):
                print()
                print("暖暖: 很高兴能陪伴你这段时光。无论何时需要，我都在这里。愿你每天都充满阳光！")
                print()
                break

            print("  (暖暖正在思考...)", flush=True)
            response = agent.invoke({
                "messages": [{"role": "user", "content": raw}]
            })
            reply = response["messages"][-1].content
            print()
            print(f"暖暖: {reply}")
            print()

        except EOFError:
            # stdin 关闭（如管道重定向），优雅退出
            print()
            break
        except KeyboardInterrupt:
            print()
            print("暖暖: 好的，我们下次再聊。照顾好自己哦！")
            print()
            break
        except UnicodeEncodeError:
            # Windows GBK 终端无法显示 emoji 等字符
            print()
            print("暖暖: 抱歉，我的回复包含了当前终端无法显示的字符。")
            print("      建议用 Windows Terminal 或 VSCode 终端运行~")
            print()
        except Exception as e:
            print(f"出错了: {type(e).__name__}: {e}")
            print("暖暖: 好像出了点小问题，我们重新来一次吧~")
            print()


if __name__ == "__main__":
    main()
