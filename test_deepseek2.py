import requests
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_deepseek import ChatDeepSeek
from langchain_core.tools import tool
load_dotenv()
# 初始化模型
@tool
def get_weather(city:str) -> str:
    """获取天气信息的工具函数，输入城市名称，返回天气描述。"""
    try:
        # 这里可以调用实际的天气API获取天气信息，以下是示例返回
        url=f"https://wttr.in/{city}?format=3"
        response=requests.get(url,timeout=10)
        if response.status_code==200:
            return f"{city}: {response.text.strip()}"
        else:
            return f"无法获取{city}的天气信息，状态码: {response.status_code}"
    except Exception as e:
        return f"获取天气信息错误: {e}"
@tool
def calculate(expression:str) -> str:
    """计算表达式的工具函数，输入数学表达式，返回计算结果。"""
    try:
        result=eval(expression)
        return f"计算结果:{result}"
    except Exception as e:
        return f"计算错误:{e}"
llm=ChatDeepSeek(
    model="deepseek-v4-flash",      # 或 "deepseek-v4-pro
    temperature=0,
    max_tokens=512,
    timeout=60,
    max_retries=2,
)
agent=create_agent(
    model=llm,      # 或 "deepseek-v4-pro
    tools=[get_weather,calculate],
    system_prompt="你是一个乐于助人的助手，能够提供天气信息和计算功能。",  # 系统指令
)
# 获取用户输入
city = input("请输入城市名称: ")
expression = input("请输入数学表达式: ")

user_input = f"请告诉我{city}的天气，并计算{expression}的结果。"
response=agent.invoke({
    "messages":[
        {"role":"user","content":user_input}
    ]
})
print(response["messages"][-1].content)