from serpapi import SerpApiClient
import os
from dotenv import load_dotenv

load_dotenv()

def search(query:str) -> str:
    """
    一个基于SerpApi的网页搜索工具
    实现智能解析搜索结果，返回答案或知识图谱
    """
    print(f"🔍 正在执行 [SerpApi] 网页搜索: {query}")
    try:
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            return "SERPAPI_API_KEY未在.env中配置"
        
        params = {
            "engine":"google",
            "q":query,
            "api_key":api_key,
            "gl":"cn", # 国家代码
            "hl":"zh-cn", # 语言代码
        }

        client = SerpApiClient(params)
        results = client.get_dict()

        # 检查是否存在 answer_box （Google的答案摘要框）或 knowledge_graph （知识图谱）等信息
        if "answer_box_list" in results:
            return "\n".join(results["answer_box_list"])
        if "answer_box" in results and "answer" in results["answer_box"]:
            return results["answer_box"]["answer"]
        if "knowledge_graph" in results and "description" in results["knowledge_graph"]:
            return results["knowledge_graph"]["description"]
        if "organic_results" in results and results["organic_results"]:
            # 如果没有直接答案，则返回前三个有机结果的摘要
            snippets = [
                f"[{i+1}] {res.get('title', '')}\n{res.get('snippet', '')}"
                for i, res in enumerate(results["organic_results"][:3])
            ]
            return "\n\n".join(snippets)

        return f"对不起，没有找到关于 '{query}' 的信息。"

    except Exception as e:
        return f"搜索时发生错误: {e}"