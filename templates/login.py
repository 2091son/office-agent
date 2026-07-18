{% extends "base.html" %}
{% block content %}
<div class="auth-container">
    <h2>登录 AI 办公助手</h2>
    <form id="loginForm">
        <input type="text" id="username" placeholder="用户名" required>
        <input type="password" id="password" placeholder="密码" required>
        <button type="submit" class="btn-primary">登录</button>
    </form>
    <p style="text-align:center;margin-top:16px;">没有账号？<a href="/register">注册</a></p>
    <p id="error" style="color:red;text-align:center;"></p>
</div>
<script>
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const resp = await fetch('/api/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username, password})
    });
    if (resp.ok) {
        const data = await resp.json();
        localStorage.setItem('token', data.token);
        localStorage.setItem('username', data.username);
        window.location.href = '/chat';
    } else {
        const err = await resp.json();
        document.getElementById('error').textContent = err.detail;
    }
});
</script>
{% endblock %}