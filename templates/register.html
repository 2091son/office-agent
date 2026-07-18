{% extends "base.html" %}
{% block content %}
<div class="auth-container">
    <h2>注册 AI 办公助手</h2>
    <form id="registerForm">
        <input type="text" id="username" placeholder="用户名" required>
        <input type="password" id="password" placeholder="密码" required>
        <input type="password" id="password2" placeholder="确认密码" required>
        <button type="submit" class="btn-primary">注册</button>
    </form>
    <p style="text-align:center;margin-top:16px;">已有账号？<a href="/">登录</a></p>
    <p id="error" style="color:red;text-align:center;"></p>
</div>
<script>
document.getElementById('registerForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const password2 = document.getElementById('password2').value;
    if (password !== password2) {
        document.getElementById('error').textContent = '两次密码不一致';
        return;
    }
    const resp = await fetch('/api/register', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username, password})
    });
    if (resp.ok) {
        window.location.href = '/';
    } else {
        const err = await resp.json();
        document.getElementById('error').textContent = err.detail;
    }
});
</script>
{% endblock %}