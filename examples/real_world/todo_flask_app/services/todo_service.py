from typing import List

from utils.db import InMemoryDB
from models.todo import Todo


class TodoService:
    """System-level example service coordinating operations."""

    def __init__(self) -> None:
        self.db = InMemoryDB()

    def list_todos(self) -> List[Todo]:
        return self.db.list()

    def create_todo(self, title: str) -> Todo:
        item = Todo(title=title)
        self.db.add(item)
        return item

    def complete_todo(self, todo_id: int) -> Todo:
        item = self.db.get(todo_id)
        item.completed = True
        self.db.update(item)
        return item

