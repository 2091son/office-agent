import json
import httpx
from backend.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL
from backend.tools import TOOLS_SCHEMA, generate_weekly_report, summarize_meeting, process_excel, send_notification, search_knowledge

SYSTEM_PROMPT = """你是一个企业办公自动化 AI 助手。你的职责是帮助员工高效完成办公任务。

你可以使用以下工具：
- generate_weekly_report：生成周报
- summarize_meeting：整理会议纪要
- process_excel：处理 Excel 数据
- send_notification：发送通知
- search_knowledge：搜索内部知识库

规则：
1. 当用户提出办公任务时，判断需要调用哪些工具
2. 如果用户的问题不需要工具，直接回复
3. 调用工具后，将工具返回的结果整合成清晰、专业的回复
4. 如果用户同时提了多个任务，按顺序依次完成"""


async def call_deepseek(messages: list):
    """调用 DeepSeek API，返回文本回复"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{DEEPSEEK_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.7,
            }
        )
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def call_deepseek_with_tools(messages: list):
    """调用 DeepSeek API，支持 Function Calling，返回可能包含 tool_calls 的响应"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{DEEPSEEK_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": messages,
                "tools": TOOLS_SCHEMA,
                "temperature": 0.7,
            }
        )
        return resp.json()


async def execute_tool(tool_name: str, arguments: dict) -> str:
    """根据工具名称和参数执行对应的工具函数"""
    tools_map = {
        "generate_weekly_report": generate_weekly_report,
        "summarize_meeting": summarize_meeting,
        "process_excel": process_excel,
        "send_notification": send_notification,
        "search_knowledge": search_knowledge,
    }

    func = tools_map.get(tool_name)
    if not func:
        return f"未知工具：{tool_name}"

    try:
        result = func(**arguments)
        # 如果是异步函数，await 它
        import inspect
        if inspect.iscoroutine(result):
            result = await result
        return result
    except Exception as e:
        return f"工具执行失败：{str(e)}"


async def run_agent(user_message: str, history: list = None):
    """核心 Agent 流程：循环判断是否调工具 → 调工具 → 直到 AI 认为任务完成"""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if history:
        messages.extend(history)

    messages.append({"role": "user", "content": user_message})

    all_results = []

    # 最多循环 5 轮，防止真正的死循环
    for _ in range(5):
        response = await call_deepseek_with_tools(messages)
        choice = response["choices"][0]
        msg = choice["message"]

        # 如果 AI 想调工具
        if "tool_calls" in msg and msg["tool_calls"]:
            for tool_call in msg["tool_calls"]:
                tool_name = tool_call["function"]["name"]
                arguments = json.loads(tool_call["function"]["arguments"])
                tool_result = await execute_tool(tool_name, arguments)
                all_results.append(f"[{tool_name}] {tool_result}")

                # 把工具调用加入对话历史
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [tool_call]
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": tool_result
                })

            # 让 AI 看一下结果，决定是否继续
            messages.append({
                "role": "user",
                "content": "工具已执行完毕。请检查结果：如果任务已完成，请给用户最终回复。如果还需要调用其他工具，请继续。"
            })
            # 继续循环，不返回
            continue

        # AI 不调工具了，说明任务完成
        return msg.get("content", "抱歉，我无法处理这个请求。"), all_results

    # 超过 5 轮还没结束，强制返回
    final_response = await call_deepseek(messages)
    return final_response, all_results