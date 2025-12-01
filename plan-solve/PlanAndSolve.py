from dotenv import load_dotenv
import sys
from pathlib import Path
import ast
# 获取根目录（plan-solve文件夹的上级目录）
root_dir = Path(__file__).parent.parent  # __file__是当前文件路径，parent取上级目录
sys.path.append(str(root_dir))  # 把根目录加入Python搜索路径
from KIMI import HelloAgentsLLM


load_dotenv()

# 这个提示词包含角色设定，任务描述以及输出格式示例
PLANNER_PROMPT_TEMPLATE = """
你是一个十分擅长问题拆解与规划的专家。你的任务是将用户的复杂问题分解为一个由多个简单步骤组成的行动计划。
请确保计划中每一个步骤都是独立、可执行的，并且严格按照逻辑顺序排列。同时请你只给出计划而不要实际解决这个问题。

问题：{question}
请严格按照以下的格式输出你的计划```python与```作为前后缀是必要的:
```python
["步骤1", "步骤2", "步骤3", ...]
```
"""

class Planner:
    def __init__(self,llm_client):
        self.llm_client = llm_client

    def plan(self,question:str) -> list[str]:
        """
        根据用户的问题生成一个行动计划
        """
        prompt = PLANNER_PROMPT_TEMPLATE.format(question=question)

        messages = [{"role":"user","content":prompt}]

        print("---正在生成计划---")
        response_text = self.llm_client.think(messages=messages) or ""

        print(f"✅计划已生成：{response_text}")

        try:
            plan_str = response_text.split("```python")[1].split("```")[0].strip()
            # 安全执行字符串，转换为python列表
            plan = ast.literal_eval(plan_str)
            return plan if isinstance(plan,list) else []
        except (ValueError,SyntaxError,IndexError) as e:
            print(f"❌解析时出现错误：{e}")
            print(f"原始响应：{response_text}")
            return []
        except Exception as e:
            print(f"❌解析计划时发生位置错误：{e}")
            return []

EXECUTOR_PROMPT_TEMPLATE = """
你是一个严格按照规划执行任务的助手。你的任务时严格按照给定的计划一步步执行并解决问题。
你将收到原始问题，完整的计划。
要求：
- 如果不是最后一步：仅输出该步骤的计算结果或答案，不要任何解释、额外对话。
- 如果是最后一步：**必须结合原始问题和所有步骤的结果，使用自然语言给出完整的总结性回答**

原始问题：{question}
完整计划：{plan}
历史对话记录：{history}
当前步骤：{current_step}
当前步骤序号：{step_index}/{total_steps}（{is_last_step}）
"""

class Executor:
    def __init__(self,llm_client):
        self.llm_client = llm_client

    def execute(self, question: str, plan: list[str]) -> str:
        history = ""
        print("\n---正在执行计划---")

        total_steps = len(plan)  # 总步骤数
        final_answer = ""  # 单独存储最后一步的总结

        for i, step in enumerate(plan):
            step_index = i + 1
            is_last_step = "最后一步" if step_index == total_steps else "非最后一步"
            
            print(f"\n->正在执行步骤{step_index}/{total_steps}:{step}")

            prompt = EXECUTOR_PROMPT_TEMPLATE.format(
                question=question,
                plan=plan,
                history=history if history else "无",
                current_step=step,
                step_index=step_index,
                total_steps=total_steps,
                is_last_step=is_last_step  # 传递是否为最后一步
            )

            messages = [{"role": "user", "content": prompt}]
            response_text = self.llm_client.think(messages=messages) or ""

            history += f"步骤{step_index}：{step}\n结果：{response_text}\n\n"
            print(f"✅步骤{step_index}已完成，结果：{response_text}")

            # 最后一步的响应作为最终总结
            if step_index == total_steps:
                final_answer = response_text

        return final_answer

class PlanAndSloveAgent:
    # 初始化Agent，创建计划器和执行器
    def __init__(self,llm_client):
        self.llm_client = llm_client
        self.planner = Planner(self.llm_client)
        self.executor = Executor(self.llm_client)

    def run(self,question:str):
        """
        运行Agent完整流程
        """
        print(f"\n---开始处理问题---\n:{question}")

        plan = self.planner.plan(question)

        if not plan:
            print("\n❌---任务终止---\n无法生成有效行动计划")
            return None
        
        final_answer = self.executor.execute(question,plan)

        print(f"\n✅---任务完成---\n最终答案为：{final_answer}")

if __name__ == "__main__":
    llm_client = HelloAgentsLLM()

    query = "一个水果店周一卖出了15个苹果。周二卖出的数量是周一的两倍。周三卖出的数量比周二少5个。请问这三天总共卖出了多少个苹果？"

    agent = PlanAndSloveAgent(llm_client)

    agent.run(query)