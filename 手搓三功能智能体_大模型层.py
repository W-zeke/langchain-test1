'''准备工具，langchain当作大模型的手和脚'''
#创建智能体
from langchain.agents import create_agent
#定义工具
from langchain_core.tools import Tool
#加载OpenAi的对话模型
from langchain_openai import ChatOpenAI
#引入刚定义的三个工具
from tool01_gettime import get_time
from baidu_tool import baidu_web_search

#搜索判断
def llm_response(prompt: str) -> str:
    """基础LLM单次问答调用"""
    messages = [{"role": "user", "content": prompt}]
    res = llm.invoke(messages)
    return res.content

def judge_need_search(question: str) -> bool:
    """智能体自主判断是否需要联网搜索"""
    judge_prompt = """
你是搜索判断器，只输出True或False，不要任何多余文字。
需要联网搜索（True）场景：实时新闻、2026最新数据、政策、赛事、今日行情、时效性资讯、当下产品价格。
不需要搜索（False）场景：基础常识、数学计算、小说创作、代码编写、历史固定知识、逻辑推理。
用户问题：{q}
    """.format(q=question)
    ans = llm_response(judge_prompt).strip()
    return ans == "True"

def run_agent(user_input: str):
    print("\n[智能体思考中...]")
    need_search = judge_need_search(user_input)
    search_context = ""
    if need_search:
        print(f"[触发百度搜索] 关键词：{user_input}")
        search_data = baidu_web_search(user_input, page_size=4)
        search_context = "=====百度实时搜索结果=====\n"
        for i, item in enumerate(search_data, 1):
            search_context += f"{i}.标题：{item['title']}\n摘要：{item['summary']}\n来源链接：{item['url']}\n\n"
    # 组装回答Prompt
    final_prompt = f"""
{search_context}
基于上方实时搜索资料（如有）准确回答用户问题；若无搜索资料，使用自身知识库回答。
回答简洁清晰，有实时资料时必须以搜索内容为依据。
用户问题：{user_input}
"""
    reply = llm_response(final_prompt)
    return reply


#定义工具插件
tools = [
    Tool(name="get time",
         func=get_time,
         description="获得当前系统时间，这个工具可以接收任意形式的参数，也可以不传参直接调用"
         ),
    Tool(name="baidu web_search",
         func=baidu_web_search,
         description="进行联网搜索，这个工具可以接受任意形式参数，也可以不传参自主判断调用")
]
#准备大模型
llm = ChatOpenAI(
    base_url="https://api.siliconflow.cn/v1",
    openai_api_key="sk-umjtmstvskfhwbfogzwujinpxyxlmzpygssbvtmgcguiwinb",
    model="Qwen/Qwen3.5-4B"
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

