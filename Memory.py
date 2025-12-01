from typing import List,Dict,Any,Optional

class Memory:
    """
    短期记忆模块，用于存储每次迭代的过程和结果
    """
    def __init__(self):
        """
        初始化一个空列表来存储记录
        """
        self.records:List[Dict[str,Any]] = []

    def add_record(self,record_type:str,content:str):
        """
        向记忆模块中添加一条记录
        参数：
        - record_type:记录的类型（execution/reflection）
        - content:记录的具体内容
        """
        record = {"type":record_type,"content":content}
        self.records.append(record)
        print(f"📝 记忆已更新，新增一条 '{record_type}' 记录。")

    def get_trajectory(self) -> str:
        """
        将所有记忆记录格式化为连贯的字符串文本，用于构建提示词
        """
        trajectory_parts = []
        for record in self.records:
            if record["type"] == "execution":
                trajectory_parts.append(f"---上一轮尝试---\n{record["content"]}")
            elif record["type"] == "reflection":
                trajectory_parts.append(f"---评审员反馈---\n{record["content"]}")
        return "\n\n".join(trajectory_parts)

    def get_last_execution(self) -> Optional[str]:
        """
        获取最近一次的执行结果
        若不存在，返回None
        """
        for record in reversed(self.records):
            if record["type"] == "execution":
                return record["content"]
        return None
