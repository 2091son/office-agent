"""Office tools: functions + JSON Schema for Function Calling"""

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "generate_weekly_report",
            "description": "Generate a detailed weekly report. Take the user's brief work notes and expand them into a full professional report with: project name, specific tasks completed, key results, challenges encountered, and next week's plan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Work content for the week"},
                    "week_range": {"type": "string", "description": "e.g. 'July 14-July 18'"}
                },
                "required": ["content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_meeting",
            "description": "Organize meeting notes into structured minutes with action items",
            "parameters": {
                "type": "object",
                "properties": {
                    "notes": {"type": "string", "description": "Raw meeting notes"}
                },
                "required": ["notes"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "process_excel",
            "description": "Process Excel data: sum, average, filter, sort. Can work with uploaded files (by document_id) or raw comma-separated numbers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["sum", "average", "filter", "sort", "top", "count"], "description": "Operation: sum, average, filter, sort, top N, count"},
                    "data_description": {"type": "string", "description": "Brief description e.g. 'student scores'"},
                    "numbers": {"type": "string", "description": "Comma-separated numbers e.g. '100,200,300'. Use this OR document_id."},
                    "document_id": {"type": "integer", "description": "ID of uploaded Excel document. Use this OR numbers."},
                    "column": {"type": "string", "description": "Column name to operate on, e.g. '语文', '数学', '总分'"},
                    "filter_condition": {"type": "string", "description": "For filter/top: value like '>90', '<60', '技术部', or top N like '3'"},
                    "sheet_name": {"type": "string", "description": "Sheet name if multi-sheet file"}
                },
                "required": ["action", "data_description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_notification",
            "description": "Send notification via DingTalk or email to a person or department",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient": {"type": "string", "description": "Recipient name or email"},
                    "message": {"type": "string", "description": "Notification content"},
                    "priority": {"type": "string", "enum": ["normal", "urgent"], "description": "Priority level"},
                    "channel": {"type": "string", "enum": ["email", "dingtalk"], "description": "Send via email (for individuals in contacts) or DingTalk (for group notifications). If not specified, email is used for known contacts, dingtalk for unknown recipients."}
                },
                "required": ["recipient", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": "Search internal knowledge base for policies and procedures",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "export_filtered_excel",
            "description": "Filter rows from an uploaded Excel file and export matching rows to a new downloadable .xlsx file",
            "parameters": {
                "type": "object",
                "properties": {
                    "document_id": {"type": "integer", "description": "ID of source Excel document"},
                    "column": {"type": "string", "description": "Column name to filter on, e.g. '英语'"},
                    "condition": {"type": "string", "description": "Filter condition like '>=90', '>80', '<60'"},
                    "filename": {"type": "string", "description": "Output filename, e.g. '英语90分以上.xlsx'"}
                },
                "required": ["document_id", "column", "condition", "filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_contacts",
            "description": "Search the company contact list by name to find email and department",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name to search for"}
                },
                "required": ["name"]
            }
        }
    }
]


def generate_weekly_report(content: str, week_range: str = "This week") -> str:
    return f"""## Weekly Report ({week_range})

### Work Completed
{content}

### Next Week Plan
(Please add as needed)

---
*Generated by AI Office Agent*"""


def summarize_meeting(notes: str) -> str:
    return f"""## Meeting Minutes

### Raw Notes
{notes}

---
*Extract: attendees, topics, decisions, action items*"""


