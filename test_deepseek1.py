from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
# 初始化模型
load_dotenv()
llm = ChatDeepSeek(
    model="deepseek-v4-flash",      # 或 "deepseek-v4-pro"
    temperature=0,
    max_tokens=512,
    timeout=60,
    max_retries=2,
)

# 基础对话
messages = [
    ("system", "你是一个乐于助人的助手。"),  # 系统指令
    ("human", "你能告诉我一些关于人工智能的信息吗？"),      # 用户问题
]

# 调用模型并获取响应
response = llm.invoke(messages)

# 打印回复内容
print("AI 回复:", response.content)
# （可选）打印 token 使用情况
print("Token 使用情况:", response.usage_metadata)