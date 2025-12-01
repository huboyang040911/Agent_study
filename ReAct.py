import sys
import os
from KIMI import HelloAgentsLLM
# sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from Tools.ToolExecutor import ToolExecutor
import re
from Tools.SerpAPI import search

# REACT_PROMPT_TEMPLATE = """
# 你是一个擅长使用外部工具的智能助手。

# 可用工具如下：
# {tools}

# 请务必按照以下格式进行思考并进行回答：
# Thought:这里是你的思考过程，请把思考过程放在这里显示出来，用于分析问题、拆解任务和规划下一步行动
# Action: 你决定采取的行动，必须是以下格式之一：
# # 调用一个工具，格式{{tool_name}}[{{tool_input}}]
# # 当你收集到足够的信息，能够回答用户的问题时，finish(answer="...") 来输出最终答案

# 在你调用工具之前应该总结已有信息

# 请开始解决以下问题：
# Question: {question}
# History: {history}
# """

REACT_PROMPT_TEMPLATE = """
请注意，你是一个有能力调用外部工具的智能助手。

可用工具如下：
{tools}

请严格按照以下格式进行回应：

Thought: 你的思考过程，用于分析问题、拆解任务和规划下一步行动。
Action: 你决定采取的行动，必须是以下格式之一：
- `{{tool_name}}[{{tool_input}}]`：调用一个可用工具。
- `Finish[最终答案]`：当你认为已经获得最终答案时。
- 当你收集到足够的信息，能够回答用户的最终问题时，你必须在`Action:`字段后使用 `finish(answer="...")` 来输出最终答案。


现在，请开始解决以下问题：
Question: {question}
History: {history}
"""

class ReActAgent:
    def __init__(self,llm_client:HelloAgentsLLM,tool_executor:ToolExecutor,max_steps:int=5):
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.max_steps = max_steps
        self.history = []

    # 输出解析器，提取Thought和Action部分
    def _parse_output(self, text: str):
        thought_match = re.search(r"Thought: (.*)", text)
        action_match = re.search(r"Action: (.*)", text)
        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None
        return thought, action


    def _parse_action(self, action_text: str):
        """解析Action字符串，提取工具名称和输入。"""
        match = re.match(r"(\w+)\[(.*)\]", action_text)
        if match:
            return match.group(1), match.group(2)
        return None, None

    def _parse_action_input(self, action_text: str):
        match = re.match(r"\w+\[(.*)\]", action_text)
        return match.group(1) if match else ""
    
    def run(self,question:str):
        """
        运行一个Agent来回答问题
        首先检查是否为 Finish 指令,如果是则结束流程
        否则通过tool_executor 获取对应的工具函数并执行
        """
        self.history = []
        current_step = 0

        while current_step < self.max_steps:
            current_step += 1
            print(f"--第{current_step}步--")

            # 格式化提示词
            tools_desc = self.tool_executor.getAvailableTools()
            history_str = "\n".join(self.history)
            prompt = REACT_PROMPT_TEMPLATE.format(
                tools = tools_desc,
                question = question,
                history = history_str
            )

            messages = [{"role":"user","content":prompt}]
            response_text = self.llm_client.think(messages=messages)

            if not response_text:
                print("❌错误：LLM没返回有效响应！")
                break

            # 解析LLM输出
            thought, action= self._parse_output(response_text)

            if thought:
                print(f"🤔思考内容：{thought}")
                print(f"执行内容：{action}")
            
            if not action:
                print("⚠警告：未能解析有效的Action，流程终止！")
                break

            if action.startswith("Finish"):
                final_answer = self._parse_action_input(action)
                print(f"🎉 最终答案: {final_answer}")
                return final_answer

            tool_name,tool_input = self._parse_action(action)
            if not tool_name or not tool_input:
                continue
            
            print(f"🎬执行：{tool_name}[{tool_input}]")
            tool_function = self.tool_executor.getTool(tool_name)
            if not tool_function:
                observation = f"错误：未找到名为{tool_name}的工具！"
            else:
                observation = tool_function(tool_input)

            print(f"👀 观察: {observation}")
            print("+"*30)
            print(f"observation的内容是：{observation}")
            print("+"*30)

            # 将当前轮次的结果加入到历史记录中
            self.history.append(f"Action:{action}")
            self.history.append(f"Observation:{observation}")

        print("达到最大循环次数，流程终止！")
        return None

if __name__ == "__main__":
    tool_executor = ToolExecutor()              # ✅ 实例
    llm = HelloAgentsLLM()                      # ✅ 实例（假设无参）

    # 注册工具（⚠️你现在 main 里根本没注册工具）
    search_description = "一个网页搜索引擎，当需要实时信息时使用"
    tool_executor.registerTool(
        "Search",
        search_description,
        search
    )

    reactagent = ReActAgent(
        llm_client=llm,
        tool_executor=tool_executor,
        max_steps=5
    )

    query = "华为最新的手机是哪一款？它的主要卖点是什么？"
    reactagent.run(query)
    