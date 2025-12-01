from typing import Dict,Any
from .SerpAPI import search
import os

class ToolExecutor:
    """
    工具执行器，负责管理和执行工具
    """
    def __init__(self):
        self.tools:Dict[str,Dict[str,any]] = {}

    def registerTool(self,name:str,description:str,func:callable):
        """
        向工具中注册一个新的工具
        """
        if name in self.tools:
            print(f"⚠警告：工具{name}已经存在，将被覆盖！")
        self.tools[name] = {"description":description,"func":func}
        print(f"工具：{name}已经注册")
    
    def getTool(self,name:str) -> callable:
        """
        根据名称获取工具的执行函数
        """
        return self.tools.get(name,{}).get("func") 
    
    def getAvailableTools(self) -> str:
        """
        获取所有可用工具的格式化描述字符串
        """
        return "\n".join([
            f"-{name}:{info["description"]}"
            for name,info in self.tools.items()
        ])

# ---工具初始化与使用示例
if __name__ == "__main__":
    # 初始化工具执行器
    toolExecutor = ToolExecutor()

    # 注册搜索工具
    search_description = "一个网页搜索引擎。当你需要回答实时性较强的问题以及在知识库中找不到信息时应该使用该工具"
    toolExecutor.registerTool("Search",search_description,search)

    # 打印可用的工具
    print("\n---可用的工具---")
    print(toolExecutor.getAvailableTools())

    print("\n---执行Action：Sreach['目前中日关系的最新动态']")
    tool_name = "Search"
    tool_input = "目前中日关系的最新动态"

    tool_function = toolExecutor.getTool(tool_name)
    if tool_function:
        observation = tool_function(tool_input)
        print("---观察(observation)")
        print(observation)
    else:
        print(f"错误，没找到名为{tool_name}的工具！")

