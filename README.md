# AI 办公助手 (Office Agent)

一个基于 DeepSeek Function Calling 的智能办公助手，支持周报生成、会议纪要、Excel 处理、邮件/钉钉通知、知识库检索等功能。

## 功能

### AI 对话
- 多轮对话，支持对话历史
- 自动判断是否需要调用工具
- 最多 5 轮工具链（先搜通讯录 → 再发通知）

### 办公工具
| 工具 | 说明 |
|---|---|
| 周报生成 | 输入工作内容，自动生成格式化周报 |
| 会议纪要 | 整理会议笔记，生成结构化纪要 |
| Excel 处理 | 上传 .xlsx，按列求和、平均、排序、筛选、导出 |
| 发送通知 | QQ 邮件 + 钉钉 Webhook 双通道 |
| 搜索知识库 | 上传文档后检索，支持 .txt/.pdf/.docx/.xlsx |
| 通讯录 | 按姓名搜索联系人，关联邮箱发送 |

### 管理面板
- 用户管理（注册/删除/升级管理员）
- 通讯录管理
- 操作日志 + 工具使用统计图表（ECharts）
- 邮件提醒（定时任务）

### 聊天增强
- 📎 文件上传（解析后直接可问 AI）
- 🎤 语音输入（Web Speech API）
- 对话导出
- 多用户隔离（每人只看自己的对话）

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | FastAPI + WebSocket + SQLAlchemy + SQLite |
| AI | DeepSeek API (chat/completions + Function Calling) |
| 前端 | 原生 HTML/CSS/JS + Jinja2 模板 |
| 图表 | ECharts |
| 文件解析 | openpyxl (Excel), python-docx (Word), pypdf (PDF) |
| 通知 | smtplib (QQ 邮箱), httpx (钉钉 Webhook) |
| 定时 | APScheduler |

## 项目结构

```
office-agent/
├── backend/
│   ├── main.py          # FastAPI 应用 + 所有路由 + WebSocket
│   ├── agent.py         # Agent 循环 + DeepSeek 调用 + 工具调度
│   ├── tools.py         # 工具函数 + Function Calling Schema
│   ├── models.py        # SQLAlchemy 数据模型
│   ├── auth.py          # JWT 认证 + 密码哈希
│   ├── config.py        # 环境变量读取
│   └── database.py      # 数据库连接
├── templates/           # Jinja2 页面模板
│   ├── chat.html        # 聊天主界面
│   ├── admin.html       # 管理面板
│   └── login.html       # 登录/注册
├── static/
│   ├── style.css        # 全局样式
│   └── exports/         # 导出的 Excel 文件
├── .env                 # API Key 等配置
└── office.db            # SQLite 数据库
```

## 快速开始

### 1. 安装依赖

```bash
pip install fastapi uvicorn httpx sqlalchemy pyjwt passlib python-docx pypdf openpyxl apscheduler jinja2 python-multipart
```

### 2. 配置 `.env`

```env
DEEPSEEK_API_KEY=sk-your-key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
SECRET_KEY=your-secret-key
SMTP_HOST=smtp.qq.com
SMTP_USER=your@qq.com
SMTP_PASS=your-smtp-auth-code
DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxx
```

### 3. 初始化数据库

```bash
python backend/_init_db.py
```

### 4. 启动

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 5000 --reload
```

打开 http://127.0.0.1:5000，注册账号即可使用。

### 5. 设置管理员

注册第一个账号后，在终端执行：

```bash
python -c "import sqlite3; conn=sqlite3.connect('office.db'); conn.execute(\"UPDATE users SET role='admin' WHERE id=1\"); conn.commit(); conn.close()"
```

## 钉钉机器人配置

1. 创建钉钉群 → 群设置 → 智能群助手 → 添加机器人
2. 安全设置选择"自定义关键词"，填 `通知`
3. 复制 Webhook URL 填入 `.env` 的 `DINGTALK_WEBHOOK`

## QQ 邮箱 SMTP

1. QQ 邮箱 → 设置 → 账户 → POP3/SMTP 服务 → 开启
2. 获取授权码填入 `.env` 的 `SMTP_PASS`
