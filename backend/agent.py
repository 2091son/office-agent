import json
import httpx
from backend.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL
from backend.tools import TOOLS_SCHEMA, generate_weekly_report, summarize_meeting, process_excel, send_notification, search_knowledge, search_contacts, export_filtered_excel

SYSTEM_PROMPT = """You are an enterprise office automation AI assistant. Your job is to help employees efficiently complete office tasks.

You can use the following tools:
- generate_weekly_report: Generate formatted weekly reports
- summarize_meeting: Organize meeting notes into structured minutes
- process_excel: Process Excel data (sum, average, filter, sort, top, count). For uploaded .xlsx files, provide document_id and column name.
- export_filtered_excel: Filter an uploaded Excel and export matching rows as a new .xlsx file. MUST include the download link in your reply.
- send_notification: Send notifications via DingTalk or email
- search_knowledge: Search knowledge base (returns newest docs first with IDs). Use to find document IDs before processing Excel.
- search_contacts: Search company contacts by name

Rules:
1. When a user asks for an office task, determine which tools to call
2. If no tools are needed, respond directly
3. After calling tools, integrate results into a clear, professional reply
4. If multiple tasks are requested, complete them in sequence
5. Keep responses concise and direct. No bullet points or numbered lists unless asked.
6. For Excel questions: FIRST call search_knowledge to find the document ID, THEN call process_excel or export_filtered_excel with that ID."""


async def call_deepseek(messages: list):
    """Call DeepSeek API, return text reply"""
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
    """Call DeepSeek API with Function Calling support"""
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
    """Execute tool function by name"""
    tools_map = {
        "generate_weekly_report": generate_weekly_report,
        "summarize_meeting": summarize_meeting,
        "process_excel": process_excel,
        "send_notification": send_notification,
        "search_knowledge": search_knowledge,
        "search_contacts": search_contacts,
        "export_filtered_excel": export_filtered_excel,
    }

    func = tools_map.get(tool_name)
    if not func:
        return f"Unknown tool: {tool_name}"

    try:
        result = func(**arguments)
        import inspect
        if inspect.iscoroutine(result):
            result = await result
        return result
    except Exception as e:
        return f"Tool execution failed: {str(e)}"


async def run_agent(user_message: str, history: list = None):
    """Core Agent loop: determine if tools needed -> execute -> reply"""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if history:
        messages.extend(history)

    messages.append({"role": "user", "content": user_message})

    all_results = []

    for _ in range(5):
        response = await call_deepseek_with_tools(messages)
        choice = response["choices"][0]
        msg = choice["message"]

        if "tool_calls" in msg and msg["tool_calls"]:
            for tool_call in msg["tool_calls"]:
                tool_name = tool_call["function"]["name"]
                arguments = json.loads(tool_call["function"]["arguments"])
                tool_result = await execute_tool(tool_name, arguments)
                all_results.append(f"[{tool_name}] {tool_result}")

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

            messages.append({
                "role": "user",
                "content": "Tools executed. If task is complete, give final reply. If more tools needed, continue."
            })
            continue

        return msg.get("content", "Sorry, unable to process."), all_results

    final_response = await call_deepseek(messages)
    return final_response, all_results
