"""安装环境：pip install baidusearch requests"""

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

# 本地测试工具
if __name__ == "__main__":
    res = baidu_web_search("2026年7月人工智能最新资讯", 3)
    for idx, r in enumerate(res, 1):
        print(f"【{idx}】{r['title']}")
        print(f"摘要：{r['summary']}\n链接：{r['url']}\n")
