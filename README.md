# 暖暖情绪支持智能体 — 功能与技术栈分析

## 一、项目概述

「暖暖」是一个基于 **LangChain + DeepSeek** 构建的情绪支持对话智能体，能够识别用户的情绪状态并给出有温度、有策略的安慰回应。项目由 5 个核心文件组成，采用三层架构：

| 层级 | 文件 | 职责 |
|------|------|------|
| **工具层** | `tool01_analyze_emotion.py` | 基于关键词的情绪识别引擎 |
| | `tool02_comfort_strategy.py` | 情绪→安慰策略映射规则库 |
| **智能体层** | `emotion_agent.py` | LangChain Agent 编排核心 |
| **API 层** | `emotion_agent_api.py` | FastAPI 后端服务 |
| **前端层** | `emotion_agent_frontend.py` | Streamlit 聊天界面 |

---

## 二、核心功能

### 2.1 情绪识别（tool01_analyze_emotion.py）

基于**关键词匹配 + 否定检测**的轻量情绪分类器：

- **11 种情绪分类**：开心、悲伤、愤怒、焦虑、沮丧、疲惫、困惑、恐惧、惊讶、平静、中性
- **关键词词典**：每种情绪对应一组触发词，逐词扫描用户输入统计命中次数
- **否定检测**：正则匹配 `不[情绪词]` 模式（如"不难过"），将对应情绪得分乘以 0.3 降低权重
- **置信度计算**：根据主要情绪得分与次主要情绪得分的比值计算，上限 0.95
- **强度分级**：得分 ≥5 → 高，≥2 → 中，<2 → 低
- **返回格式**：JSON，包含 `primary_emotion`、`confidence`、`intensity` 字段

### 2.2 安慰策略（tool02_comfort_strategy.py）

一个声明式的 **情绪→策略映射表**：

- 11 种情绪各对应一套完整策略，包含：
  - **approach**（策略类型）：如"共情陪伴型"、"情绪疏导型"、"安全感建立型"
  - **tone**（语气建议）：如"温柔、耐心、包容"
  - **key_points**（关键话术点）：3-5 条具体引导方向
  - **avoid**（避免说的话）：防止火上浇油
- 输入情绪名称，返回对应的 JSON 策略对象
- 未知情绪兜底到"中性"策略

### 2.3 智能体编排（emotion_agent.py）

LangChain Agent 的核心编排逻辑：

- **工具注册**：将 `analyze_emotion` 和 `comfort_strategy` 包装为 LangChain `Tool` 对象
- **LLM 配置**：使用 `ChatDeepSeek` 模型（`deepseek-v4-flash`），temperature=0.8
- **系统提示词**：定义智能体人格（"暖暖"）、三步工作流（识别→策略→回应）、5 条核心原则
- **调用接口**：`get_llm_agent(query)` 接收用户文本，返回智能体回复
- **工作流程**：LLM 自主决定何时调用工具 → 先分析情绪 → 再查询策略 → 最后生成温暖回复

### 2.4 API 服务（emotion_agent_api.py）

FastAPI 轻量后端：

- `POST /chat`：接收用户输入，调用智能体，以 **流式响应（StreamingResponse）** 逐字返回
- `GET /`：健康检查端点
- 默认运行在 `127.0.0.1:8001`，支持 uvicorn 热重载

### 2.5 前端界面（emotion_agent_frontend.py）

Streamlit 单页聊天应用：

- 暖色调治愈风 UI（渐变背景、圆角气泡、定制 CSS）
- 流式展示回复（逐字输出，带光标闪烁效果）
- 侧边栏预设情绪快捷按钮
- 对话历史持久化（session_state）

---

## 三、技术栈

| 技术 | 用途 | 版本（参考） |
|------|------|-------------|
| **Python** | 开发语言 | 3.x |
| **LangChain** | Agent 编排框架（工具注册、模型调用） | 最新版 |
| **langchain-deepseek** | LangChain 与 DeepSeek 模型的集成适配器 | — |
| **DeepSeek** | 底层大语言模型（`deepseek-v4-flash`） | v4-flash |
| **FastAPI** | RESTful API 框架 | 0.139.0 |
| **Uvicorn** | ASGI 服务器 | 0.51.0 |
| **Streamlit** | 前端聊天界面 | 1.59.1 |
| **python-dotenv** | 环境变量管理（API Key） | 1.2.2 |
| **Requests** | HTTP 客户端（前端调用后端） | 2.34.2 |

### 架构图

```
用户输入
    │
    ▼
┌─────────────────────────────────────┐
│  Streamlit 前端                      │
│  emotion_agent_frontend.py          │
│  (聊天UI + 对话历史)                  │
└──────────┬──────────────────────────┘
           │ HTTP POST (流式)
           ▼
┌─────────────────────────────────────┐
│  FastAPI 后端                        │
│  emotion_agent_api.py               │
│  (StreamingResponse)                 │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  LangChain Agent                    │
│  emotion_agent.py                   │
│  (系统提示词 + 工具注册)              │
├─────────────────────────────────────┤
│  ┌──────────┐  ┌───────────────┐   │
│  │ 情绪识别   │  │ 安慰策略      │   │
│  │ analyze_  │  │ comfort_     │   │
│  │ emotion   │  │ strategy     │   │
│  └──────────┘  └───────────────┘   │
├─────────────────────────────────────┤
│  ChatDeepSeek (LLM)                 │
│  deepseek-v4-flash                   │
└─────────────────────────────────────┘
```

---

## 四、关键设计决策

### 4.1 工具 vs 纯 Prompt

情绪识别和策略查询被设计为**独立工具**而非直接写在 prompt 中，好处是：
- 情绪识别逻辑**可控、可测试、可调试**，不依赖模型稳定性
- 策略库可独立扩展，新增情绪只需添加词典条目
- 降低对 LLM 的 prompt 依赖，节省 token

### 4.2 关键词情绪识别

当前方案使用简单的关键词匹配而非模型推理，属于**轻量级 MVP 方案**：
- ✅ 速度快，无额外 API 调用成本
- ✅ 确定性高，不会出现幻觉
- ❌ 无法理解复杂语境（反讽、隐喻）
- ❌ 不支持细粒度情感分析（如情绪渐变）

### 4.3 流式响应

后端使用 `StreamingResponse` 逐字返回，前端用 `st.empty()` 占位符实现打字机效果，提升用户体验。

### 4.4 防重复处理

前端通过 `processed_count` 机制防止 Streamlit rerun 导致重复提交（已修复 `>` → `>=` 的边界 bug）。

---

## 五、可能的改进方向

1. **情绪识别升级**：接入 LLM 或专用情感分析模型，提升准确性
2. **对话记忆**：引入 `ConversationBufferMemory`，让智能体能记住上下文
3. **策略个性化**：根据用户历史偏好动态调整安慰策略
4. **多轮情绪追踪**：在对话中追踪情绪变化曲线
5. **安全性增强**：API Key 应放入 `.env`（已实现），生产环境需加速率限制

---

## 六、运行方式

```bash
# 1. 安装依赖
pip install langchain langchain-deepseek python-dotenv fastapi uvicorn streamlit requests

# 2. 配置环境变量（.env）
DEEPSEEK_API_KEY=sk-xxx

# 3. 启动后端（终端1）
uvicorn emotion_agent_api:app --host 127.0.0.1 --port 8001 --reload

# 4. 启动前端（终端2）
streamlit run emotion_agent_frontend.py
```

---

*分析日期：2026-07-11*
