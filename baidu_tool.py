"""
百度联网搜索工具
提供：原始搜索、搜索判断、搜索上下文组装
"""

from baidusearch.baidusearch import search
import time


def baidu_web_search(query: str, page_size: int = 4) -> list:
    """
    免费百度网页搜索工具，无需任何API密钥
    :param query: 搜索关键词
    :param page_size: 返回结果数量
    :return: [{"title":"标题","summary":"摘要","url":"链接"},...]
    """
    # 间隔防封禁
    time.sleep(0.3)
    raw_results = search(query, num_results=page_size)
    output = []
    for item in raw_results:
        output.append({
            "title": item["title"],
            "summary": item["abstract"],
            "url": item["url"]
        })
    return output


def judge_need_search(question: str, llm_func) -> bool:
    """
    让 LLM 判断是否需要联网搜索
    :param question: 用户问题
    :param llm_func: 接收 prompt 返回文本的 LLM 调用函数（如主文件的 llm_response）
    :return: True 需要搜索，False 不需要
    """
    judge_prompt = f"""你是搜索判断器，只输出True或False，不要任何多余文字。
需要联网搜索（True）场景：实时新闻、2026最新数据、政策、赛事、今日行情、时效性资讯、当下产品价格。
不需要搜索（False）场景：基础常识、数学计算、小说创作、代码编写、历史固定知识、逻辑推理。
用户问题：{question}"""
    ans = llm_func(judge_prompt).strip()
    return ans == "True"


def build_search_context(question: str, llm_func, page_size: int = 4) -> str:
    """
    判断 → 搜索 → 组装上下文，一步完成
    :param question: 用户问题
    :param llm_func: 接收 prompt 返回文本的 LLM 调用函数
    :param page_size: 搜索结果条数
    :return: 组装好的搜索上下文（空字符串表示无需搜索或无结果）
    """
    if not judge_need_search(question, llm_func):
        return ""

    print(f"[触发百度搜索] 关键词：{question}")
    search_data = baidu_web_search(question, page_size=page_size)
    if not search_data:
        return ""

    context = "=====百度实时搜索结果=====\n"
    for i, item in enumerate(search_data, 1):
        context += f"{i}.标题：{item['title']}\n摘要：{item['summary']}\n来源链接：{item['url']}\n\n"
    return context


# 本地测试
if __name__ == "__main__":
    res = baidu_web_search("2026年7月人工智能最新资讯", 3)
    for idx, r in enumerate(res, 1):
        print(f"【{idx}】{r['title']}")
        print(f"摘要：{r['summary']}\n链接：{r['url']}\n")
