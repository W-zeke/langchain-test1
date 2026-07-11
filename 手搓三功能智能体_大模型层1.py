'''准备工具，langchain当作大模型的手和脚'''
#创建智能体
from langchain.agents import create_agent
#定义工具
from langchain_core.tools import Tool
#加载OpenAi的对话模型
from langchain_openai import ChatOpenAI
#引入刚定义的三个工具
from tool01_gettime import get_time
from tool02_translate import translate
from tool03_weather import get_weather
#定义工具插件
tools = [
    Tool(name="get time",
         func=get_time,
         description="获得当前系统时间，这个工具可以接收任意形式的参数，也可以不传参直接调用"
         ),
    Tool(name="translate",
         func=translate,
         description="实现单词或者文本的翻译，输入从的参数是需要翻译的内容，比如hello"
         ),
    Tool(name="get weather",
         func=get_weather,
         description="获取某个城市的未来7天的天气情况，输入的参数的城市的名称字符串，比如：北京"
         )
]
#准备大模型
llm = ChatOpenAI(
    base_url="https://api.siliconflow.cn/v1",
    openai_api_key="sk-ggsbvjqakkovqxyrgbgrwpeyfodccyeynobxmnupdzhesozf",
    model="Pro/MiniMaxAI/MiniMax-M2.5"
)
#创建智能体，-----  工具 大模型 系统提示词 打包起来。
agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt="你是一个淘气的有用的助手，可以调用工具回答用户的问题"
)



massage = {"messages":[{"role":"user","content":"你是谁，翻译一下message，现在几点了"}]}
#-------流式的形式得到智能体的响应---------
# for chunk in agent.stream(massage):
#     # print(chunk)
#     #在控制打印出智能体正在调用的工具的名称，以及最终得到的工具给的结果
#     if "tools" in chunk:#调用了工具后的输出结果
#         print(chunk["tools"]["messages"][0].content,flush=True)#强制输出，不是等缓存完了再输出
#         print(chunk["tools"]["messages"][0].name,flush=True)

#------------非流式，一次性得到智能体的结果
# response = agent.invoke(massage)
# # print(response)
# print(response['messages'][-1].content)
#定义一个函数，接收一个段字符串，最终响应智能体的结果
def get_llm_agent(query):
    response = agent.invoke({
        "messages":[{"role":"user","content":query}]
    })
    #需要优化，体力活
    return response['messages'][-1].content

# result = get_llm_agent("你是谁，今天温州的天气怎么样？")
# print(result)
