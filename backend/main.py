import traceback, json
from fastapi import FastAPI, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from backend.database import engine, get_db, Base, SessionLocal
from backend.models import User, OperationLog, Conversation, Message, Contact
from backend.auth import hash_password, create_token, get_current_user, require_admin
from backend.agent import run_agent
from backend import init_db

init_db()
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

LOGIN_HTML = """<!DOCTYPE html><html lang="zh"><head><meta charset="UTF-8"><title>AI Office</title><link rel="stylesheet" href="/static/style.css"></head><body>
<div class="auth-container" id="loginBox">
<h2>Login</h2>
<input type="text" id="loginUser" placeholder="Username"><br><br>
<input type="password" id="loginPass" placeholder="Password"><br><br>
<button class="btn-primary" onclick="doLogin()">Login</button>
<p style="text-align:center;margin-top:12px;"><a href="#" onclick="showReg()">Register</a></p>
<p id="loginErr" style="color:red;"></p>
</div>
<div class="auth-container" id="regBox" style="display:none;">
<h2>Register</h2>
<input type="text" id="regUser" placeholder="Username"><br><br>
<input type="password" id="regPass" placeholder="Password"><br><br>
<input type="password" id="regPass2" placeholder="Confirm"><br><br>
<button class="btn-primary" onclick="doReg()">Register</button>
<p style="text-align:center;margin-top:12px;"><a href="#" onclick="showLogin()">Back</a></p>
<p id="regErr" style="color:red;"></p>
</div>
<script>
async function doLogin(){const r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:document.getElementById('loginUser').value,password:document.getElementById('loginPass').value})});const d=await r.json();if(r.ok){localStorage.setItem('token',d.token);localStorage.setItem('role',d.role);window.location.href='/chat';}else document.getElementById('loginErr').textContent=d.detail;}
async function doReg(){const pw=document.getElementById('regPass').value;if(pw!==document.getElementById('regPass2').value){document.getElementById('regErr').textContent='Mismatch';return;}const r=await fetch('/api/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:document.getElementById('regUser').value,password:pw})});const d=await r.json();if(r.ok){alert('Done');showLogin();}else document.getElementById('regErr').textContent=d.detail;}
function showReg(){document.getElementById('loginBox').style.display='none';document.getElementById('regBox').style.display='block';}
function showLogin(){document.getElementById('regBox').style.display='none';document.getElementById('loginBox').style.display='block';}
</script></body></html>"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse(content=LOGIN_HTML)

@app.get("/register", response_class=HTMLResponse)
async def register_page():
    return HTMLResponse(content=LOGIN_HTML)

@app.post("/api/register")
async def api_register(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    username = data.get("username", "").strip()
    password = data.get("password", "")
    if not username or not password:
        raise HTTPException(400, "Required")
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(400, "Exists")
    is_first = db.query(User).count() == 0
    user = User(username=username, password=hash_password(password), role="admin" if is_first else "employee")
    db.add(user); db.commit()
    return {"message": "OK"}

@app.post("/api/login")
async def api_login(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    user = db.query(User).filter(User.username == data.get("username","").strip(), User.password == hash_password(data.get("password",""))).first()
    if not user: raise HTTPException(401, "Invalid")
    token = create_token(user.id, user.role)
    return {"token": token, "role": user.role, "username": user.username}

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse(request=request, name="chat.html")

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse(request=request, name="admin.html")

@app.get("/api/admin")
async def api_admin(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    from sqlalchemy import func
    logs = db.query(OperationLog).order_by(OperationLog.created_at.desc()).limit(50).all()
    stats = db.query(OperationLog.action, func.count(OperationLog.id).label("count")).group_by(OperationLog.action).all()
    return {"stats": [(s[0], s[1]) for s in stats], "logs": [{"time": log.created_at.strftime('%m-%d %H:%M'), "user": log.user.username, "action": log.action, "detail": log.detail[:50] if log.detail else ""} for log in logs]}

@app.get("/api/conversations")
async def list_conversations(db: Session = Depends(get_db)):
    convs = db.query(Conversation).order_by(Conversation.created_at.desc()).all()
    return [{"id": c.id, "title": c.title} for c in convs]

@app.get("/api/conversations/{conv_id}")
async def get_conversation(conv_id: int, db: Session = Depends(get_db)):
    msgs = db.query(Message).filter(Message.conversation_id == conv_id).all()
    return [{"role": m.role, "content": m.content} for m in msgs]

@app.post("/api/conversations")
async def create_conversation(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    conv = Conversation(user_id=1, title=data.get("title","New")[:30])
    db.add(conv); db.commit()
    return {"id": conv.id}

@app.get("/api/contacts")
async def list_contacts(db: Session = Depends(get_db)):
    contacts = db.query(Contact).all()
    return [{"id": c.id, "name": c.name, "email": c.email, "department": c.department} for c in contacts]

@app.post("/api/contacts")
async def add_contact(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    c = Contact(name=data.get("name",""), email=data.get("email",""), department=data.get("department",""))
    db.add(c); db.commit()
    return {"id": c.id}

@app.post("/api/admin/promote")
async def promote_user(request: Request, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    data = await request.json()
    uid = data.get("user_id")
    user = db.query(User).filter(User.id == uid).first()
    if not user: raise HTTPException(400, "User not found")
    user.role = "admin"
    db.commit()
    return {"message": "User " + user.username + " is now admin"}

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    token = websocket.query_params.get("token","")
    if not token:
        await websocket.send_text(json.dumps({"type":"error","content":"Not logged in"}))
        await websocket.close(); return
    import jwt as pyjwt
    from backend.config import SECRET_KEY
    try:
        payload = pyjwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
    except pyjwt.PyJWTError:
        await websocket.send_text(json.dumps({"type":"error","content":"Invalid token"}))
        await websocket.close(); return

    await websocket.send_text(json.dumps({"type":"reply","content":"AI Office Agent ready"}))

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data).get("message","")
            if not msg.strip(): continue
            try:
                # 加载对话历史
                history = []
                conv_id = json.loads(data).get("conv_id", None)
                if conv_id:
                    db3 = SessionLocal()
                    prev = db3.query(Message).filter(Message.conversation_id == conv_id).order_by(Message.created_at.desc()).limit(10).all()
                    db3.close()
                    history = [{"role": m.role, "content": m.content} for m in reversed(prev)]

                ai_reply, tool_results = await run_agent(msg, history=history)
                db_log = SessionLocal()
                conv_id = json.loads(data).get("conv_id", None)
                if conv_id:
                    db_log.add(Message(conversation_id=conv_id, role="user", content=msg))
                    db_log.add(Message(conversation_id=conv_id, role="assistant", content=ai_reply))
                for r in tool_results:
                    log = OperationLog(user_id=user_id, action=r.split("]")[0].replace("[","") if "]" in r else "chat", detail=r[:200])
                    db_log.add(log)
                db_log.commit(); db_log.close()
                await websocket.send_text(json.dumps({"type":"reply","content":ai_reply,"tools":tool_results}))
            except Exception as e:
                await websocket.send_text(json.dumps({"type":"error","content":f"Error: {str(e)}"}))
    except WebSocketDisconnect:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=5000, reload=True)