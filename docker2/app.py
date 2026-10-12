import os
import socket

import mysql.connector
from flask import Flask, redirect, render_template_string, request, url_for

app = Flask(__name__)


def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "db"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME", "appdb"),
        user=os.getenv("DB_USER", "appuser"),
        password=os.getenv("DB_PASSWORD", "apppassword"),
        connection_timeout=3,
        charset="utf8mb4",
    )


def initialize_database():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(50) NOT NULL,
            message VARCHAR(500) NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) CHARACTER SET utf8mb4
        """
    )
    connection.commit()
    cursor.close()
    connection.close()


def load_messages():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT id, name, message, created_at
        FROM messages
        ORDER BY id DESC
        """
    )
    messages = cursor.fetchall()
    cursor.close()
    connection.close()

    for item in messages:
        item["created_at"] = item["created_at"].strftime("%Y-%m-%d %H:%M:%S")
    return messages


def save_message(name, message):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO messages (name, message) VALUES (%s, %s)",
        (name, message),
    )
    connection.commit()
    cursor.close()
    connection.close()


PAGE = """
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Docker Compose 방명록</title>
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0; min-height: 100vh; padding: 40px 16px;
      font-family: Arial, sans-serif; color: #172033;
      background: linear-gradient(135deg, #eef7ff, #f7f9fc);
    }
    .card {
      width: min(100%, 680px); margin: 0 auto; padding: 34px;
      background: white; border-radius: 18px;
      box-shadow: 0 16px 45px rgba(24, 63, 98, .12);
    }
    .badge { color: #1677b8; font-weight: 700; font-size: 14px; }
    h1 { margin: 10px 0 6px; }
    .description { margin: 0; color: #667085; }
    .meta { margin: 16px 0 24px; color: #667085; font-size: 14px; }
    code { padding: 3px 7px; background: #eef2f7; border-radius: 6px; }
    form { display: grid; gap: 10px; }
    input, textarea {
      width: 100%; padding: 12px; border: 1px solid #d0d5dd;
      border-radius: 9px; font: inherit;
    }
    textarea { min-height: 96px; resize: vertical; }
    button {
      padding: 13px 20px; border: 0; border-radius: 9px;
      background: #2496ed; color: white; font-size: 16px;
      font-weight: 700; cursor: pointer;
    }
    button:hover { background: #1479bd; }
    .section-title { margin: 30px 0 12px; font-size: 18px; }
    .message {
      padding: 16px 0; border-bottom: 1px solid #eaecf0;
    }
    .message:last-child { border-bottom: 0; }
    .message-head { display: flex; justify-content: space-between; gap: 12px; }
    .time { color: #98a2b3; font-size: 13px; }
    .message p { margin: 8px 0 0; white-space: pre-wrap; }
    .empty { padding: 22px 0; color: #98a2b3; text-align: center; }
  </style>
</head>
<body>
  <main class="card">
    <div class="badge">Docker Compose · Flask + MySQL</div>
    <h1>🐳 Docker Compose 방명록</h1>
    <p class="description">메시지는 MySQL과 Named Volume에 저장됩니다.</p>
    <p class="meta">
      Web Container: <code>{{ hostname }}</code> · 메시지 {{ messages|length }}개
    </p>

    <form method="post" action="{{ url_for('add_message') }}">
      <input type="text" name="name" placeholder="이름" maxlength="50" required>
      <textarea name="message" placeholder="메시지를 입력하세요" maxlength="500" required></textarea>
      <button type="submit">메시지 남기기</button>
    </form>

    <h2 class="section-title">방명록</h2>
    {% for item in messages %}
      <article class="message">
        <div class="message-head">
          <strong>{{ item.name }}</strong>
          <span class="time">{{ item.created_at }}</span>
        </div>
        <p>{{ item.message }}</p>
      </article>
    {% else %}
      <div class="empty">아직 메시지가 없습니다. 첫 메시지를 남겨 보세요.</div>
    {% endfor %}

  </main>
</body>
</html>
"""


@app.get("/")
def index():
    return render_template_string(
        PAGE,
        messages=load_messages(),
        hostname=socket.gethostname(),
    )


@app.post("/messages")
def add_message():
    name = request.form["name"].strip()
    message = request.form["message"].strip()
    if name and message:
        save_message(name, message)
        print(f"[guestbook] message saved: name={name}", flush=True)
    return redirect(url_for("index"))


initialize_database()