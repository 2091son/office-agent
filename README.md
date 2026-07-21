# AI 办公自动化 Agent

基于 Function Calling 的企业级 AI 办公助手，AI 能自主判断用户意图，调用对应工具完成任务。

## 核心亮点

不是简单的"调 API 返回文本"。用户输入一句话，AI 能自主判断该调哪个工具、按什么顺序调、拿到结果后整合回复。工具执行失败时有回退逻辑。

## 功能演示

> 用户：帮我写一份周报，这周做了需求评审和代码开发，然后发给技术部

AI 自动拆成两步：
1. 调用 `generate_weekly_report` 生成格式化周报
2. 调用 `send_notification` 发送邮件通知

全程不需要用户分步下命令。

## 五个办公工具

| 工具 | 功能 |
|---|---|
| 周报生成 | 输入工作内容，自动生成格式化周报 |
| 会议纪要 | 杂乱笔记转结构化纪要，自动提取待办事项 |
| Excel 处理 | 统计、筛选、排序 |
| 邮件通知 | SMTP 真实发送 |
| 知识库搜索 | 企业内部知识检索 |

## 技术栈

- **FastAPI** + WebSocket — 后端 + 实时对话
- **DeepSeek API** + Function Calling — AI 工具调用
- **SQLAlchemy** + SQLite — ORM + 数据库
- **JWT 认证** — 无状态登录
- **管理员面板** — 操作审计日志

## 项目结构

```
office-agent/
├── backend/
│   ├── main.py          # FastAPI 入口 + 路由
│   ├── agent.py         # Agent 核心逻辑（Function Calling）
│   ├── tools.py         # 工具定义 + JSON Schema
│   ├── auth.py          # JWT 认证 + 权限控制
│   ├── database.py      # 数据库连接
│   ├── models.py        # 数据模型（User, OperationLog）
│   └── config.py        # 配置管理
├── templates/           # 前端页面
├── static/              # CSS
└── .env                 # 环境变量（需自行创建）
```

## 运行

```bash
pip install -r requirements.txt

# 创建 .env 文件
DEEPSEEK_API_KEY=你的Key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
SMTP_HOST=smtp.qq.com
SMTP_USER=你的QQ@qq.com
SMTP_PASS=你的授权码
SECRET_KEY=随便一串乱码

# 启动
python -m uvicorn backend.main:app --host 127.0.0.1 --port 5000 --reload
```

默认管理员：admin / 123456

## 面试可以讲

1. **Function Calling 原理**：AI 不是黑盒——我定义了工具的 JSON Schema，AI 根据用户意图返回 tool_calls，我的代码执行对应函数，结果还给 AI 生成回复。多步工具链用 while 循环实现，每轮 AI 能看到之前执行了什么，自主决定是否继续。

2. **JWT vs Session**：第一个项目用 Flask session，这个项目升级到 JWT。session 存服务端，JWT 是无状态认证——服务器不存用户状态，适合水平扩展。

3. **为什么升级到 SQLAlchemy ORM**：工具链复杂之后，ORM 的事务管理和模型关联比裸 SQL 清晰得多。operation_logs 表记录所有用户操作——这是企业项目的基本要求。

4. **WebSocket 和 HTTP 的区别**：聊天场景需要持续双向通信，HTTP 每次重新建立连接效率太低。WebSocket 一次连接持续保持，消息实时推送。

## 页面展示
![聊天](static/screenshot1.png)
![管理面板](static/screenshot2.png)