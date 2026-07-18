# AI 办公自动化 Agent

企业级 AI 办公助手，支持 Function Calling 工具链调用。

## 功能

- **周报生成**：输入工作内容，自动生成格式化周报
- **会议纪要整理**：杂乱笔记 → 结构化纪要 + 待办事项
- **Excel 数据处理**：统计、筛选、排序
- **通知发送**：模拟企业内部通知
- **知识库搜索**：企业内部知识检索

## 技术栈

- FastAPI + WebSocket（实时对话）
- DeepSeek API + Function Calling（工具调用）
- SQLAlchemy + SQLite（用户系统）
- JWT 认证
- Jinja2 模板

## 核心亮点

不是简单的"调 API 返回文本"。AI 能自主判断用户意图，选择调用对应工具，整合结果返回。工具失败时有回退逻辑。

## 运行

```bash
pip install -r requirements.txt
# 创建 .env 文件，填入 DEEPSEEK_API_KEY
python -m uvicorn backend.main:app --host 127.0.0.1 --port 5000 --reload