def process_excel(action: str, data_description: str, numbers: str = "",
                  document_id: int = None, column: str = None,
                  filter_condition: str = None, sheet_name: str = None) -> str:
    # --- Document-based mode ---
    if document_id:
        import sqlite3, os
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "office.db")
        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT title, content FROM documents WHERE id=?", (document_id,)).fetchone()
        conn.close()
        if not row:
            return f"Document #{document_id} not found."
        title, content = row

        # Parse the stored table format back into rows
        lines = content.split("\n")
        if not lines:
            return f"Document is empty."

        # Find the right sheet block
        sheet_start = 0
        if sheet_name:
            for i, ln in enumerate(lines):
                if ln.strip() == f"=== Sheet: {sheet_name} ===":
                    sheet_start = i + 1
                    break
        elif lines[0].startswith("=== Sheet:"):
            sheet_start = 1

        # Extract headers and data rows
        headers = []
        data_rows = []
        for i in range(sheet_start, len(lines)):
            ln = lines[i].strip()
            if ln.startswith("=== Sheet:") or not ln:
                break
            cells = [c.strip() for c in ln.split("|")]
            if not headers:
                headers = cells
            else:
                data_rows.append(cells)

        if not headers:
            return f"Cannot parse table headers from document."

        # Find column index
        col_idx = None
        if column:
            for i, h in enumerate(headers):
                if column in h:
                    col_idx = i
                    break
        # Default: use the last column (often 总分 or similar)
        if col_idx is None:
            col_idx = -1

        # Extract column values
        vals = []
        for dr in data_rows:
            if col_idx < len(dr) and dr[col_idx]:
                try:
                    vals.append(float(dr[col_idx]))
                except ValueError:
                    vals.append(dr[col_idx])

        if not vals:
            return f"No valid data found in column '{column or headers[col_idx]}'."

        # --- Filter action ---
        if action == "filter":
            cond = filter_condition or ""
            if cond.startswith(">="):
                threshold = float(cond[2:])
                filtered = [v for v in vals if isinstance(v, (int, float)) and v >= threshold]
                return f"Filter {data_description} ({column or ''} >= {threshold}): {len(filtered)} rows\nValues: {filtered}"
            elif cond.startswith("<="):
                threshold = float(cond[2:])
                filtered = [v for v in vals if isinstance(v, (int, float)) and v <= threshold]
                return f"Filter {data_description} ({column or ''} <= {threshold}): {len(filtered)} rows\nValues: {filtered}"
            elif cond.startswith(">"):
                threshold = float(cond[1:])
                filtered = [v for v in vals if isinstance(v, (int, float)) and v > threshold]
                return f"Filter {data_description} ({column or ''} > {threshold}): {len(filtered)} rows\nValues: {filtered}"
            elif cond.startswith("<"):
                threshold = float(cond[1:])
                filtered = [v for v in vals if isinstance(v, (int, float)) and v < threshold]
                return f"Filter {data_description} ({column or ''} < {threshold}): {len(filtered)} rows\nValues: {filtered}"
            else:
                # Text match
                filtered = [dr for dr in data_rows if any(cond in str(c) for c in dr)]
                result = f"Filter {data_description} matching '{cond}': {len(filtered)} rows\n"
                for dr in filtered:
                    result += " | ".join(str(c) for c in dr) + "\n"
                return result

        # --- Numeric operations ---
        num_vals = [v for v in vals if isinstance(v, (int, float))]
        if not num_vals:
            return f"No numeric values in column '{column or headers[col_idx]}'. Values: {vals}"

        if action == "sum":
            return f"Sum of {data_description} ({column or ''}): {sum(num_vals):.2f}"
        elif action == "average":
            return f"Average of {data_description} ({column or ''}): {sum(num_vals)/len(num_vals):.2f}"
        elif action == "sort":
            sorted_vals = sorted(num_vals, reverse=True)
            return f"Sorted {data_description} ({column or ''}, high to low): {sorted_vals}"
        elif action == "top":
            n = int(filter_condition or 3)
            sorted_vals = sorted(num_vals, reverse=True)
            return f"Top {n} {data_description} ({column or ''}): {sorted_vals[:n]}"
        elif action == "count":
            return f"Count of {data_description} ({column or ''}): {len(num_vals)}"
        else:
            return f"{action.capitalize()} on {data_description} ({column or ''}): {num_vals}"

    # --- Raw numbers mode (backward compatible) ---
    if not numbers:
        return f"Please provide numbers or a document_id for {action} on {data_description}."
    nums = [float(n.strip()) for n in numbers.split(",") if n.strip()]
    if not nums:
        return f"No valid numbers found."
    if action == "sum":
        return f"Sum of {data_description}: {sum(nums):.2f}"
    elif action == "average":
        return f"Average of {data_description}: {sum(nums)/len(nums):.2f}"
    elif action == "sort":
        return f"Sorted {data_description}: {sorted(nums, reverse=True)}"
    elif action == "top":
        n = int(filter_condition or 3)
        return f"Top {n} of {data_description}: {sorted(nums, reverse=True)[:n]}"
    elif action == "count":
        return f"Count of {data_description}: {len(nums)}"
    else:
        return f"{action.capitalize()} on {data_description}: {nums}"


