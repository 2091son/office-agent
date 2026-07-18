"""办公工具集：每个工具函数 + Function Calling 所需的 JSON Schema"""

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "generate_weekly_report",
            "description": "根据用户描述的内容，生成一份格式化的周报",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "本周的工作内容，可以是零散的描述"
                    },
                    "week_range": {
                        "type": "string",
                        "description": "例如'7月14日-7月18日'"
                    }
                },
                "required": ["content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_meeting",
            "description": "将会议笔记整理成结构化的会议纪要，提取议题、决议、待办事项",
            "parameters": {
                "type": "object",
                "properties": {
                    "notes": {
                        "type": "string",
                        "description": "原始的会议笔记或录音文字"
                    }
                },
                "required": ["notes"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "process_excel",
            "description": "对 Excel 数据执行操作：统计、筛选、排序等",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "要执行的操作，例如：统计总数、按某列排序、筛选大于某值的行",
                        "enum": ["统计总数", "计算平均值", "筛选数据", "排序"]
                    },
                    "data_description": {
                        "type": "string",
                        "description": "对数据的描述，例如'销售数据，列有：月份、销售额、利润'"
                    },
                    "numbers": {
                        "type": "string",
                        "description": "实际数据，例如'100,200,300,400,500'"
                    }
                },
                "required": ["action", "data_description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_notification",
            "description": "向指定人员发送通知或提醒",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient": {
                        "type": "string",
                        "description": "接收人姓名或部门"
                    },
                    "message": {
                        "type": "string",
                        "description": "通知内容"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["普通", "紧急"],
                        "description": "优先级"
                    }
                },
                "required": ["recipient", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": "搜索企业内部知识库或数据",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "要搜索的关键词或问题"
                    }
                },
                "required": ["query"]
            }
        }
    }
]


def generate_weekly_report(content: str, week_range: str = "本周") -> str:
    """生成格式化周报"""
    return f"""## 周报（{week_range}）

### 本周工作内容
{content}

### 下周计划
（请根据实际情况补充）

---
*由 AI 办公助手自动生成*"""


def summarize_meeting(notes: str) -> str:
    """整理会议纪要（核心逻辑由 AI prompt 处理，这里做格式化包装）"""
    return f"""## 📋 会议纪要

### 原始笔记
{notes}

---
*请 AI 提取以下信息：参会人、议题、决议、待办事项*"""


def process_excel(action: str, data_description: str, numbers: str = "") -> str:
    """处理 Excel 数据"""
    if not numbers:
        return f"操作：{action}\n数据描述：{data_description}\n结果：请提供具体数据以进行计算。"

    nums = [float(n.strip()) for n in numbers.split(",") if n.strip()]
    if not nums:
        return f"操作：{action}\n数据描述：{data_description}\n结果：未能解析到有效数字。"

    if action == "统计总数":
        total = sum(nums)
        return f"操作：统计总数\n数据描述：{data_description}\n结果：总计 = {total}"
    elif action == "计算平均值":
        avg = sum(nums) / len(nums)
        return f"操作：计算平均值\n数据描述：{data_description}\n结果：平均值 = {avg:.2f}"
    else:
        sorted_nums = sorted(nums)
        return f"操作：{action}\n数据描述：{data_description}\n结果：处理后的数据 = {sorted_nums}"


def send_notification(recipient: str, message: str, priority: str = "普通") -> str:
    """发送通知（模拟，实际项目中接邮件 API）"""
    priority_emoji = "🔴" if priority == "紧急" else "🟢"
    return f"{priority_emoji} 已向 **{recipient}** 发送通知：\n\n> {message}\n\n（模拟发送，实际部署时接入邮件服务）"


def search_knowledge(query: str) -> str:
    """模拟企业知识库搜索"""
    knowledge_base = {
        "请假": "公司请假流程：1. OA系统提交申请 → 2. 直属领导审批 → 3. 3天以上需人事备案。年假15天，病假需附医院证明。",
        "报销": "报销流程：贴发票 → OA填写报销单 → 部门审批 → 财务审核 → 打款（5个工作日内）。单笔超5000需副总审批。",
        "周报": "周报提交截止时间：每周五17:00前。模板请参考OA系统-文档中心-周报模板。",
        "加班": "加班需提前在OA申请，经审批后方可执行。加班费按国家规定：工作日1.5倍，休息日2倍，节假日3倍。",
    }
    for key, answer in knowledge_base.items():
        if key in query:
            return f"📚 知识库查询结果：\n\n{answer}"
    return f"📚 知识库中未找到与「{query}」相关的结果。请联系管理员补充。"