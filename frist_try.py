import requests
import json
import os
from tavily import TavilyClient
from openai import OpenAI
import re

agent_prompt = """
你是一个智能旅行助手，你的任务是逐步分析用户的需求，你可以使用工具逐步解决需求。

# 可用工具
- `get_weather(city: str)`: 查询指定城市的实时天气。
- `get_attraction(city: str, weather: str)`: 根据城市和天气搜索推荐的旅游景点。

# 行动规范
你的回答必须严格遵循以下格式，首先是你的思考过程，其次是你需要执行的具体行动
Think：[这里是你的思考过程和规划]
Action：[这是你要调用的工具，格式为：function_name(arg_name="arg_value")]

当你认为完成任务后，足够解决用户需求并回答用户问题时，你必须在Action后加入'finish(answer='value')'
注意你需要把这里的value解析为用户能够理解的自然语言。

注意：如果你发现景点门票已经售罄，请你更换备选方案；如果用户连续拒接了三个推荐，你需要反思并调整推荐策略，这时你可以询问用户的偏好
请立即开始行动！
"""

def get_weather(city:str) -> str:
    """调用API查询真实天气信息"""
    url = f"https://wttr.in/{city}?format=j1"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        current_condition = data['current_condition'][0]
        weather_desc = current_condition['weatherDesc'][0]['value']
        temp_c = current_condition['temp_C']
        return f"{city}当前天气：{weather_desc},气温{temp_c}摄氏度。"
    except requests.exceptions.RequestException as e:
        return f"错误：查询天气遇到错误：{e}"
    except (KeyError,IndexError) as e:
        return f"错误：解析天气数据失败，请检查城市名！{e}"

def get_attraction(city:str,weather:str) -> str:
    '''根据城市和天气，使用tavily的API搜索并返回景点推荐'''
    api_key = "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"
    if not api_key:
        return "API配置错误！"
    tavily = TavilyClient(api_key=api_key)
    query = f"'{city}'在{weather}天气下最适合去的景点推荐及理由"
    try:
        response = tavily.search(query=query,search_depth="basic",include_answer=True)
        print("="*30)
        print(f"Tavily API的response：{response}")
        print("="*30)
        if response.get('answer'):
            return response['answer']
        formatted_results = []
        for result in response.get('results',[]):
            formatted_results.append(f"-{result['title']}:{result['content']}")
        if not formatted_results:
            return "没有找到相关景点推荐!"
        return "根据搜索结果，为您找到以下信息：\n"+"\n".join(formatted_results)
    except Exception as e:
        return f"错误：执行Tavily API时出现错误：{e}"

# 修复工具名拼写错误（之前已改，确认无误）
tools_dict = {
    "get_weather": get_weather,
    "get_attraction": get_attraction,
}

class OpenAICompatibleClient:
    """兼容OpenAI接口的LLM客户端"""
    def __init__(self,model:str,api_key:str,base_url:str):
        self.model = model
        self.client = OpenAI(api_key=api_key,base_url=base_url)
    
    def generate(self,prompt:str,system_prompt:str) -> str:
        print("正在调用大模型...")
        try:
            messages = [
                {"role":"system","content":system_prompt},
                {"role":"user","content":prompt}
            ]
            response = self.client.chat.completions.create(
                model = self.model,
                messages = messages,
                stream = False,
            )
            print("="*30)
            print(f"LLM的response：{response}")
            print("="*30)
            answer = response.choices[0].message.content
            print("LLM响应成功！")
            return answer
        except Exception as e:
            print(f"调用LLM时发生错误：{e}")
            return "调用语言模型时出错！"

# 配置区（确保密钥有效）
API_KEY = "sk-LA87J2CGrryR9tN6iO6Bdo4XYy5sDKo8FVxGx10Y4G9kWP1m"
BASE_URL = "https://api.moonshot.cn/v1"
MODEL_ID = "kimi-k2-turbo-preview"
TAVILY_API_KEY = "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"

llm = OpenAICompatibleClient(
    model = MODEL_ID,
    api_key = API_KEY,
    base_url = BASE_URL,
)

user_prompt = "帮我查询一下今天成都的天气，然后根据天气推荐一个合适的旅游景点"

# 加入用户的偏好“记忆功能”
# user_prefer = "用户更加倾向于历史底蕴丰厚的景点，同时用户倾向于更加经济的方案" # 直接加入用户偏好，放入历史对话中

prompt_history = [f"用户请求：{user_prompt}"]
# prompt_history.append(user_prefer)

print(f"用户输入：{user_prompt}\n"+"~"*30)

# 主循环
for i in range(5):
    print(f"--循环{i+1}--\n")

    full_prompt = "\n".join(prompt_history)
    llm_output = llm.generate(full_prompt,system_prompt=agent_prompt)
    print(f"模型输出：\n{llm_output}")
    prompt_history.append(llm_output)

    # 关键修复：优化Action解析正则
    # 支持：Action:xxx、Action：xxx、Action: xxx、Action： xxx（中英文冒号+有无空格）
    action_match = re.search(r"Action[:：]\s*(.*)", llm_output, re.DOTALL)
    if not action_match:
        print("解析错误:模型输出中未找到 Action。")
        # 打印调试信息，帮助定位问题
        print(f"调试：模型输出原始内容：{repr(llm_output)}")
        break
    action_str = action_match.group(1).strip()
    print(f"解析到的Action：{action_str}")  # 调试用，可查看解析结果

    if action_str.startswith("finish"):
        # 支持单引号、双引号，且兼容空格（如finish(answer = "xxx")）
        finish_match = re.search(r'finish\(answer\s*=\s*([\'"])(.*?)\1\)', action_str)
        if finish_match:
            final_answer = finish_match.group(2)
            print(f"任务完成，最终答案: {final_answer}")
        else:
            final_answer = "未获取到有效回答"
            print(f"任务完成，最终答案: {final_answer}")
        break

    # 解析工具名和参数（兼容参数中的空格，如city = "成都"）
    tool_name_match = re.search(r"^(\w+)\(", action_str)
    args_match = re.search(r"\((.*?)\)", action_str)
    if not tool_name_match or not args_match:
        print("解析错误:工具调用格式不正确。")
        print(f"调试：Action字符串格式：{action_str}")
        break
    tool_name = tool_name_match.group(1)
    args_str = args_match.group(1).strip()
    print(f"解析到的工具名：{tool_name}，参数串：{args_str}")  # 调试用

    # 解析参数（兼容key = "value" 或 key="value" 格式）
    kwargs = {}
    arg_pattern = re.compile(r'(\w+)\s*=\s*([\'"])(.*?)\2')
    arg_matches = arg_pattern.findall(args_str)
    for key, quote, value in arg_matches:
        kwargs[key] = value
    print(f"解析到的参数：{kwargs}")  # 调试用

    # 调用工具
    if tool_name in tools_dict:
        try:
            observation = tools_dict[tool_name](**kwargs)
        except Exception as e:
            observation = f"工具调用错误：{str(e)}"
    else:
        observation = f"错误:未定义的工具 '{tool_name}'"
    
    # 记录观察结果
    observation_str = f"Observation: {observation}"
    print(f"{observation_str}\n" + "="*40)
    prompt_history.append(observation_str)