async def send_notification(recipient: str, message: str, priority: str = "normal", channel: str = None) -> str:
    import os, smtplib, asyncio, httpx
    from email.mime.text import MIMEText

    # Step 0: If recipient looks like an email, send directly
    if "@" in recipient:
        contact_email = recipient
    else:
        contact_email = None

    if contact_email:
        try:
            smtp_host = os.getenv("SMTP_HOST", "smtp.qq.com")
            smtp_user = os.getenv("SMTP_USER", "")
            smtp_pass = os.getenv("SMTP_PASS", "")
            if not smtp_user or not smtp_pass:
                return f"SMTP not configured"

            msg = MIMEText(f"Hello,\n\n{message}\n\n---\nAI Office Agent\nTo: {recipient}\nPriority: {priority}", "plain", "utf-8")
            msg["From"] = smtp_user
            msg["To"] = contact_email
            msg["Subject"] = f"{'[URGENT] ' if priority == 'urgent' else ''}Notification: {recipient}"

            def _send():
                server = smtplib.SMTP_SSL(smtp_host, 465, timeout=10)
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
                server.quit()

            await asyncio.get_event_loop().run_in_executor(None, _send)
            return f"Email sent to {recipient}: {message}"
        except Exception as e:
            return f"Email failed: {str(e)}"

    # Step 1: Look up recipient in contacts
    try:
        from backend.database import SessionLocal
        db = SessionLocal()
        rows = db.execute("SELECT name, email FROM contacts WHERE name LIKE ?", (f"%{recipient}%",)).fetchall()
        db.close()
        for name, email in rows:
            if name in recipient or recipient in name:
                contact_email = email
                break
    except:
        pass

    # Step 2: If found in contacts, send email directly to them
    if contact_email:
        try:
            smtp_host = os.getenv("SMTP_HOST", "smtp.qq.com")
            smtp_user = os.getenv("SMTP_USER", "")
            smtp_pass = os.getenv("SMTP_PASS", "")
            if not smtp_user or not smtp_pass:
                return f"SMTP not configured"

            msg = MIMEText(f"Hello,\n\n{message}\n\n---\nAI Office Agent\nTo: {recipient}\nPriority: {priority}", "plain", "utf-8")
            msg["From"] = smtp_user
            msg["To"] = contact_email
            msg["Subject"] = f"{'[URGENT] ' if priority == 'urgent' else ''}Notification: {recipient}"

            def _send():
                server = smtplib.SMTP_SSL(smtp_host, 465, timeout=10)
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
                server.quit()

            await asyncio.get_event_loop().run_in_executor(None, _send)
            return f"Email sent to {recipient} ({contact_email}): {message}"
        except Exception as e:
            return f"Email failed: {str(e)}"

    # Step 3: Not in contacts — suggest alternatives
    if channel == "dingtalk":
        try:
            dingtalk_url = os.getenv("DINGTALK_WEBHOOK", "")
            if dingtalk_url:
                async with httpx.AsyncClient() as client:
                    r = await client.post(dingtalk_url, json={
                        "msgtype": "text",
                        "text": {"content": f"通知：{recipient}\n{message}"}
                    })
                if r.status_code == 200:
                    return f"钉钉通知已发送至 {recipient}：{message}"
                return f"钉钉发送失败：{r.text}"
            return "钉钉 Webhook 未配置"
        except Exception as e:
            return f"钉钉发送失败：{str(e)}"
    return f"未找到联系人 '{recipient}'。如需发钉钉群通知，请说明'发钉钉'。"



