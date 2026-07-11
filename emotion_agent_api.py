"""
FastAPI 后端 —— 暖暖情绪支持助手 API
为 Streamlit 等前端提供 /chat 接口
"""

from fastapi import FastAPI, Body
from fastapi.responses import StreamingResponse
import uvicorn
from emotion_agent import get_llm_agent

app = FastAPI(title="暖暖情绪支持助手")


@app.get("/")
async def root():
    return {"message": "欢迎来到暖暖情绪支持助手，发送 POST /chat 开始聊天"}


@app.post("/chat")
async def chat(query: str = Body(..., description="用户的输入数据", embed=True)):
    """
    接收用户输入 → 调用 LangChain 智能体 → 流式返回回复
    """
    answer = get_llm_agent(query)

    async def stream_answer():
        for char in answer:
            yield char

    return StreamingResponse(stream_answer(), media_type="text/plain")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
