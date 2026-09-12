import json
import os
import socket
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template_string, request, url_for

app = Flask(__name__)

DATA_FILE = Path(os.getenv("DATA_FILE", "/app/data/messages.json"))
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_messages():
    if not DATA_FILE.exists():
        return []
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def save_messages(messages):
    DATA_FILE.write_text(
        json.dumps(messages, ensure_ascii=False, indent=2), encoding="utf-8"
    )


PAGE = """
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>Docker 1 방명록</title>
  <style>
    body { font-family: sans-serif; background: #f5f7fa; margin: 0; }
    .card { max-width: 560px; margin: 40px auto; padding: 28px;
            background: #fff; border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,.08); }
    h1 { margin-top: 0; }
    .meta { color: #666; font-size: 14px; }
    code { background: #eef2f7; padding: 2px 6px; border-radius: 4px; }
    form { display: flex; gap: 8px; margin: 20px 0; }
    input[type=text] { flex: 1; padding: 8px; border: 1px solid #ccc; border-radius: 6px; }
    button { padding: 8px 16px; border: 0; border-radius: 6px;
             background: #2496ed; color: #fff; cursor: pointer; }
    ul { list-style: none; padding: 0; }
    li { padding: 10px 0; border-bottom: 1px solid #eee; }
    li small { color: #999; margin-left: 6px; }
  </style>
</head>
<body>
  <div class="card">
    <h1>🐳 Docker 1 방명록</h1>
    <p class="meta">
      Container: <code>{{ hostname }}</code> ·
      Stage: <code>{{ stage }}</code> ·
      메시지 {{ messages|length }}개
    </p>
    <form method="post" action="/messages">
      <input type="text" name="name" placeholder="이름" required maxlength="20">
      <input type="text" name="text" placeholder="메시지" required maxlength="100">
      <button type="submit">남기기</button>
    </form>
    <ul>
    {% for m in messages|reverse %}
      <li><b>{{ m.name }}</b>: {{ m.text }} <small>{{ m.time }}</small></li>
    {% else %}
      <li>아직 메시지가 없다. 첫 메시지를 남기자.</li>
    {% endfor %}
    </ul>
  </div>
</body>
</html>
"""


@app.get("/")
def index():
    return render_template_string(
        PAGE,
        messages=load_messages(),
        hostname=socket.gethostname(),
        stage=os.getenv("PRACTICE_STAGE", "docker"),
    )


@app.post("/messages")
def add_message():
    messages = load_messages()
    messages.append({
        "name": request.form["name"].strip(),
        "text": request.form["text"].strip(),
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    save_messages(messages)
    return redirect(url_for("index"))


@app.get("/api/messages")
def api_messages():
    return jsonify(load_messages())


@app.get("/health")
def health():
    return jsonify(status="ok", messages=len(load_messages())), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)