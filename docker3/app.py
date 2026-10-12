import os
import socket
from datetime import datetime

import pymysql
from flask import Flask, jsonify, redirect, render_template_string, request, url_for

app = Flask(__name__)



def get_db():
    # 모든 web Task가 같은 MySQL Service(db)에 접속한다.
    return pymysql.connect(
        host=os.getenv("DB_HOST", "db"),
        user=os.getenv("DB_USER", "ngds"),
        password=os.getenv("DB_PASSWORD", "ngds-pass"),
        database=os.getenv("DB_NAME", "guestbook"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def ensure_table(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_id VARCHAR(12) NOT NULL,
            name VARCHAR(20) NOT NULL,
            text VARCHAR(100) NOT NULL,
            via VARCHAR(64),
            node VARCHAR(32),
            container VARCHAR(32),
            time VARCHAR(19)
        )
        """
    )


def get_info():
    return {
        "node": os.getenv("NODE_NAME", "unknown"),
        "container": socket.gethostname(),
        "time": datetime.now().strftime("%H:%M:%S"),
    }


def load_messages():
    with get_db() as conn, conn.cursor() as cur:
        ensure_table(cur)
        cur.execute("SELECT * FROM messages ORDER BY id DESC LIMIT 50")
        return cur.fetchall()


PAGE = """
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>Docker Swarm 방명록</title>
  <style>
    body {
      margin: 0; padding: 40px 16px; font-family: Arial, sans-serif;
      color: #172033; background: linear-gradient(135deg, #fff7e6, #f7f9fc);
    }
    .card {
      width: min(100%, 640px); margin: 0 auto; padding: 34px;
      background: white; border-radius: 18px;
      box-shadow: 0 16px 45px rgba(24, 63, 98, .12);
    }
    .badge { color: #d97706; font-weight: 700; font-size: 14px; }
    .now { display: flex; gap: 24px; margin: 16px 0 8px; }
    .label { color: #667085; font-size: 13px; }
    .node { font-size: 28px; font-weight: 700; }
    .container { font-size: 18px; font-family: monospace; }
    form { display: flex; gap: 8px; margin: 24px 0; flex-wrap: wrap; }
    input { padding: 8px; border: 1px solid #ccc; border-radius: 6px; }
    input[name=text] { flex: 1; min-width: 160px; }
    button { padding: 8px 16px; border: 0; border-radius: 6px;
             background: #d97706; color: #fff; cursor: pointer; }
    ul { list-style: none; padding: 0; }
    li { padding: 10px 0; border-bottom: 1px solid #eee; }
    li small { display: block; color: #98a2b3; margin-top: 4px; font-family: monospace; }
  </style>
</head>
<body>
  <main class="card">
    <div class="badge">Docker Swarm · ngds_web</div>
    <h1>🐝 Swarm 방명록</h1>
    <div class="now">
      <div><div class="label">접속한 주소</div><div class="node">{{ host }}</div></div>
      <div><div class="label">지금 응답한 Node</div><div class="node">{{ node }}</div></div>
      <div><div class="label">Container ID</div><div class="container">{{ container }}</div></div>
    </div>
    <form method="post" action="/messages">
      <input type="text" name="student_id" placeholder="학번" required maxlength="12">
      <input type="text" name="name" placeholder="이름" required maxlength="20">
      <input type="text" name="text" placeholder="메시지" required maxlength="100">
      <button type="submit">남기기</button>
    </form>
    <ul>
    {% for m in messages %}
      <li><b>{{ m.student_id }} {{ m.name }}</b>: {{ m.text }}
        <small>접속 {{ m.via }} → 처리 Node {{ m.node }} · Container {{ m.container }} · {{ m.time }}</small></li>
    {% else %}
      <li>아직 메시지가 없다. 학번과 이름으로 첫 메시지를 남기자.</li>
    {% endfor %}
    </ul>
  </main>
</body>
</html>
"""


@app.get("/")
def index():
    return render_template_string(
        PAGE, messages=load_messages(), host=request.host, **get_info()
    )


@app.post("/messages")
def add_message():
    info = get_info()
    entry = {
        "student_id": request.form["student_id"].strip(),
        "name": request.form["name"].strip(),
        "text": request.form["text"].strip(),
        # 브라우저가 접속한 주소 (예: localhost:8002 → worker1로 접속)
        "via": request.host,
        "node": info["node"],
        "container": info["container"],
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    with get_db() as conn, conn.cursor() as cur:
        ensure_table(cur)
        cur.execute(
            "INSERT INTO messages (student_id, name, text, via, node, container, time) "
            "VALUES (%(student_id)s, %(name)s, %(text)s, %(via)s, %(node)s, %(container)s, %(time)s)",
            entry,
        )
    return redirect(url_for("index"))


@app.get("/api/info")
def api_info():
    return jsonify(get_info())


@app.get("/api/messages")
def api_messages():
    return jsonify(load_messages())


@app.get("/health")
def health():
    return jsonify(status="ok"), 200