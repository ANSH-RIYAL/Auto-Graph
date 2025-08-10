from flask import Flask, jsonify, request

from services.todo_service import TodoService

app = Flask(__name__)
service = TodoService()


@app.route("/health")
def health() -> str:
    return "ok"


@app.route("/api/todos", methods=["GET"])  # Implementation-level example
def list_todos():
    return jsonify([t.to_dict() for t in service.list_todos()])


@app.route("/api/todos", methods=["POST"])  # calls -> service.create_todo
def create_todo():
    data = request.get_json(force=True)
    todo = service.create_todo(title=data.get("title", ""))
    return jsonify(todo.to_dict()), 201


@app.route("/api/todos/<int:todo_id>", methods=["PATCH"])  # depends_on utils/db for storage
def complete_todo(todo_id: int):
    todo = service.complete_todo(todo_id)
    return jsonify(todo.to_dict())


if __name__ == "__main__":
    app.run(debug=True)

