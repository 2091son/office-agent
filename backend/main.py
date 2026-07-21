import traceback
from fastapi import FastAPI, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from backend.database import engine, get_db, Base, SessionLocal
from backend.models import User, OperationLog
from backend.auth import hash_password, create_token, get_current_user, require_admin
from backend.agent import run_agent
from backend import init_db
import json

init_db()

app = FastAPI(title="AI 办公助手")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(request=request, name="register.html")


@app.post("/api/register")
async def api_register(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        raise HTTPException(status_code=400, detail="用户名和密码不能为空")
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")

            # 第一个注册的用户自动成为管理员
        is_first = db.query(User).count() == 0
        user = User(
            username=username,
            password=hash_password(password),
            role="admin" if is_first else "employee"
        )
    db.add(user)
    db.commit()
    return {"message": "注册成功"}


@app.post("/api/login")
async def api_login(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    username = data.get("username", "").strip()
    password = data.get("password", "")

    user = db.query(User).filter(
        User.username == username,
        User.password == hash_password(password)
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_token(user.id, user.role)
    return {"token": token, "role": user.role, "username": user.username}


@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse(request=request, name="chat.html")


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()

    token = websocket.query_params.get("token", "")
    if not token:
        await websocket.send_text(json.dumps({"type": "error", "content": "未登录"}))
        await websocket.close()
        return
    
    import jwt as pyjwt
    from backend.config import SECRET_KEY
    try:
        payload = pyjwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
    except pyjwt.PyJWTError as e:
        await websocket.send_text(json.dumps({"type": "error", "content": "Token 无效，请重新登录"}))
        await websocket.close()
        return
    current_user_id = user_id
    await websocket.send_text(json.dumps({"type": "reply", "content": "AI 办公助手已就绪，试试输入：帮我写一份周报"}))

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data).get("message", "")

            if not msg.strip():
                continue

            try:
                ai_reply, tool_results = await run_agent(msg)

                # 写操作日志
                db_log = SessionLocal()
                for r in tool_results:
                    log = OperationLog(
                        user_id=user_id,
                        action=r.split("]")[0].replace("[", "") if "]" in r else "对话",
                        detail=r[:200]
                    )
                    db_log.add(log)
                db_log.commit()
                db_log.close()

                await websocket.send_text(json.dumps({
                    "type": "reply",
                    "content": ai_reply,
                    "tools": tool_results
                }))
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "content": f"AI 处理失败: {str(e)}"
                }))
    except WebSocketDisconnect:
        pass

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse(request=request, name="admin.html")

@app.get("/api/admin")
async def api_admin(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    logs = db.query(OperationLog).order_by(OperationLog.created_at.desc()).limit(50).all()

    from sqlalchemy import func
    stats = db.query(
        OperationLog.action, func.count(OperationLog.id).label("count")
    ).group_by(OperationLog.action).all()

    return {
        "stats": [(s[0], s[1]) for s in stats],
        "logs": [{
            "time": log.created_at.strftime('%m-%d %H:%M'),
            "user": log.user.username,
            "action": log.action,
            "detail": log.detail[:50] if log.detail else ""
        } for log in logs]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=5000, reload=True)
