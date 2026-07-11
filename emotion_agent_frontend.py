"""
Streamlit 前端 —— 暖暖情绪支持助手聊天界面
调用 FastAPI 后端 /chat 接口，实现对话交互
"""

import streamlit as st
import requests
from typing import Generator

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title="暖暖 - 情绪支持助手",
    page_icon="💛",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ============================================================
# 自定义 CSS —— 温暖治愈风格
# ============================================================
st.markdown("""
<style>
    /* ===== 全局样式 ===== */
    .stApp {
        background: linear-gradient(135deg, #fef9f0 0%, #fff5e8 100%);
    }
    
    /* ===== 标题样式 ===== */
    .title-container {
        text-align: center;
        padding: 1.5rem 0 0.5rem 0;
    }
    .title-container h1 {
        font-size: 2.5rem;
        color: #e8896e;
        margin-bottom: 0.2rem;
    }
    .title-container p {
        color: #b0897a;
        font-size: 1rem;
    }
    
    /* ===== 用户消息 ===== */
    [data-testid="user-chat-message"] {
        background-color: #f0e6de;
        border-radius: 18px 18px 4px 18px;
        padding: 0.75rem 1rem;
        margin: 0.3rem 0;
        color: #3a3a3a !important;
    }
    [data-testid="user-chat-message"] *,
    [data-testid="user-chat-message"] p,
    [data-testid="user-chat-message"] span,
    [data-testid="user-chat-message"] div,
    [data-testid="user-chat-message"] .stMarkdown {
        color: #3a3a3a !important;
    }

    /* ===== 助手消息 ===== */
    [data-testid="assistant-chat-message"] {
        background-color: #ffffff;
        border-radius: 18px 18px 18px 4px;
        padding: 0.75rem 1rem;
        margin: 0.3rem 0;
        border: 1px solid #f0e6de;
        color: #3a3a3a !important;
    }
    [data-testid="assistant-chat-message"] *,
    [data-testid="assistant-chat-message"] p,
    [data-testid="assistant-chat-message"] span,
    [data-testid="assistant-chat-message"] div,
    [data-testid="assistant-chat-message"] .stMarkdown {
        color: #3a3a3a !important;
    }

    /* ===== 额外兜底：Streamlit 聊天容器 ===== */
    [data-testid="chatMessageContainer"] [data-testid="chatMessage"] * {
        color: #3a3a3a !important;
    }
    [data-testid="stChatMessage"] *,
    .stChatMessage * {
        color: #3a3a3a !important;
    }
    
    /* ===== 输入框 ===== */
    .stTextInput>div>div>input {
        border-radius: 24px;
        border: 2px solid #f0d5c8;
        padding: 0.5rem 1.2rem;
        background-color: #ffffff;
        color: #2c3e50;  /* ← 输入框文字颜色 */
    }
    .stTextInput>div>div>input:focus {
        border-color: #e8896e;
        box-shadow: 0 0 0 2px rgba(232, 137, 110, 0.2);
    }
    
    /* ===== 侧边提示 ===== */
    .sidebar-hint {
        background: #fff5e8;
        padding: 1rem;
        border-radius: 12px;
        border-left: 4px solid #e8896e;
        font-size: 0.9rem;
        color: #5a4a3a;  /* ← 提示文字颜色 */
    }
    
    footer { display: none; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 后端 API 地址
# ============================================================
API_URL = "http://127.0.0.1:8001/chat"


# ============================================================
# 调用后端
# ============================================================
def call_backend(query: str) -> Generator[str, None, None]:
    """
    调用 FastAPI 后端的 /chat 接口，以流式方式获取回复。
    """
    try:
        with requests.post(
            API_URL,
            json={"query": query},
            stream=True,
            timeout=60,
        ) as resp:
            resp.raise_for_status()
            for chunk in resp.iter_content(chunk_size=1, decode_unicode=True):
                if chunk:
                    yield chunk
    except requests.exceptions.ConnectionError:
        yield "😅 连接不到后端服务，请确认 FastAPI 是否已启动（uvicorn）"
    except requests.exceptions.Timeout:
        yield "⏰ 请求超时了，请稍后再试~"
    except Exception as e:
        yield f"😔 出错了: {e}"


# ============================================================
# 初始化对话历史
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "你好呀，我是「暖暖」☀️\n\n"
                       "告诉我你的感受，我会用心倾听，陪你一起让心情变得更好～",
        }
    ]

# 记录已处理的消息（防 rerun 重复处理）
if "processed_count" not in st.session_state:
    st.session_state.processed_count = 0


# ============================================================
# 页面标题
# ============================================================
st.markdown(
    '<div class="title-container">'
    '<h1>💛 暖暖</h1>'
    '<p>你的情绪支持助手 · 用心倾听，温暖陪伴</p>'
    "</div>",
    unsafe_allow_html=True,
)

# ============================================================
# 侧边栏 —— 使用提示
# ============================================================
with st.sidebar:
    st.markdown("### 🌸 关于暖暖")
    st.markdown(
        '<div class="sidebar-hint">'
        "我是你的情绪支持助手，你可以跟我说说："
        "</div>",
        unsafe_allow_html=True,
    )
    examples = [
        "😢 今天心情不太好…",
        "😠 气死我了！",
        "😰 我好焦虑",
        "😌 最近有点累",
        "🥰 我今天超开心！",
    ]
    prompt_from_sidebar = None
    for ex in examples:
        if st.button(ex, use_container_width=True, type="tertiary"):
            prompt_from_sidebar = ex

    st.divider()
    st.caption("💡 需要先启动后端：")
    st.code("uvicorn emotion_agent_api:app --host 127.0.0.1 --port 8001 --reload")
    st.caption("Powered by LangChain + DeepSeek")

# ============================================================
# 显示对话历史
# ============================================================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ============================================================
# 输入框 & 发送
# ============================================================

# 优先取侧边栏按钮触发的输入，其次取聊天输入框
prompt = prompt_from_sidebar or st.chat_input("说说你的感受吧...")

if prompt and len(st.session_state.messages) >= st.session_state.processed_count:
    # 标记已处理，防止 rerun 重复
    st.session_state.processed_count = len(st.session_state.messages) + 2  # user + assistant

    # 用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 助手回复（流式）
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        collected = ""
        for chunk in call_backend(prompt):
            collected += chunk
            response_placeholder.markdown(collected + "▌")
        response_placeholder.markdown(collected)

    st.session_state.messages.append({"role": "assistant", "content": collected})
    st.rerun()
