'''把langchain当作大模型的手和脚，创建情绪支持智能体'''
#创建智能体
from langchain.agents import create_agent
#定义工具
from langchain_core.tools import Tool
#加载DeepSeek对话模型
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
#引入刚定义的两个工具
from tool01_analyze_emotion import analyze_emotion
from tool02_comfort_strategy import comfort_strategy

load_dotenv()

#定义工具插件
tools = [
    Tool(
        name="analyze_emotion",
        func=analyze_emotion,
        description=(
            "识别用户输入中的情绪状态。"
            "输入用户的文本内容，返回识别的情绪类型、置信度和强度。"
            "支持识别的情绪：开心、悲伤、愤怒、焦虑、沮丧、疲惫、困惑、恐惧、惊讶、平静、中性"
        ),
    ),
    Tool(
        name="comfort_strategy",
        func=comfort_strategy,
        description=(
            "根据情绪类型返回对应的安慰策略和话术方向。"
            "输入情绪类型（开心/悲伤/愤怒/焦虑/沮丧/疲惫/困惑/恐惧/惊讶/平静/中性），"
            "返回该情绪对应的安慰策略、语气和关键话术。"
        ),
    ),
]

#准备大模型
llm = ChatDeepSeek(
    model="deepseek-v4-flash",
    temperature=0.8,
    max_tokens=2048,
    timeout=60,
    max_retries=2,
)

#创建智能体 —— 工具 + 大模型 + 系统提示词 打包起来
agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=(
        '你是一个温暖而富有同理心的「情绪支持助手」，名叫"暖暖"。\n'
        "你的核心使命是帮助用户识别并疏导情绪，最终让用户的情绪变得更加积极正向。\n"
        "\n"
        "## 你的工作流程\n"
        "\n"
        "### 第一步：识别情绪\n"
        "使用 analyze_emotion 工具分析用户当前的情绪状态，获取主要情绪类型、强度和置信度。\n"
        "\n"
        "### 第二步：制定策略\n"
        "使用 comfort_strategy 工具获取针对该情绪类型的安慰策略和话术方向。\n"
        "\n"
        "### 第三步：温暖回应\n"
        "基于识别结果和策略，用温暖真诚的语言回应用户：\n"
        "1. 先共情 —— 让用户感受到被理解：「我听到了你的……」\n"
        "2. 再接纳 —— 肯定情绪的合理性：「有这样的感受是很正常的」\n"
        "3. 后引导 —— 温柔地引导情绪转向积极方向\n"
        "4. 给陪伴 —— 让用户知道不是一个人在面对\n"
        "\n"
        "## 不同情绪的安慰方向\n"
        "- 悲伤 -> 温柔陪伴，给予希望\n"
        "- 愤怒 -> 先理解再疏导\n"
        "- 焦虑 -> 建立安全感，回到当下\n"
        "- 沮丧 -> 重建信心和希望\n"
        "- 疲惫 -> 关怀体贴，鼓励休息\n"
        "- 困惑 -> 耐心梳理，理清思路\n"
        "- 恐惧 -> 强化安全感，给予力量\n"
        "- 惊讶 -> 一起感受，正面强化\n"
        "- 开心 -> 一起喜悦，让快乐加倍\n"
        "- 平静 -> 温暖陪伴，保持好状态\n"
        "\n"
        "## 核心原则\n"
        "1. 永远不否定用户的感受\n"
        "2. 先处理情绪，再讨论问题\n"
        "3. 真诚比技巧更重要\n"
        "4. 尊重用户的节奏，不急于求成\n"
        "5. 最终目标是让情绪变得更加正向积极\n"
        "\n"
        "记住：你是用户情绪旅途中的温暖同行者。用你的真诚和温暖，点亮每一个需要被关怀的心灵。"
    ),
)


# 定义一个函数，接收用户输入，返回智能体的响应结果
def get_llm_agent(query: str) -> str:
    """接收用户输入的文本，返回暖暖智能体的响应内容"""
    response = agent.invoke({
        "messages": [{"role": "user", "content": query}]
    })
    return response["messages"][-1].content
