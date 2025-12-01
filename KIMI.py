import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List,Dict

# 加载环境变量
load_dotenv()

# 封装一个模型类
class HelloAgentsLLM:
    """
    LLM客户端，调用兼容OpenAI接口的服务
    这里使用的是KIMI大模型
    """
    def __init__(self,model:str=None,apiKey:str=None,baseUrl:str=None,timeout:int=None):
        """
        初始化客户端
        """
        self.model = model or os.getenv("LLM_MODEL_ID")
        apiKey = apiKey or os.getenv("LLM_API_KEY")
        baseUrl = baseUrl or os.getenv("LLM_BASE_URL")
        timeout = timeout or int(os.getenv("LLM_TIMEOUT",60))

        if not all([self.model,apiKey,baseUrl]):
            raise ValueError("模型ID，API密钥和访问地址必须在.env文件中定义")
        
        self.client = OpenAI(api_key=apiKey,base_url=baseUrl)

    def think(self,messages:List[Dict[str,str]],temperature:float=0) -> str:
        """
        调用大模型
        """
        print(f"🧠 正在调用{self.model}模型...")
        try:
            response = self.client.chat.completions.create(
                model = self.model,
                messages = messages,
                temperature = temperature,
                stream = True,
            )
            print("✅ 大语言模型响应成功:")
            collected_content = []
            for chunk in response:
                content = chunk.choices[0].delta.content or ""
                print(content,end="",flush=True)
                collected_content.append(content)
            print() # 流式输出后换行
            return "".join(collected_content)

        except Exception as e:
            print(f"❌ 调用LLM API时发生错误: {e}")
            return None

if __name__ == "__main__":
    try:
        llmClient = HelloAgentsLLM()

        messages = [
            {"role":"system","content":"你是我的私人助手"},
            {"role":"user","content":"编写一个比较大小的Python脚本"}
        ]

        print("---调用大模型---")

        response = llmClient.think(messages)
        if response:
            print("\n\n---完整的响应内容---")
            print(response)
    except Exception as e:
        print(f"出现错误：{e}!")