def search_knowledge(query: str) -> str:
    """Search knowledge base - try exact, then fuzzy"""
    import sqlite3, os
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "office.db")
    conn = sqlite3.connect(db_path)

    # Try exact match first
    rows = conn.execute(
        "SELECT id, title, content FROM documents WHERE content LIKE ? OR title LIKE ? ORDER BY id DESC LIMIT 5",
        (f"%{query}%", f"%{query}%")
    ).fetchall()

    # If no exact match, try each character
    if not rows and len(query) > 1:
        for ch in query:
            if len(ch.strip()) < 1: continue
            rows = conn.execute(
                "SELECT id, title, content FROM documents WHERE content LIKE ? OR title LIKE ? ORDER BY id DESC LIMIT 5",
                (f"%{ch}%", f"%{ch}%")
            ).fetchall()
            if rows: break

    conn.close()

    if rows:
        result = "知识库查询结果：\n"
        for doc_id, title, content in rows:
            result += f"\n--- [{doc_id}] {title} ---\n{content[:500]}\n"
        return result

    return f"未找到与'{query}'相关的内容。请上传相关文档后重试。"

def search_contacts(name: str) -> str:
    try:
        import sqlite3, os
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "office.db")
        conn = sqlite3.connect(db_path)
        rows = conn.execute("SELECT name, email, department FROM contacts WHERE name LIKE ?", (f"%{name}%",)).fetchall()
        conn.close()
        if not rows:
            return f"No contacts found for '{name}'."
        result = "Contacts found:\n"
        for r in rows:
            result += f"- {r[0]} | {r[1]} | {r[2]}\n"
        return result
    except Exception as e:
        return f"Search failed: {str(e)}"


def export_filtered_excel(document_id: int, column: str, condition: str, filename: str) -> str:
    """Filter rows from an uploaded Excel and export matching rows to a new .xlsx"""
    import sqlite3, os
    from openpyxl import Workbook

    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "office.db")
    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT title, content FROM documents WHERE id=?", (document_id,)).fetchone()
    conn.close()
    if not row:
        return f"Document #{document_id} not found."
    title, content = row

    lines = content.split("\n")
    sheet_start = 1 if lines[0].startswith("=== Sheet:") else 0

    headers = []
    data_rows = []
    for i in range(sheet_start, len(lines)):
        ln = lines[i].strip()
        if ln.startswith("=== Sheet:") or not ln:
            break
        cells = [c.strip() for c in ln.split("|")]
        if not headers:
            headers = cells
        else:
            data_rows.append(cells)

    if not headers:
        return "Cannot parse table headers."

    col_idx = None
    for i, h in enumerate(headers):
        if column in h:
            col_idx = i
            break
    if col_idx is None:
        return f"Column '{column}' not found in headers: {headers}"

    op = ">="
    val_str = condition
    for o in [">=", "<=", ">", "<", "="]:
        if condition.startswith(o):
            op = o
            val_str = condition[len(o):]
            break

    matched = []
    for dr in data_rows:
        if col_idx < len(dr) and dr[col_idx]:
            try:
                cell_val = float(dr[col_idx])
                threshold = float(val_str)
                if op == ">=" and cell_val >= threshold: matched.append(dr)
                elif op == "<=" and cell_val <= threshold: matched.append(dr)
                elif op == ">" and cell_val > threshold: matched.append(dr)
                elif op == "<" and cell_val < threshold: matched.append(dr)
                elif op == "=" and cell_val == threshold: matched.append(dr)
            except ValueError:
                continue

    if not matched:
        return f"No rows match {column} {condition}."

    wb = Workbook()
    ws = wb.active
    ws.title = "筛选结果"
    ws.append(headers)
    for dr in matched:
        ws.append(dr)

    exports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "exports")
    os.makedirs(exports_dir, exist_ok=True)
    import time
    safe_name = f"export_{int(time.time())}.xlsx"
    filepath = os.path.join(exports_dir, safe_name)
    wb.save(filepath)

    return f"已生成筛选结果文件（{len(matched)} 条记录，条件: {column} {condition}）。下载链接: /api/download/{safe_name}"
