"""
Simple Python GUI App - To-Do List
Runs a web server on port 8080 with an interactive to-do list interface.
"""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler

# In-memory to-do storage
todos = []
next_id = 1

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Python To-Do App</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            padding: 40px 20px;
        }
        .container {
            background: white;
            border-radius: 16px;
            padding: 32px;
            width: 100%;
            max-width: 500px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 8px;
            font-size: 28px;
        }
        .subtitle {
            text-align: center;
            color: #888;
            margin-bottom: 24px;
            font-size: 14px;
        }
        .input-row {
            display: flex;
            gap: 8px;
            margin-bottom: 24px;
        }
        input[type="text"] {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.2s;
            outline: none;
        }
        input[type="text"]:focus { border-color: #667eea; }
        button.add-btn {
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            transition: transform 0.1s;
        }
        button.add-btn:hover { transform: scale(1.05); }
        .todo-list { list-style: none; }
        .todo-item {
            display: flex;
            align-items: center;
            padding: 12px;
            border-bottom: 1px solid #f0f0f0;
            animation: slideIn 0.3s ease;
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }
        .todo-item.done .todo-text {
            text-decoration: line-through;
            color: #aaa;
        }
        .todo-text { flex: 1; font-size: 16px; color: #333; margin: 0 12px; }
        .check-btn, .delete-btn {
            background: none;
            border: none;
            font-size: 20px;
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 4px;
            transition: background 0.2s;
        }
        .check-btn:hover { background: #e8f5e9; }
        .delete-btn:hover { background: #ffebee; }
        .empty {
            text-align: center;
            color: #bbb;
            padding: 40px;
            font-size: 16px;
        }
        .counter {
            text-align: center;
            color: #999;
            margin-top: 16px;
            font-size: 13px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>To-Do List</h1>
        <p class="subtitle">Built with Python &middot; No frameworks needed</p>
        <div class="input-row">
            <input type="text" id="taskInput" placeholder="What needs to be done?" onkeydown="if(event.key==='Enter')addTodo()">
            <button class="add-btn" onclick="addTodo()">Add</button>
        </div>
        <ul class="todo-list" id="todoList"></ul>
        <div class="counter" id="counter"></div>
    </div>

    <script>
        async function loadTodos() {
            const res = await fetch('/api/todos');
            const todos = await res.json();
            const list = document.getElementById('todoList');
            const counter = document.getElementById('counter');
            if (todos.length === 0) {
                list.innerHTML = '<li class="empty">No tasks yet. Add one above!</li>';
                counter.textContent = '';
                return;
            }
            const done = todos.filter(t => t.done).length;
            list.innerHTML = todos.map(t => `
                <li class="todo-item ${t.done ? 'done' : ''}">
                    <button class="check-btn" onclick="toggleTodo(${t.id})">${t.done ? '&#9745;' : '&#9744;'}</button>
                    <span class="todo-text">${escapeHtml(t.text)}</span>
                    <button class="delete-btn" onclick="deleteTodo(${t.id})">&#128465;</button>
                </li>
            `).join('');
            counter.textContent = `${done} of ${todos.length} completed`;
        }

        function escapeHtml(s) {
            return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
        }

        async function addTodo() {
            const input = document.getElementById('taskInput');
            const text = input.value.trim();
            if (!text) return;
            await fetch('/api/todos', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({text})
            });
            input.value = '';
            loadTodos();
        }

        async function toggleTodo(id) {
            await fetch('/api/todos/' + id + '/toggle', {method: 'POST'});
            loadTodos();
        }

        async function deleteTodo(id) {
            await fetch('/api/todos/' + id, {method: 'DELETE'});
            loadTodos();
        }

        loadTodos();
    </script>
</body>
</html>
"""


class TodoHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode())
        elif self.path == '/api/todos':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(todos).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        global next_id
        if self.path == '/api/todos':
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length))
            todo = {'id': next_id, 'text': body['text'], 'done': False}
            todos.append(todo)
            next_id += 1
            self.send_response(201)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(todo).encode())
        elif self.path.startswith('/api/todos/') and self.path.endswith('/toggle'):
            tid = int(self.path.split('/')[3])
            for t in todos:
                if t['id'] == tid:
                    t['done'] = not t['done']
            self.send_response(200)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_DELETE(self):
        global todos
        if self.path.startswith('/api/todos/'):
            tid = int(self.path.split('/')[3])
            todos = [t for t in todos if t['id'] != tid]
            self.send_response(200)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        print(f"  {args[0]}")


if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8080), TodoHandler)
    print("To-Do App running at http://localhost:8080")
    print("Press Ctrl+C to stop")
    server.serve_forever()
