from Memory import Memory
from KIMI import HelloAgentsLLM
from dotenv import load_dotenv

load_dotenv()

INITIAL_PROMPT_TEMPLATE = """
你是以为资深的python程序员。请根据以下要求，编写一个python函数。
你的代码必须包含完整的函数签名，文档字符串并遵循PEP 8编码规范。

要求：{task}

请直接输出代码，不要包含任何额外的解释等内容。
"""

REFIECTION_PROMPT_TEMPLATE = """
你是以为资深的代码审评专家，对代码的性能有极致的要求。
你的任务是审查以下python代码，并专注于找出其在算法效率上的主要瓶颈。

任务：{task}
待审查的代码：
```python
{code}
```

请分析代码的时间复杂度，思考是否存在一种在算法上更优的解决办法。
若存在，请清晰指出当前算法的不足并提出具体且可行的改进建议。
如果代码在算法层面已经达到最优，才能回答“无需改进”

请直接输出你的反馈，不要输出额外内容。
"""

REFINE_PROMPT_TEMPLATE = """
你是一位资深的python算法与程序优化专家，请根据以为代码审评专家的反馈来优化代码。

原始任务：{task}
上一轮尝试的代码：{last_code_attempt}
评审专家的反馈：{feedback}

请根据评审专家的反馈，生成一个优化后的新版代码。
你的代码必须包含完整的函数签名，文档字符串并遵循PEP 8编码规范。
请直接输出你优化后的代码，不要输出额外内容。
"""

class ReflectionAgent:
    def __init__(self,llm_client,max_iterations=5):
        self.llm_client = llm_client
        self.memory = Memory()
        self.max_iterations = max_iterations
    
    def run(self,task:str):
        print("\n---正在进行初始尝试---")
        
        # 1.初始执行
        initial_prompt = INITIAL_PROMPT_TEMPLATE.format(task=task)
        initial_code = self._get_llm_response(initial_prompt)
        self.memory.add_record("execution",initial_code)

        # 2.迭代循环：反思与优化
        for i in range(self.max_iterations):
            print(f"\n---第{i+1}/{self.max_iterations}轮迭代---")

            print("\n->正在进行反思...")
            last_code = self.memory.get_last_execution()
            reflect_prompt = REFIECTION_PROMPT_TEMPLATE.format(task=task,code=last_code)
            feedback = self._get_llm_response(reflect_prompt)
            self.memory.add_record("reflection",feedback)

            if "无需改进" in feedback:
                print("\n✅ 反思认为代码已无需改进，任务完成。")
                break

            print("\n->正在进行优化...")
            refine_prompt = REFINE_PROMPT_TEMPLATE.format(
                task = task,
                last_code_attempt = last_code,
                feedback = feedback,
            )
            refined_code = self._get_llm_response(refine_prompt)
            self.memory.add_record("execution",refined_code)
        
        final_code = self.memory.get_last_execution()
        print(f"\n---任务完成---\n最终生成的代码：\n```python\n{final_code}\n```")
        return final_code

    def _get_llm_response(self,prompt:str) -> str:
        """
        一个辅助方法，调用LLM并获取完整的流式响应
        """
        messages = [{"role":"user","content":prompt}]
        response_text = self.llm_client.think(messages=messages) or ""
        return response_text

if __name__ == "__main__":
    llm_client = HelloAgentsLLM()

    query = "编写一个Python函数，找出1到n之间所有的素数 (prime numbers)。"

    agent = ReflectionAgent(llm_client=llm_client)

    agent.run(query)

